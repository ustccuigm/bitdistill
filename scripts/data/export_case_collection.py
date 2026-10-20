"""Export the selected case collection into a stable public data layout."""
import argparse
import hashlib
import json
from pathlib import Path


METHODS = ("BF16", "Ours", "GPTQ", "EfficientQAT", "BitDistiller", "On-Policy QAD", "QeRL")


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path, help="Website data directory")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--revision", required=True, help="Website Git commit")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output already exists; choose a new directory")
    index = json.loads((args.source / "case_index.json").read_text())
    if len(index) != 40 or len({row["task_id"] for row in index}) != 40:
        raise ValueError("Expected the 40 selected tasks")
    hashes = {}
    for row in index:
        source = args.source / row["path"]
        destination = args.output / source.name
        for name in ("task.json", "ground_truth.json", "analysis.json"):
            content = (source / name).read_bytes()
            dump(destination / name, json.loads(content))
            hashes[f"{source.name}/{name}"] = hashlib.sha256(content).hexdigest()
        summary = (source / "summary.md").read_text().replace("原始任务", "任务")
        (destination / "summary.md").write_text(summary.rstrip() + "\n")
        for method in METHODS:
            for name in ("trajectory.json", "actions.json", "request_metadata.json"):
                content = (source / method / name).read_bytes()
                dump(destination / method / name, json.loads(content))
                hashes[f"{source.name}/{method}/{name}"] = hashlib.sha256(content).hexdigest()
            transcript = source / method / "cot_and_actions.txt"
            (destination / method / transcript.name).write_bytes(transcript.read_bytes())
            score = json.loads((source / method / "score.json").read_text())
            if score["passed"] != (method in ("BF16", "Ours")):
                raise ValueError(f"Unexpected selected outcome: {row['task_id']} {method}")
            dump(destination / method / "score.json", {
                key: value for key, value in score.items() if key not in ("score_file", "source_dir")
            })
        row["path"] = source.name
    dump(args.output / "index.json", index)
    dump(args.output / "collection.json", {
        "description": "整理的数据",
        "selection": "BF16 and Ours pass; the five comparison methods fail in the selected trajectories.",
        "methods": METHODS, "cases": 40,
        "source": f"https://github.com/ustccuigm/bitdistill/tree/{args.revision}/data",
        "file_sha256_before_formatting": hashes,
    })
    (args.output / "results.csv").write_text((args.source / "results.csv").read_text())
    print(f"Exported {len(index)} cases and {len(index) * len(METHODS)} method trajectories")


if __name__ == "__main__":
    main()
