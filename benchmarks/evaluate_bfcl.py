"""Official BFCL V4 generation and scoring through the native model template."""
import argparse
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace

from runtime import Runtime
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from generation_budget import apply_budget


def serializable_messages(messages):
    return [message.model_dump(mode="json", exclude_none=True)
            if hasattr(message, "model_dump") else message for message in messages]


def register_model(mapping, name, config):
    # BFCL reverses its filesystem escaping by replacing underscores with slashes.
    mapping[name] = config
    mapping[name.replace("_", "/")] = config


def validate_results(result_dir, expected_ids=None):
    actual_ids = set()
    for path in result_dir.rglob("*_result.json"):
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("traceback") or (isinstance(row.get("result"), str)
                    and row["result"].startswith("Error during inference:")):
                raise RuntimeError(f"BFCL inference failed for {row.get('id')}; inspect {path}")
            if row["id"] in actual_ids:
                raise RuntimeError(f"Duplicate BFCL result: {row['id']}")
            actual_ids.add(row["id"])
    if not actual_ids or (expected_ids is not None and not expected_ids <= actual_ids):
        raise RuntimeError("BFCL generation did not produce every selected task")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--gpus", default="0")
    parser.add_argument("--task-ids", type=Path, help="Official BFCL category-to-task-IDs JSON selection")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    os.environ["BFCL_PROJECT_ROOT"] = str(args.output.resolve())
    from bfcl_eval._llm_response_generation import main as generate
    from bfcl_eval.eval_checker.eval_runner import main as evaluate
    from bfcl_eval.constants.model_config import MODEL_CONFIG_MAPPING, ModelConfig
    from bfcl_eval.model_handler.api_inference.openai_completion import OpenAICompletionsHandler
    if args.task_ids:
        from bfcl_eval.utils import load_test_entries_from_id_file
        selection = json.loads(args.task_ids.read_text())
        if not isinstance(selection, dict) or not selection:
            raise ValueError("BFCL task selection must be a nonempty category-to-IDs object")
        for ids in selection.values():
            if not isinstance(ids, list) or not ids or not all(isinstance(value, str) for value in ids) or len(set(ids)) != len(ids):
                raise ValueError("Each selected category must contain unique task IDs")
        _, entries = load_test_entries_from_id_file(args.task_ids)
        expected_ids = {identity for ids in selection.values() for identity in ids}
        if {entry["id"] for entry in entries} != expected_ids:
            raise ValueError("BFCL selection contains unknown task IDs")
        (args.output / "test_case_ids_to_generate.json").write_text(json.dumps(selection) + "\n")
    if not os.getenv("SERPAPI_API_KEY") and (not args.task_ids or any("web_search" in name for name in selection)):
        raise ValueError("BFCL web search requires SERPAPI_API_KEY")

    class NativeStudentHandler(OpenAICompletionsHandler):
        def _query_FC(self, inference_data):
            messages = serializable_messages(inference_data["message"])
            inference_data["inference_input_log"] = {
                "messages": messages, "tools": inference_data["tools"]}
            kwargs = {"model": self.model_name, "messages": messages,
                      "temperature": self.temperature, "seed": 42,
                      "max_tokens": int(os.getenv("EVAL_MAX_TOKENS", "32768"))}
            if inference_data["tools"]:
                kwargs["tools"] = inference_data["tools"]
            apply_budget(os.environ["OPENAI_BASE_URL"], kwargs)
            return self.generate_with_backoff(**kwargs)

        def _parse_query_response_FC(self, response):
            result = super()._parse_query_response_FC(response)
            self._add_reasoning_content_if_available_FC(response, result)
            return result

    register_model(MODEL_CONFIG_MAPPING, args.model, ModelConfig(
        model_name=args.model, display_name=args.model, url="", org="", license="",
        model_handler=NativeStudentHandler, is_fc_model=True,
    ))
    port = int(os.getenv("EVAL_PORT", "34400"))
    with Runtime(args.runtime, args.model, args.gpus, port, args.output / "runtime.log",
                 quantized=True, tool_calls=True) as runtime:
        os.environ["OPENAI_BASE_URL"] = runtime.url
        os.environ["OPENAI_API_KEY"] = "EMPTY"
        generate(SimpleNamespace(model=[args.model], test_category=["all_scoring"],
            temperature=float(os.getenv("EVAL_TEMPERATURE", "0.001")), include_input_log=True,
            exclude_state_log=False, num_gpus=1, num_threads=int(os.getenv("EVAL_WORKERS", "4")),
            gpu_memory_utilization=0.82, backend="vllm", skip_server_setup=True,
            local_model_path=str(args.runtime), result_dir=str(args.output / "results"),
            allow_overwrite=False, run_ids=bool(args.task_ids)))
    # Subsets must contain every requested result before partial scoring.
    categories = list(selection) if args.task_ids else ["all_scoring"]
    validate_results(args.output / "results", expected_ids if args.task_ids else None)
    evaluate([args.model], categories, str(args.output / "results"),
             str(args.output / "scores"), bool(args.task_ids))
    report = args.output / "scores/data_overall.csv"
    if not report.is_file():
        raise RuntimeError("Official BFCL scorer produced no overall results")
    (args.output / "evaluation_scope.json").write_text(json.dumps({
        "scope": "subset" if args.task_ids else "full", "categories": categories,
        "task_ids": sorted(expected_ids) if args.task_ids else None}, indent=2) + "\n")
    scope = "subset" if args.task_ids else "full"
    print(f"STEER_EVAL_SIGNAL status=complete scope={scope} benchmark=bfcl_v4 scores={report}")


if __name__ == "__main__":
    main()
