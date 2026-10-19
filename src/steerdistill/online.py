"""Fresh trajectory batches with one persistent optimizer update per batch."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import random
import signal
import subprocess

from steerdistill.manifests import sha256


def epoch_batches(rows, size, epochs, seed, max_steps):
    step = 0
    for epoch in range(epochs):
        order = list(range(len(rows)))
        random.Random(seed + epoch).shuffle(order)
        for start in range(0, len(order), size):
            if max_steps and step >= max_steps:
                return
            step += 1
            indices = order[start:start + size]
            yield step, epoch + 1, indices, [rows[i] for i in indices]


def atomic_json(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def model_digest(path):
    root = Path(path)
    if not (root / "config.json").is_file() or not list(root.glob("*.safetensors")):
        raise ValueError(f"Incomplete model: {root}")
    digest = hashlib.sha256()
    for file in sorted(root.iterdir()):
        if file.is_file() and file.suffix in {".json", ".safetensors", ".jinja"}:
            digest.update(file.name.encode())
            digest.update(sha256(file).encode())
    return digest.hexdigest()


def run_command(command, env, log):
    process = subprocess.Popen(command, env=env, stdout=log, stderr=subprocess.STDOUT,
                               start_new_session=True)
    try:
        code = process.wait()
    except BaseException:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=60)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
        raise
    if code:
        raise subprocess.CalledProcessError(code, command)


def _run_scheduler(root, run, args):
    key = "PROMPT_MANIFEST" if os.environ["BENCHMARK_ENGINE"] == "tool_env" else "BENCHMARK_RL_TRAIN_DATA"
    prompts = Path(os.environ[key])
    raw = prompts.read_bytes()
    rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
    cfg = {
        "schema": 1, "method": "steerdistill_online",
        "benchmark": "bfcl_v4" if os.environ["BENCHMARK"] == "tau2_bench" else os.environ["BENCHMARK"],
        "engine": os.environ["BENCHMARK_ENGINE"], "model_family": os.environ["MODEL_FAMILY"],
        "prompts_sha256": hashlib.sha256(raw).hexdigest(), "num_prompts": len(rows),
        "global_batch_size": int(os.getenv("OPD_GLOBAL_BATCH_SIZE", "16")),
        "micro_batch_size": int(os.getenv("OPD_MICRO_BATCH_SIZE", "1")),
        "turn_batch_size": int(os.getenv("ONLINE_TURN_BATCH_SIZE", "1")),
        "epochs": int(os.getenv("OPD_EPOCHS", "2")),
        "max_steps": int(os.getenv("OPD_MAX_STEPS", "0")),
        "seed": int(os.getenv("OPD_SEED", "42")), "drop_last": False,
        "generations_per_prompt": 1,
        "teacher": os.environ["TEACHER_MODEL"], "initial_master": os.environ["INITIAL_W4_MASTER"],
        "initial_runtime": os.environ["INITIAL_RUNTIME_W4"], "clip": os.environ["CLIP_PATH"],
        "gpu_ids": args.gpu_ids, "train_gpu_ids": os.getenv("TRAIN_GPU_IDS", args.gpu_ids),
        "model_max_length": int(os.getenv("MODEL_MAX_LENGTH", "32768")),
        "learning_rate": float(os.getenv("LEARNING_RATE", "8e-6")),
        "sampling": {key: os.getenv(key) for key in (
            "MAX_ITERATIONS", "MAX_TOKENS", "ROLLOUT_TEMPERATURE",
            "COUNTERFACTUAL_ATTEMPTS", "VALIDATION_ATTEMPTS")},
    }
    for key in ("global_batch_size", "micro_batch_size", "turn_batch_size", "epochs"):
        if cfg[key] < 1:
            raise ValueError(f"{key} must be positive")
    if cfg["max_steps"] < 0:
        raise ValueError("max_steps must be zero (unlimited) or positive")
    if not rows:
        raise ValueError("The input does not contain any trajectory tasks")
    world = len(cfg["train_gpu_ids"].split(","))
    if cfg["global_batch_size"] % (world * cfg["micro_batch_size"]):
        raise ValueError("Trajectory batch must divide by training ranks times trajectory microbatch")
    cfg["input_hashes"] = {key: model_digest(cfg[key]) for key in
                           ("teacher", "initial_master", "initial_runtime")}
    cfg["input_hashes"]["clip"] = sha256(Path(cfg["clip"]))
    config_path = run / "run_config.json"
    if config_path.exists() and json.loads(config_path.read_text()) != cfg:
        raise ValueError("Online run inputs changed; select a new STEER_ONLINE_ROOT")
    atomic_json(config_path, cfg)
    master, runtime, previous = cfg["initial_master"], cfg["initial_runtime"], 0
    latest = None
    for step, epoch, indices, batch in epoch_batches(
        rows, cfg["global_batch_size"], cfg["epochs"], cfg["seed"], cfg["max_steps"]
    ):
        directory = run / "steps" / f"step{step:06d}"
        done = directory / "complete.json"
        manifest = {"rollout_step": step, "epoch": epoch, "prompt_indices": indices,
                    "input_master": master, "input_runtime": runtime,
                    "previous_optimizer_step": previous, "expected_optimizer_updates": 1}
        if done.is_file():
            state = json.loads(done.read_text())
            if any(state.get(key) != value for key, value in manifest.items()):
                raise ValueError("Completed step has a different trajectory/model lineage")
            if state.get("optimizer_step") != previous + 1:
                raise ValueError("Completed step did not perform exactly one optimizer update")
            for key in ("master", "runtime"):
                if model_digest(state[f"output_{key}"]) != state[f"{key}_sha256"]:
                    raise ValueError(f"Completed step has a modified {key}")
            master, runtime, previous = state["output_master"], state["output_runtime"], state["optimizer_step"]
            latest = state
            continue
        if directory.exists():
            if os.getenv("OPD_RESUME_ROLLOUT_ONLY") != "1":
                raise ValueError(f"Partial step requires inspection before retry: {directory}")
            if json.loads((directory / "input.json").read_text()) != manifest:
                raise ValueError("Partial step has different trajectory/model inputs")
            train = directory / "train"
            if any(train.glob("*")):
                raise ValueError("Partial step has training artifacts; optimizer recovery requires inspection")
        else:
            directory.mkdir(parents=True)
        prompt_path = directory / "prompts.jsonl"
        prompt_path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in batch))
        atomic_json(directory / "input.json", manifest)
        env = dict(os.environ, STEER_ONLINE_ROOT=str(run), PROMPT_MANIFEST=str(prompt_path),
                   STEER_RL_TRAIN_DATA=str(prompt_path), OPD_STUDENT_MASTER=master,
                   OPD_STUDENT_RUNTIME=runtime, OPD_PREVIOUS_OPTIMIZER_STEP=str(previous),
                   OPD_EXPECTED_TRAJECTORIES=str(len(batch)), DISCOVERY_ATTEMPTS="1",
                   SEED=str(cfg["seed"]), STEER_SKILL_STORE=str(run / "skill_store/events.jsonl"))
        atomic_json(run / "status.json", dict(manifest, status="running"))
        try:
            with (directory / "step.log").open("a") as log:
                run_command(
                    ["bash", str(root / "scripts/run/run_rollout_step.sh"), str(step), args.gpu_ids],
                    env,
                    log,
                )
            training = json.loads((directory / "train/training_signal.json").read_text())
            if training["global_step"] != previous + 1 or training["previous_step"] != previous:
                raise ValueError("Online step must advance the optimizer exactly once")
            master = str(run / "checkpoints" / f"student-step{step:06d}-hf")
            runtime = str(run / "checkpoints" / f"student-step{step:06d}-awq-runtime")
            previous = training["global_step"]
            latest = dict(manifest, output_master=master, output_runtime=runtime,
                          optimizer_step=previous, training_signal=training,
                          master_sha256=model_digest(master), runtime_sha256=model_digest(runtime))
            atomic_json(done, latest)
            atomic_json(run / "latest.json", latest)
            atomic_json(run / "status.json", dict(manifest, status="completed"))
        except BaseException as error:
            atomic_json(run / "status.json", dict(manifest, status="interrupted" if isinstance(error, KeyboardInterrupt)
                                                  else "failed", error=str(error)))
            raise
        print(f"STEER_ONLINE_STEP_SIGNAL step={step} optimizer_step={previous} status=ready runtime={runtime}", flush=True)
    if latest is not None:
        atomic_json(run / "latest.json", latest)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gpu-ids", required=True)
    args = parser.parse_args()
    root = Path(os.environ.get("STEERDISTILL_ROOT", Path(__file__).resolve().parents[2])).resolve()
    run = Path(os.environ["STEER_ONLINE_ROOT"]).resolve()
    if (run.exists() and any(path.name != ".scheduler.lock" for path in run.iterdir())
            and not (run / "run_config.json").is_file()):
        raise ValueError("Existing output directory has no online run configuration")
    run.mkdir(parents=True, exist_ok=True)
    with (run / ".scheduler.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return _run_scheduler(root, run, args)


if __name__ == "__main__":
    def interrupt(signum, frame):
        raise KeyboardInterrupt(f"Received signal {signum}")
    signal.signal(signal.SIGTERM, interrupt)
    main()
