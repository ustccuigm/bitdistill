"""NeMo QAD batch scheduling adapted to SteerDistill's per-turn repair records.

The sampling unit is a trajectory, not an assistant-turn JSONL row. All turn
and repair targets for a task travel together. SteerDistill defaults to 16 prompts,
one generation and global batch 16: one optimizer update per rollout batch.
"""
import argparse
import json
import logging

import torch
from torch.utils.data import Dataset

logger = logging.getLogger(__name__)


def trajectory_groups(examples):
    groups, ordinary_sources, seen = {}, {}, set()
    for index, row in enumerate(examples):
        key = row.get("task_key")
        if not key:
            raise ValueError("Online records must identify their task_key")
        if "assistant_turn" in row:
            identity = (key, row["assistant_turn"])
            if identity in seen:
                raise ValueError("A retained assistant turn occurs more than once")
            seen.add(identity)
        if row.get("distill_mode", "ordinary_opd") == "ordinary_opd":
            source = row.get("source_run")
            if not source:
                raise ValueError("Online ordinary records must identify source_run")
            previous = ordinary_sources.setdefault(key, source)
            if previous != source:
                raise ValueError("This recipe requires one discovery generation per prompt")
        groups.setdefault(key, []).append(index)
    if not groups:
        raise ValueError("No training trajectories")
    return list(groups.values())


class OnlineGlobalBatches(Dataset):
    """Contiguous DP shards, one dataset item per rank per optimizer update."""
    def __init__(self, examples, global_batch_size, micro_batch_size, world_size):
        if min(global_batch_size, micro_batch_size, world_size) < 1:
            raise ValueError("Batch sizes and world size must be positive")
        if global_batch_size % (micro_batch_size * world_size):
            raise ValueError("Global trajectory batch must divide by micro batch * DP size")
        self.examples = examples
        self.groups = trajectory_groups(examples)
        self.global_size = global_batch_size
        self.micro_size = micro_batch_size
        self.world = world_size
        self.local_size = global_batch_size // world_size
        if len(self.groups) > global_batch_size:
            raise ValueError("An online update exceeds the global trajectory batch size")
        self.updates = 1

    def __len__(self):
        return self.updates * self.world

    def __getitem__(self, index):
        if index < 0:
            index += len(self)
        if not 0 <= index < len(self):
            raise IndexError(index)
        update, rank = divmod(index, self.world)
        begin = update * self.global_size
        all_groups = self.groups[begin:begin + self.global_size]
        # Keep the same number of collective slots on every rank, including
        # empty shards in the final smaller batch; dummy rows carry zero loss.
        local = all_groups[rank::self.world]
        microgroups = []
        for offset in range(0, self.local_size, self.micro_size):
            ids = [i for group in local[offset:offset + self.micro_size] for i in group]
            microgroups.append([(i, self.examples[i]) for i in ids])
        return {"microgroups": microgroups,
                "expected_ids": [i for group in all_groups for i in group],
                "global_batch_index": update, "trajectories": len(all_groups),
                "dummy": self.examples[0]}


class OnlineCollator:
    def __init__(self, base, turn_batch_size=4):
        self.base = base
        if turn_batch_size < 1:
            raise ValueError("Turn batch size must be positive")
        self.turn_batch_size = turn_batch_size

    def __call__(self, items):
        if len(items) != 1:
            raise ValueError("Transport batch must be one pre-sharded global batch")
        item = items[0]
        micros, ids = [], []
        # Each SteerDistill turn retains its original prefix and repair reference.
        # Forward these separately for memory, but only update after the full
        # global batch has accumulated, as NeMo does across its microbatches.
        for group in item["microgroups"]:
            batches = []
            for offset in range(0, len(group), self.turn_batch_size):
                records = group[offset:offset + self.turn_batch_size]
                batch = self.base([row for _, row in records])
                batch["online_row_mask"] = torch.ones(len(records), dtype=torch.bool)
                ids.extend(index for index, _ in records)
                batches.append(batch)
            micros.append(batches)
        dummy = self.base([item["dummy"]])
        dummy["online_row_mask"] = torch.zeros(1, dtype=torch.bool)
        return {"online_microgroups": micros, "online_dummy": dummy,
                "online_ids": ids, "online_expected_ids": item["expected_ids"],
                "online_global_batch_index": item["global_batch_index"],
                "online_trajectories": item["trajectories"]}


