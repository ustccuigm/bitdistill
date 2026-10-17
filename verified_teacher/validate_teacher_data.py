#!/usr/bin/env python3
"""Validate every cleaned teacher record through SteerDistill's collator."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from transformers import AutoTokenizer


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--model-max-length", type=int, default=32768)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    sys.path.insert(0, str(args.repo_root / "train"))
    from data_loading import DataCollatorForSupervisedDataset  # noqa: PLC0415

    tokenizer = AutoTokenizer.from_pretrained(
        args.model, model_max_length=args.model_max_length, fix_mistral_regex=True
    )
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    collator = DataCollatorForSupervisedDataset(tokenizer)
    batch, count, min_tokens, max_tokens = [], 0, None, 0
    seen = set()
    verified_runs = set()
    for line_no, line in enumerate(args.data.open(encoding="utf-8"), 1):
        row = json.loads(line)
        prompt, completion = row.get("prompt"), row.get("completion")
        prompt_ids, completion_ids = row.get("prompt_token_ids"), row.get("completion_token_ids")
        if not prompt or not completion or not isinstance(prompt_ids, list) or not isinstance(completion_ids, list):
            raise ValueError(f"line {line_no}: empty text or token ids")
        length = len(prompt_ids) + len(completion_ids) + 1
        if length > args.model_max_length or len(completion_ids) in {2048, 4096}:
            raise ValueError(f"line {line_no}: invalid lengths total={length} completion={len(completion_ids)}")
        prompt_array = np.asarray(prompt_ids, dtype=np.int32)
        completion_array = np.asarray(completion_ids, dtype=np.int32)
        if (
            prompt_array.size == 0
            or completion_array.size == 0
            or prompt_array.min() < 0
            or completion_array.min() < 0
            or prompt_array.max() >= len(tokenizer)
            or completion_array.max() >= len(tokenizer)
        ):
            raise ValueError(f"line {line_no}: token id outside tokenizer vocabulary")
        digest = hashlib.sha256()
        digest.update(prompt_array.tobytes())
        digest.update(b"\xff\xff\xff\xff")
        digest.update(completion_array.tobytes())
        key = digest.digest()
        if key in seen:
            raise ValueError(f"line {line_no}: duplicate token sequence")
        seen.add(key)
        metadata = row.get("metadata", {})
        if metadata.get("reward") != 1.0:
            raise ValueError(f"line {line_no}: non-success reward")
        run_dir = Path(metadata.get("run_dir", ""))
        if not run_dir.is_absolute():
            run_dir = args.repo_root / run_dir
        run_key = str(run_dir)
        if run_key not in verified_runs:
            verify_path = run_dir / "verify.code.json"
            trajectory_path = run_dir / "trajectory.json"
            if not verify_path.is_file() or not trajectory_path.is_file():
                raise ValueError(f"line {line_no}: missing trajectory/verifier in {run_dir}")
            verify = json.loads(verify_path.read_text(encoding="utf-8"))
            if verify.get("reward_type") != "complete" or verify.get("verify_result", {}).get("execution_status") != "success":
                raise ValueError(f"line {line_no}: verifier is not a successful complete result")
            verified_runs.add(run_key)
        batch.append(row)
        count += 1
        min_tokens = length if min_tokens is None else min(min_tokens, length)
        max_tokens = max(max_tokens, length)
        if len(batch) == args.batch_size:
            encoded = collator(batch)
            if not encoded["labels"].ne(-100).any(dim=1).all():
                raise ValueError(f"line {line_no}: collator produced an empty target")
            batch.clear()
    if batch:
        encoded = collator(batch)
        if not encoded["labels"].ne(-100).any(dim=1).all():
            raise ValueError("final batch: collator produced an empty target")
    report = {
        "records": count,
        "verified_successful_runs": len(verified_runs),
        "unique_sequences": len(seen),
        "min_total_tokens": min_tokens,
        "max_total_tokens": max_tokens,
        "model_max_length": args.model_max_length,
        "collator_batch_size": args.batch_size,
        "status": "passed",
    }
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        f"TEACHER_VALIDATION_SIGNAL status=passed records={count} "
        f"verified_runs={len(verified_runs)} min_tokens={min_tokens} max_tokens={max_tokens}",
        flush=True,
    )


if __name__ == "__main__":
    main()
