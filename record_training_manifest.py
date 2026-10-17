#!/usr/bin/env python3
"""Audit token coverage and window handling before SteerDistill training."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from transformers import AutoTokenizer
from train.chat_templates import normalize_tool_arguments as normalize_messages


def render(value, tokenizer):
    if isinstance(value, list):
        return tokenizer.apply_chat_template(
            normalize_messages(value), tokenize=False, add_generation_prompt=True
        )
    return str(value or "")


def encode(value, tokenizer):
    return list(tokenizer.encode(value, add_special_tokens=False))


def native_completion_ids(prompt, completion, tool_calls, tokenizer):
    if not isinstance(prompt, list):
        raise ValueError(
            "Native tool-call records require a structured prompt when "
            "completion_token_ids are absent."
        )
    history = normalize_messages(prompt)
    assistant = normalize_messages([{
        "role": "assistant",
        "content": completion if completion else None,
        "tool_calls": json.loads(json.dumps(tool_calls)),
    }])[0]
    prompt_ids = encode(
        tokenizer.apply_chat_template(history, tokenize=False, add_generation_prompt=True),
        tokenizer,
    )
    full_ids = encode(
        tokenizer.apply_chat_template(
            history + [assistant], tokenize=False, add_generation_prompt=False
        ),
        tokenizer,
    )
    if full_ids[:len(prompt_ids)] != prompt_ids:
        raise ValueError("Tokenizer chat template cannot isolate native completion.")
    result = full_ids[len(prompt_ids):]
    if not result:
        raise ValueError("Native tool-call template produced no completion tokens.")
    return result


def digest(value):
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--tokenizer", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--run-manifest", type=Path)
    parser.add_argument("--max-length", type=int, required=True)
    args = parser.parse_args()
    tokenizer = AutoTokenizer.from_pretrained(
        str(args.tokenizer), trust_remote_code=True, use_fast=True, local_files_only=True
    )
    eos_id = tokenizer.eos_token_id
    records = []
    quarantined = 0
    head_tail = 0
    with args.data.open(encoding="utf-8") as handle:
        for index, line in enumerate(handle):
            if not line.strip():
                continue
            item = json.loads(line)
            prompt_text = render(item.get("prompt", ""), tokenizer)
            completion_text = str(item.get("completion") or "")
            if item.get("completion_tool_calls") and "completion_content" in item:
                completion_text = str(item["completion_content"] or "")
            prompt_ids = list(item.get("prompt_token_ids") or encode(prompt_text, tokenizer))
            prompt_ids.extend(item.get("prompt_suffix_token_ids") or [])
            completion_ids = list(item.get("completion_token_ids") or [])
            completion_representation = "recorded_token_ids" if completion_ids else "text"
            if not completion_ids and item.get("completion_tool_calls"):
                completion_ids = native_completion_ids(
                    item.get("prompt"), completion_text,
                    item["completion_tool_calls"], tokenizer
                )
                completion_representation = "native_chat_template"
            if not completion_ids:
                completion_ids = encode(completion_text, tokenizer)
            if item.get("add_eos", True) and eos_id is not None and (
                not completion_ids or completion_ids[-1] != eos_id
            ):
                completion_ids.append(eos_id)
            steer_text = render(item.get("skill_prompt", ""), tokenizer) if "skill_prompt" in item else ""
            steer_ids = encode(steer_text, tokenizer) if "skill_prompt" in item else []
            prompt_budget = args.max_length - len(completion_ids)
            prompt_head = len(prompt_ids)
            prompt_tail = 0
            retained_head_tail = False
            if len(completion_ids) >= args.max_length:
                status = "quarantine_completion_over_window"
                quarantined += 1
            elif len(steer_ids) > prompt_budget:
                status = "quarantine_steer_prompt_over_window"
                quarantined += 1
            else:
                status = "ok"
                if len(prompt_ids) > prompt_budget:
                    retained_head_tail = True
                    head_budget = min(1024, max(1, prompt_budget // 4))
                    prompt_head = min(head_budget, len(prompt_ids))
                    prompt_tail = max(0, prompt_budget - prompt_head)
                    head_tail += 1
            records.append({
                "row_index": index,
                "task_key": item.get("task_key"),
                "distill_mode": item.get("distill_mode", "ordinary_opd"),
                "completion_representation": completion_representation,
                "prompt_tokens": len(prompt_ids),
                "completion_tokens": len(completion_ids),
                "steer_prompt_tokens": len(steer_ids),
                "response_supervision_tokens": len(completion_ids),
                "response_supervision": "full_response_including_reasoning_action_and_eos",
                "history_head_tail_retained": retained_head_tail,
                "retained_prompt_head_tokens": prompt_head,
                "retained_prompt_tail_tokens": prompt_tail,
                "max_length": args.max_length,
                "window_status": status,
                "prompt_sha256": digest(prompt_text),
                "completion_sha256": digest(completion_text),
                "steer_prompt_sha256": digest(steer_text) if "skill_prompt" in item else None,
            })
    payload = {
        "schema": 1,
        "data": str(args.data.name),
        "tokenizer": str(args.tokenizer.name),
        "max_length": args.max_length,
        "records": len(records),
        "quarantined_records": quarantined,
        "history_head_tail_records": head_tail,
        "response_supervision": "full_response_including_reasoning_action_and_eos",
        "rows": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    args.output.write_text(serialized, encoding="utf-8")
    if args.run_manifest is not None and args.run_manifest.is_file():
        run_manifest = json.loads(args.run_manifest.read_text(encoding="utf-8"))
        run_manifest["training_data_manifest"] = payload
        args.run_manifest.write_text(
            json.dumps(run_manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(
        f"STEER_DATA_MANIFEST_SIGNAL records={len(records)} "
        f"quarantined={quarantined} head_tail={head_tail} output={args.output}"
    )
    if quarantined:
        raise SystemExit(3)


if __name__ == "__main__":
    main()
