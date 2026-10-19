"""Bind reusable CLIP caches to the actual weights, data, and search settings."""
import argparse
import hashlib
import json
from pathlib import Path


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def model_identity(model):
    model = Path(model)
    weights = sorted(model.glob("*.safetensors")) or sorted(model.glob("pytorch_model*.bin"))
    if not weights:
        raise ValueError(f"No model weights found: {model}")
    files = sorted(set(weights + list(model.glob("*.json")) + list(model.glob("*.jinja"))))
    return {path.name: sha256(path) for path in files}


def check_manifest(recorded, expected, clip):
    if recorded.get("inputs") != expected:
        raise ValueError("CLIP inputs changed: use a new RUN_ROOT or CLIP_PATH")
    if recorded.get("clip_sha256") != sha256(clip):
        raise ValueError("CLIP cache checksum does not match its manifest")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("check", "record"))
    parser.add_argument("--model", required=True, type=Path)
    parser.add_argument("--data", required=True, type=Path)
    parser.add_argument("--clip", required=True, type=Path)
    parser.add_argument("--samples", required=True, type=int)
    parser.add_argument("--seqlen", required=True, type=int)
    parser.add_argument("--grid", required=True, type=int)
    args = parser.parse_args()
    inputs = {"schema": 1, "model": model_identity(args.model),
              "data_sha256": sha256(args.data), "samples": args.samples,
              "seqlen": args.seqlen, "grid": args.grid, "bits": 4, "group_size": 64}
    manifest = args.clip.with_suffix(args.clip.suffix + ".manifest.json")
    if args.mode == "check":
        if not manifest.is_file():
            raise ValueError("CLIP cache has no input manifest; select a fresh CLIP_PATH")
        check_manifest(json.loads(manifest.read_text()), inputs, args.clip)
    else:
        value = {"inputs": inputs, "clip_sha256": sha256(args.clip)}
        temporary = manifest.with_suffix(manifest.suffix + ".tmp")
        temporary.write_text(json.dumps(value, indent=2) + "\n")
        temporary.replace(manifest)
    print(f"STEER_CLIP_PROVENANCE_SIGNAL status=passed mode={args.mode}")


if __name__ == "__main__":
    main()