def prepare_online_data(data_module, args):
    if args.per_device_train_batch_size != 1 or args.gradient_accumulation_steps != 1:
        raise ValueError("Transport batch and HF accumulation must be 1; worker accumulates microbatches")
    dataset = OnlineGlobalBatches(data_module["train_dataset"], args.opd_global_batch_size,
                                 args.opd_micro_batch_size, args.world_size)
    return {"train_dataset": dataset, "eval_dataset": None,
            "data_collator": OnlineCollator(data_module["data_collator"], args.online_turn_batch_size)}


def distributed():
    return torch.distributed.is_available() and torch.distributed.is_initialized()


def collect_update_batch(iterator, num_batches, device, optimizer_step):
    if num_batches != 1:
        raise ValueError("Each Trainer step must contain exactly one global batch shard")
    try:
        batch = next(iterator)
    except StopIteration:
        return [], None
    ids = batch["online_ids"]
    if distributed():
        parts = [None] * torch.distributed.get_world_size()
        torch.distributed.all_gather_object(parts, (batch["online_global_batch_index"], ids))
        if len({index for index, _ in parts}) != 1:
            raise ValueError("DP ranks disagree about global batch order")
        ids = [i for _, part in parts for i in part]
    if sorted(ids) != sorted(batch["online_expected_ids"]):
        raise ValueError("Global batch skipped or repeated real rollout records")
    tokens = sum(int(micro["labels"][:, 1:].ne(-100).sum())
                 for group in batch["online_microgroups"] for micro in group)
    count = torch.tensor(tokens, dtype=torch.long, device=device)
    if distributed():
        torch.distributed.all_reduce(count)
    if count.item() <= 0:
        raise ValueError("Global batch has no active distillation tokens")
    logger.info("STEER_ONLINE_BATCH_SIGNAL optimizer_step=%d global_batch_index=%d "
                "trajectories=%d turn_records=%d global_tokens=%d coverage=exactly_once",
                optimizer_step, batch["online_global_batch_index"],
                batch["online_trajectories"], len(ids), count.item())
    return [batch], count


def iter_collective_microbatches(batch, device):
    for group in batch["online_microgroups"]:
        length = torch.tensor(len(group), dtype=torch.long, device=device)
        if distributed():
            torch.distributed.all_reduce(length, op=torch.distributed.ReduceOp.MAX)
        for index in range(length.item()):
            yield group[index] if index < len(group) else batch["online_dummy"]


def global_token_loss(token_sum, global_tokens):
    if global_tokens is None or global_tokens <= 0:
        raise ValueError("Missing global-batch token denominator")
    world = torch.distributed.get_world_size() if distributed() else 1
    # FSDP averages rank gradients. Compensate once; do not divide by the
    # microbatch count again because global_tokens already covers that batch.
    return token_sum * world / global_tokens


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--global-batch-size", type=int, required=True)
    parser.add_argument("--micro-batch-size", type=int, required=True)
    parser.add_argument("--world-size", type=int, required=True)
    parser.add_argument("--expected-trajectories", type=int)
    parser.add_argument("--prompts", type=str)
    parser.add_argument("--benchmark", type=str)
    args = parser.parse_args()
    with open(args.data) as handle:
        examples = [json.loads(line) for line in handle if line.strip()]
    dataset = OnlineGlobalBatches(examples, args.global_batch_size,
                                 args.micro_batch_size, args.world_size)
    if args.expected_trajectories is not None and len(dataset.groups) != args.expected_trajectories:
        raise ValueError(f"Expected {args.expected_trajectories} fresh trajectories, got {len(dataset.groups)}")
    if args.prompts:
        with open(args.prompts) as handle:
            prompts = [json.loads(line) for line in handle if line.strip()]
        expected_keys = []
        for row in prompts:
            meta = row.get("metadata") or {}
            task = row.get("task") or {}
            if meta.get("scenario") is not None and "task_id" in meta:
                expected_keys.append(f"{meta['scenario']}:{meta['task_id']}")
            elif isinstance(task, dict) and "task_id" in task and args.benchmark:
                expected_keys.append(f"{args.benchmark}:{task['task_id']}")
            else:
                raise ValueError("Prompt lacks an environment task identity")
        if len(set(expected_keys)) != len(expected_keys):
            raise ValueError("Prompt batch contains repeated task identities")
        if set(expected_keys) != {row["task_key"] for row in examples}:
            raise ValueError("Training trajectories do not match the sampled task batch")
    print(dataset.updates)
