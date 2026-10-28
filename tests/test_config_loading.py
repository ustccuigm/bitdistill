"""Configuration entry-point contracts; no GPU or model dependencies required."""
import os
from pathlib import Path
import shutil
import re
import shlex
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
ENTRY_POINTS = (
    "scripts/run/run_benchmark.sh", "scripts/run/run_online.sh",
    "scripts/run/reproduce_results.sh", "scripts/prepare/prepare_quant_assets.sh",
    "scripts/validate/preflight.sh",
)


class ConfigLoadingTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name) / "checkout with spaces"
        for name in (
            "scripts/_bootstrap.sh", "scripts/lib/load_config.sh",
            "scripts/lib/select_benchmark.sh", "scripts/lib/run_paths.sh",
            "scripts/lib/precision.sh",
            "configs/local.example.env", "configs/steerdistill.example.env",
            "configs/benchmark-paths.example.env",
        ) + ENTRY_POINTS:
            destination = self.root / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, destination)

    def run_shell(self, command, **environment):
        return subprocess.run(
            ["bash", "-euc", 'source scripts/_bootstrap.sh\n'
             'source scripts/lib/load_config.sh\n' + command],
            cwd=self.root, env={"PATH": os.environ["PATH"], **environment},
            text=True, capture_output=True,
        )

    def install_local_config(self):
        shutil.copyfile(self.root / "configs/local.example.env",
                        self.root / "configs/local.env")

    def test_local_config_loads_and_exports_without_manual_setup(self):
        self.install_local_config()
        result = self.run_shell(
            "bash -uc 'printf \"%s\\n\" \"$MODEL_FAMILY\" \"$BENCHMARK\" "
            "\"$ENV_ROOT\" \"$GPU_IDS\" \"$LEARNING_RATE\"'"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), [
            "qwen3_8b", "bfcl_v4", str(self.root / ".venv"),
            "0,1,2,3,4,5,6,7", "8e-6",
        ])

    def test_precision_isolated_for_every_model_and_benchmark(self):
        self.install_local_config()
        for model in ("qwen3_8b", "qwen3_5_4b", "gemma4_12b"):
            for benchmark in ("bfcl_v4", "tau2_bench", "webshop", "alfworld", "search_qa"):
                for precision, bits, activation in (("w2a16", 2, 16), ("w4a8", 4, 8)):
                    with self.subTest(model=model, benchmark=benchmark, precision=precision):
                        result = self.run_shell(
                            'printf "%s\\n" "$BITS" "$ACTIVATION_BITS" "$RUN_ROOT" "$TRAINING_RUN_ROOT" "$CLIP_PATH"',
                            STEER_ASSET_ROOT="/assets", MODEL_FAMILY=model,
                            BENCHMARK=benchmark, QUANT_PRECISION=precision,
                        )
                        self.assertEqual(result.returncode, 0, result.stderr)
                        b, a, run, training, clip = result.stdout.splitlines()
                        self.assertEqual((b, a), (str(bits), str(activation)))
                        self.assertEqual(run, f"/assets/runs/{model}/{benchmark}/{precision}")
                        training_benchmark = "bfcl_v4" if benchmark == "tau2_bench" else benchmark
                        self.assertEqual(training, f"/assets/runs/{model}/{training_benchmark}/{precision}")
                        self.assertEqual(clip, f"{training}/checkpoints/clip-int{bits}-g64.pt")

    def test_conflicting_precision_fails_before_running(self):
        self.install_local_config()
        result = self.run_shell('echo unexpected', QUANT_PRECISION="w2a16", BITS="4")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('conflict', result.stderr)

    def test_explicit_config_takes_precedence_and_survives_directory_change(self):
        self.install_local_config()
        (self.root / "custom.env").write_text('CUSTOM_VALUE="private value"\n')
        result = self.run_shell(
            'cd /\nbash -euc \'source "$STEER_CONFIG"; printf "%s" "$CUSTOM_VALUE"\'',
            STEER_CONFIG="custom.env",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "private value")

    def test_missing_explicit_config_does_not_silently_fallback(self):
        self.install_local_config()
        result = self.run_shell("echo unexpected", STEER_CONFIG="absent.env")
        self.assertEqual(result.returncode, 2)
        self.assertIn("Configuration not found", result.stderr)
        self.assertNotIn("unexpected", result.stdout)

    def test_legacy_environment_only_configuration(self):
        result = self.run_shell(
            'printf "%s" "$MODEL_SOURCE_PATH"',
            STEER_ASSET_ROOT="/assets", ENV_ROOT="/environment",
            MODEL_FAMILY="gemma4_12b", BENCHMARK="alfworld",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "/assets/models/gemma4_12b/alfworld")

    def test_local_template_preserves_all_route_paths(self):
        self.install_local_config()
        runs = set()
        checkpoints = set()
        for model in ("qwen3_8b", "qwen3_5_4b", "gemma4_12b"):
            for benchmark in ("bfcl_v4", "tau2_bench", "webshop", "alfworld", "search_qa"):
                with self.subTest(model=model, benchmark=benchmark):
                    result = self.run_shell(
                        'printf "%s\\n" "$MODEL_SOURCE_PATH" "$RUN_ROOT" "$CLIP_PATH"',
                        STEER_ASSET_ROOT="/assets", MODEL_FAMILY=model, BENCHMARK=benchmark,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    checkpoint, run, clip = result.stdout.splitlines()
                    group = "tool_use" if benchmark in ("bfcl_v4", "tau2_bench") else benchmark
                    self.assertEqual(checkpoint, f"/assets/models/{model}/{group}")
                    self.assertEqual(run, f"/assets/runs/{model}/{benchmark}")
                    training = "bfcl_v4" if benchmark == "tau2_bench" else benchmark
                    self.assertIn(f"/assets/runs/{model}/{training}/", clip)
                    runs.add(run)
                    checkpoints.add(checkpoint)
        self.assertEqual(len(runs), 15)
        self.assertEqual(len(checkpoints), 12)

    def test_reloading_config_keeps_custom_paths(self):
        self.install_local_config()
        result = self.run_shell(
            'before="$MODEL_SOURCE_PATH|$RUN_ROOT|$CLIP_PATH"\n'
            'source scripts/lib/load_config.sh\n'
            '[[ "$before" == "$MODEL_SOURCE_PATH|$RUN_ROOT|$CLIP_PATH" ]]',
            QWEN3_8B_TOOL_USE_MODEL="/checkpoints/custom teacher",
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_loader_preserves_allexport_shell_option(self):
        self.install_local_config()
        result = self.run_shell(
            '[[ $- != *a* ]]\nset -a\nsource scripts/lib/load_config.sh\n[[ $- == *a* ]]'
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_all_public_entry_points_read_local_config(self):
        (self.root / "configs/local.env").write_text('echo LOCAL_CONFIG_LOADED\nreturn 73\n')
        for entry_point in ENTRY_POINTS:
            with self.subTest(entry_point=entry_point):
                result = subprocess.run(
                    ["bash", str(self.root / entry_point)], cwd="/",
                    env={"PATH": os.environ["PATH"]}, text=True, capture_output=True,
                )
                self.assertEqual(result.returncode, 73, result.stderr)
                self.assertEqual(result.stdout.strip(), "LOCAL_CONFIG_LOADED")

    def test_online_entry_uses_gpu_setting_and_accepts_positional_override(self):
        interpreter = self.root / "fake environment/bin/python"
        interpreter.parent.mkdir(parents=True)
        interpreter.write_text('#!/bin/bash\nprintf "%s\\n" "$@"\n')
        interpreter.chmod(0o755)
        (self.root / "configs/local.env").write_text(
            f'ENV_ROOT="{interpreter.parent.parent}"\nGPU_IDS=4,5\n'
        )
        for arguments, expected in (([], "4,5"), (["6,7"], "6,7")):
            result = subprocess.run(
                ["bash", str(self.root / "scripts/run/run_online.sh"), *arguments],
                env={"PATH": os.environ["PATH"]}, text=True, capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.splitlines()[-2:], ["--gpu-ids", expected])

    def test_route_help_and_invalid_options_do_not_load_configuration(self):
        launcher = self.root / "scripts/run/run_benchmark.sh"
        for arguments, code in ((["--help"], 0), (["train", "--model"], 2),
                                (["train", "--model", "unknown"], 2),
                                (["eval", "--benchmark", "unknown"], 2),
                                (["quantize", "--unexpected"], 2), (["invalid"], 2)):
            with self.subTest(arguments=arguments):
                result = subprocess.run(
                    ["bash", str(launcher), *arguments],
                    env={"PATH": os.environ["PATH"]}, text=True, capture_output=True,
                )
                self.assertEqual(result.returncode, code, result.stderr)
                self.assertNotIn("Set STEER_ASSET_ROOT", result.stderr)

    def prepare_route_stubs(self):
        self.install_local_config()
        for name in (
            "scripts/prepare/prepare_quant_assets.sh", "scripts/prepare/prepare_initial_runtime.sh",
            "scripts/run/run_online.sh", "scripts/run/evaluate.sh", "scripts/validate/preflight.sh",
        ):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                '#!/bin/bash\nprintf "%s|%s|%s|%s\\n" '
                '"$MODEL_FAMILY" "$BENCHMARK" "$MODEL_SOURCE_PATH" "$RUN_ROOT"\n'
            )
        interpreter = self.root / "stub-env/bin/python"
        interpreter.parent.mkdir(parents=True)
        interpreter.write_text("#!/bin/bash\nexit 0\n")
        interpreter.chmod(0o755)
        return {"PATH": os.environ["PATH"], "STEER_ASSET_ROOT": str(self.root / "assets"),
                "ENV_ROOT": str(interpreter.parent.parent),
                "INFERENCE_ENV_ROOT": str(interpreter.parent.parent)}

    def test_readme_training_commands_dispatch_to_the_documented_routes(self):
        environment = self.prepare_route_stubs()
        commands = re.findall(r"^bash scripts/run/run_benchmark.sh (.+)$",
                              (ROOT / "README.md").read_text() + "\n" +
                              (ROOT / "docs/training/README.md").read_text(), re.MULTILINE)
        covered = set()
        for command in commands:
            arguments = shlex.split(command)
            model = arguments[arguments.index("--model") + 1]
            benchmark = arguments[arguments.index("--benchmark") + 1]
            with self.subTest(command=command):
                result = subprocess.run(
                    ["bash", str(self.root / "scripts/run/run_benchmark.sh"), *arguments],
                    env=environment, text=True, capture_output=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                group = "tool_use" if benchmark in ("bfcl_v4", "tau2_bench") else benchmark
                expected = f"{model}|{benchmark}|{self.root}/assets/models/{model}/{group}|{self.root}/assets/runs/{model}/{benchmark}"
                self.assertTrue(result.stdout.strip())
                self.assertTrue(all(row == expected for row in result.stdout.splitlines()), result.stdout)
                covered.add((arguments[0], model, benchmark))
        expected_training = {
            (stage, model, benchmark)
            for stage in ("quantize", "train")
            for model in ("qwen3_8b", "qwen3_5_4b", "gemma4_12b")
            for benchmark in ("bfcl_v4", "webshop", "alfworld", "search_qa")
        }
        self.assertTrue(expected_training <= covered)

    def test_full_dispatch_preserves_selected_route_in_child_launchers(self):
        environment = self.prepare_route_stubs()
        result = subprocess.run(
            ["bash", str(self.root / "scripts/run/run_benchmark.sh"), "full",
             "--model", "gemma4_12b", "--benchmark", "webshop"],
            env=environment, text=True, capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(result.stdout.splitlines()), 7)
        self.assertTrue(all(row.startswith("gemma4_12b|webshop|") for row in result.stdout.splitlines()))

    def test_fixed_config_cannot_silently_override_requested_route(self):
        environment = self.prepare_route_stubs()
        (self.root / "configs/local.env").write_text('MODEL_FAMILY=qwen3_8b\nBENCHMARK=bfcl_v4\n')
        result = subprocess.run(
            ["bash", str(self.root / "scripts/run/run_benchmark.sh"), "train",
             "--model", "gemma4_12b", "--benchmark", "webshop"],
            env=environment, text=True, capture_output=True,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("overrides the requested route", result.stderr)


if __name__ == "__main__":
    unittest.main()
