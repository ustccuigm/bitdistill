"""Conservative relational-state verification at a tool intervention boundary."""
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import sqlite3


def snapshot_state(directory, ignored_columns=None):
    directory = Path(directory)
    manifest = json.loads((directory / "manifest.json").read_text())
    database = directory / manifest["db"]
    if hashlib.sha256(database.read_bytes()).hexdigest() != manifest["db_sha256"]:
        raise ValueError("Transition snapshot checksum mismatch")
    result = {}
    connection = sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        for (name,) in connection.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
            quoted = '"' + name.replace('"', '""') + '"'
            columns = tuple(connection.execute(f"PRAGMA table_info({quoted})"))
            ignored = set((ignored_columns or {}).get(name, []))
            if ignored - {column[1] for column in columns}:
                raise ValueError("Transition policy references an absent column")
            if any(column[1] in ignored and column[5] for column in columns):
                raise ValueError("Transition policies cannot ignore primary keys")
            keep = [index for index, column in enumerate(columns) if column[1] not in ignored]
            rows = Counter(tuple(row[index] for index in keep)
                           for row in connection.execute(f"SELECT * FROM {quoted}"))
            result[name] = (tuple(columns[index] for index in keep), rows)
    finally:
        connection.close()
    return result


def load_policy(snapshot_root):
    path = Path(snapshot_root).parent / "transition_policy.json"
    if not path.is_file():
        return {}
    policy = json.loads(path.read_text())
    if policy.get("format") != 1:
        raise ValueError("Unsupported transition policy format")
    return policy


def observations(messages, turn):
    seen = -1
    result = []
    for message in messages:
        if message.get("role") == "assistant":
            seen += 1
            if seen > turn:
                break
        elif seen == turn and message.get("role") in {"tool", "user"}:
            content = message.get("content", "")
            try:
                content = json.loads(content)
            except (ValueError, TypeError):
                content = " ".join(str(content).split())
            result.append(content)
    return result


def error_observation(evidence):
    for value in evidence:
        if isinstance(value, dict):
            if value.get("error") or value.get("success") is False:
                return True
            status = value.get("status_code")
            if isinstance(status, int) and status >= 400:
                return True
        text = json.dumps(value).lower()
        if any(marker in text for marker in ("error:", "traceback", "internal server error")):
            return True
    return False


def compare_transition(candidate_root, reference_root, turn, reference_turn, candidate_messages, reference_messages):
    policy = load_policy(candidate_root)
    if policy != load_policy(reference_root):
        raise ValueError("Candidate and reference use different task-state policies")
    def state(root, index):
        return snapshot_state(Path(root) / f"turn_{index:04d}", policy.get("ignored_columns"))
    before = state(candidate_root, turn)
    after = state(candidate_root, turn + 1)
    expected_before = state(reference_root, reference_turn)
    expected_after = state(reference_root, reference_turn + 1)
    actual = observations(candidate_messages, turn)
    expected = observations(reference_messages, reference_turn)
    if error_observation(actual):
        return False, "environment_error"
    # Only generated clock metadata proved unused by this task's verifier and
    # environment logic is projected out. All other state and side effects stay.
    if before != expected_before:
        return False, "precondition_state_mismatch"
    if after != expected_after:
        return False, "postcondition_state_mismatch"
    if expected_before != expected_after:
        return True, "verified_state_transition"
    if not actual or not expected:
        return False, "read_evidence_missing"
    if actual != expected:
        return False, "read_result_mismatch"
    return True, "verified_read_transition"


def unchanged_read(snapshot_root, turn, messages):
    """Only observed, non-error reads may be skipped during alignment."""
    root = Path(snapshot_root)
    evidence = observations(messages, turn)
    if not evidence or error_observation(evidence):
        return False
    ignored = load_policy(root).get("ignored_columns")
    return snapshot_state(root / f"turn_{turn:04d}", ignored) == snapshot_state(root / f"turn_{turn + 1:04d}", ignored)


def check_boundary(snapshot_root, iteration, messages, output_dir):
    spec = json.loads(Path(os.environ["STEER_LOCAL_GATE"]).read_text())
    turn = int(spec["assistant_turn"])
    if iteration != turn + 1:
        return True
    reference_dir = Path(spec["reference_run"])
    reference = json.loads((reference_dir / "trajectory.json").read_text())
    reference_turn = int(spec["reference_turn"])
    reference_action = [message for message in reference["messages"]
                        if message.get("role") == "assistant"][reference_turn]
    if not reference_action.get("tool_calls"):
        accepted, reason = False, "expected_terminal_response"
    else:
        accepted, reason = compare_transition(snapshot_root, reference_dir / "snapshots", turn,
            reference_turn, messages, reference["messages"])
    receipt = dict(spec, accepted=accepted, reason=reason, checked_before_continuation=True)
    Path(output_dir, "local_gate.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return accepted
