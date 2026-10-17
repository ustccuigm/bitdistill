"""Extract calibration conversations from the benchmark's RL training inputs.

Benchmark catalogs and evaluator annotations are not policy contexts. Never
fall back to dumping an arbitrary record as a prompt or inventing a response.
"""
import argparse
import hashlib
import json
from pathlib import Path


def calibration_record(row):
    if isinstance(row, list):
        if len(row) == 1 and isinstance(row[0], list) and len(row[0]) == 2:
            prompt, completion = row[0]
            return calibration_record({"prompt": prompt, "completion": completion})
        raise ValueError("Unsupported calibration list")
    if not isinstance(row, dict):
        raise ValueError("Expected an RL task or conversation object")
    extra = row.get("extra_info") or {}
    split = row.get("split") or (extra.get("split") if isinstance(extra, dict) else None)
    if split is not None and split not in {"train", "training"}:
        raise ValueError(f"Calibration cannot use split={split!r}")
    messages = row.get("messages")
    if messages is not None:
        if not isinstance(messages, list) or not messages:
            raise ValueError("Empty messages in RL data")
        for message in messages:
            if not isinstance(message, dict) or message.get("role") not in {"system", "user", "assistant", "tool"}:
                raise ValueError("Invalid conversation message")
        messages = [message for message in messages if message.get("tool_calls")
                    or str(message.get("content") or "").strip()]
        if not messages or not any(message["role"] == "user" for message in messages):
            raise ValueError("Calibration conversation has no user task")
        result = {"messages": messages}
        if row.get("tools"):
            result["tools"] = row["tools"]
        return result
    prompt = row.get("prompt")
    if not isinstance(prompt, (list, str)) or not prompt or (isinstance(prompt, str) and not prompt.strip()):
        raise ValueError("RL record needs prompt or messages; raw benchmark metadata is not a prompt")
    if isinstance(prompt, list):
        prompt = calibration_record({"messages": prompt})["messages"]
    else:
        # Detect the previous catalog/evaluator JSON serialization fallback.
        try:
            decoded = json.loads(prompt)
        except (ValueError, TypeError):
            decoded = None
        if isinstance(decoded, dict) and any(key in decoded for key in (
            "record", "benchmark_file", "reward_model", "evaluation_criteria", "user_scenario",
        )):
            raise ValueError("Serialized benchmark metadata is not an agent prompt")
    result = {"prompt": prompt}
    completion = row.get("completion")
    if isinstance(completion, str) and completion.strip():
        result["completion"] = completion
    if row.get("completion_tool_calls"):
        if not isinstance(prompt, list):
            raise ValueError("Native completion tool calls need a structured prompt")
        result = {"messages": prompt + [{"role": "assistant", "content": completion or None,
                                        "tool_calls": row["completion_tool_calls"]}]}
    if row.get("tools"):
        result["tools"] = row["tools"]
    return result


def prepare(source, output):
    if source.resolve() == output.resolve():
        raise ValueError("Calibration output must not overwrite the raw RL input")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    count = 0
    input_count = 0
    duplicates = 0
    seen = set()
    source_hash = hashlib.sha256()
    try:
        with source.open("rb") as stream, temporary.open("w", encoding="utf-8") as target:
            for number, line in enumerate(stream, 1):
                source_hash.update(line)
                if not line.strip():
                    continue
                input_count += 1
                try:
                    row = calibration_record(json.loads(line))
                except ValueError as error:
                    raise ValueError(f"{source}:{number}: {error}") from error
                serialized = json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                key = hashlib.sha256(serialized.encode()).hexdigest()
                if key in seen:
                    duplicates += 1
                    continue
                seen.add(key)
                target.write(serialized + "\n")
                count += 1
        if not count:
            raise ValueError("RL calibration input is empty")
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)
    report = {"schema": 1, "input_records": input_count, "kept_records": count,
              "duplicate_records": duplicates, "source_sha256": source_hash.hexdigest(),
              "output_sha256": hashlib.sha256(output.read_bytes()).hexdigest()}
    report_path = output.with_suffix(output.suffix + ".report.json")
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"STEER_CALIBRATION_DATA_SIGNAL status=ready records={count} duplicates={duplicates} output={output}")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    prepare(args.input, args.output)


if __name__ == "__main__":
    main()
