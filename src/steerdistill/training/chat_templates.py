"""Normalize tool arguments without changing the recorded trajectory."""
import copy
import json


def normalize_tool_arguments(messages):
    normalized = copy.deepcopy(messages)
    for message_index, message in enumerate(normalized):
        if not isinstance(message, dict):
            continue
        for call_index, call in enumerate(message.get("tool_calls") or []):
            if not isinstance(call, dict):
                continue
            function = call.get("function", call)
            if not isinstance(function, dict):
                continue
            arguments = function.get("arguments")
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except json.JSONDecodeError as error:
                    raise ValueError(f"Invalid JSON in chat tool-call arguments at message={message_index}, call={call_index}") from error
            if arguments is None:
                arguments = {}
            if not isinstance(arguments, dict):
                raise ValueError(f"Chat tool-call arguments must decode to an object at message={message_index}, call={call_index}")
            function["arguments"] = arguments
    return normalized
