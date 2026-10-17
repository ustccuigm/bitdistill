"""Run native benchmark revision with scoped student and teacher servers."""
import os
import signal
from pathlib import Path
import subprocess
import sys
from contextlib import ExitStack
from runtime import Runtime


def main():
    root = Path(__file__).resolve().parent
    output = Path(os.environ["STEER_STEP_DIR"])
    gpus = os.environ["STEER_GPU_IDS"].split(",")
    if len(gpus) < 2:
        raise ValueError("Native online revision requires separate student and teacher GPUs")
    model = os.environ["MODEL_SERVING_NAME"]
    port = int(os.getenv("BASE_PORT", "34000"))
    with ExitStack() as stack:
        student = stack.enter_context(Runtime(os.environ["STEER_RUNTIME_PATH"], model,
            os.getenv("NATIVE_STUDENT_GPU", gpus[0]), port, output / "logs/student.log", quantized=True))
        teacher = stack.enter_context(Runtime(os.environ["STEER_TEACHER_MODEL"], model,
            os.getenv("NATIVE_TEACHER_GPU", gpus[-1]), port + 1, output / "logs/teacher.log"))
        subprocess.run([sys.executable, str(root / "online_rollout.py"),
            "--benchmark", os.environ["STEER_BENCHMARK"],
            "--tasks", os.environ["STEER_RL_TRAIN_DATA"], "--output", str(output),
            "--store", os.environ["STEER_SKILL_STORE"], "--step", os.environ["STEER_STEP"],
            "--student-url", student.url, "--teacher-url", teacher.url, "--model", model,
            "--attempts", os.getenv("DISCOVERY_ATTEMPTS", "1"),
            "--reference-attempts", os.getenv("COUNTERFACTUAL_ATTEMPTS", "4"),
            "--retries", os.getenv("VALIDATION_ATTEMPTS", "4"),
            "--workers", os.getenv("REPAIR_WORKERS", "4")], check=True)


if __name__ == "__main__":
    def interrupt(signum, frame):
        raise KeyboardInterrupt(f"Received signal {signum}")
    signal.signal(signal.SIGTERM, interrupt)
    main()
