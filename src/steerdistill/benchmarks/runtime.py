"""Scoped local vLLM processes; stop only processes created by this run."""
from contextlib import AbstractContextManager
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import time
import urllib.request


class Runtime(AbstractContextManager):
    def __init__(self, model, name, gpus, port, log, *, quantized=False, tool_calls=False):
        self.model, self.name, self.gpus = model, name, gpus
        self.port, self.log, self.quantized = port, Path(log), quantized
        self.tool_calls = tool_calls
        self.url = f"http://127.0.0.1:{port}/v1"
        self.process = self.handle = None

    def __enter__(self):
        with socket.socket() as probe:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            probe.bind(("127.0.0.1", self.port))
        self.log.parent.mkdir(parents=True, exist_ok=True)
        self.handle = self.log.open("a")
        command = [str(Path(os.environ["INFERENCE_ENV_ROOT"]) / "bin/python"),
                   "-m", "vllm.entrypoints.openai.api_server", "--model", str(self.model),
                   "--served-model-name", self.name, "--host", "127.0.0.1", "--port", str(self.port),
                   "--dtype", "bfloat16", "--max-model-len", os.getenv("MODEL_MAX_LENGTH", "32768"),
                   "--max-num-seqs", os.getenv("MAX_NUM_SEQS", "8"),
                   "--gpu-memory-utilization", os.getenv("STREAM_GPU_MEMORY_UTILIZATION", "0.82"),
                   "--tensor-parallel-size", str(len(self.gpus.split(","))),
                   "--seed", os.getenv("SEED", "42"), "--trust-remote-code"]
        config = json.loads((Path(self.model) / "config.json").read_text())
        # All supported benchmark adapters submit text, including tool messages.
        if config.get("model_type") == "qwen3_5":
            command += ["--language-model-only"]
        if config.get("model_type") == "gemma4_unified_text":
            command += ["--enforce-eager"]
        if self.tool_calls:
            model_type = config.get("model_type")
            parser, reasoning = {
                "qwen3": ("hermes", "qwen3"),
                "qwen3_5": ("qwen3_xml", "qwen3"),
                "gemma4_unified_text": ("gemma4", "gemma4"),
            }[model_type]
            command += ["--enable-auto-tool-choice", "--tool-call-parser", parser,
                        "--reasoning-parser", reasoning]
        env = dict(os.environ, CUDA_VISIBLE_DEVICES=self.gpus)
        # Unix socket paths are limited to 107 bytes; run directories can be longer.
        env.setdefault("VLLM_RPC_BASE_PATH", "/tmp")
        env.pop("PYTHONPATH", None)
        try:
            self.process = subprocess.Popen(command, env=env, stdout=self.handle,
                                            stderr=subprocess.STDOUT, start_new_session=True)
            deadline = time.monotonic() + 900
            while time.monotonic() < deadline:
                if self.process.poll() is not None:
                    raise RuntimeError(f"Inference server exited: {self.log}")
                try:
                    with urllib.request.urlopen(self.url + "/models", timeout=3) as response:
                        names = {row["id"] for row in json.load(response)["data"]}
                    if self.name not in names:
                        raise RuntimeError(f"Unexpected model served at {self.url}: {names}")
                    return self
                except (OSError, ValueError):
                    time.sleep(2)
            raise TimeoutError(f"Inference server failed readiness: {self.log}")
        except BaseException:
            self.__exit__(None, None, None)
            raise

    def __exit__(self, *exc):
        if self.process is not None and self.process.poll() is None:
            os.killpg(self.process.pid, signal.SIGTERM)
            try:
                self.process.wait(timeout=45)
            except subprocess.TimeoutExpired:
                os.killpg(self.process.pid, signal.SIGKILL)
                self.process.wait(timeout=10)
        if self.handle is not None:
            self.handle.close()
        return False
