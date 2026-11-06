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


def compare_alignment_state(candidate_root, reference_root, turn, reference_turn,
                            *, candidate_terminal=False, reference_terminal=False):
    """Compare state transitions for localization, never returned information."""
    policy = load_policy(candidate_root)
    if policy != load_policy(reference_root):
        raise ValueError("Candidate and reference use different task-state policies")
    def state(root, index):
        return snapshot_state(Path(root) / f"turn_{index:04d}", policy.get("ignored_columns"))
    before = state(candidate_root, turn)
    expected_before = state(reference_root, reference_turn)
    # Terminal prose executes no environment action and has no next snapshot.
    after = before if candidate_terminal else state(candidate_root, turn + 1)
    expected_after = expected_before if reference_terminal else state(reference_root, reference_turn + 1)
    return before == expected_before and after == expected_after


def unchanged_state(snapshot_root, turn):
    """State-preserving turns can be aligned without inspecting observations."""
    root = Path(snapshot_root)
    ignored = load_policy(root).get("ignored_columns")
    return snapshot_state(root / f"turn_{turn:04d}", ignored) == snapshot_state(root / f"turn_{turn + 1:04d}", ignored)


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False).encode()).hexdigest()


def _boundary_messages(messages, turn):
    """Freeze only the prefix available before the first continuation request."""
    seen = -1
    boundary = []
    for message in messages:
        if message.get("role") == "assistant":
            seen += 1
            if seen > turn:
                break
        boundary.append(message)
    if seen < turn:
        raise ValueError("Local gate target turn is missing")
    return boundary


def _snapshot_evidence(root, turn):
    evidence = []
    for index in (turn, turn + 1):
        directory = Path(root) / f"turn_{index:04d}"
        # Validate the actual database, not merely a claimed checksum.
        snapshot_state(directory)
        manifest_bytes = (directory / "manifest.json").read_bytes()
        manifest = json.loads(manifest_bytes)
        evidence.append({
            "snapshot_dir": str(directory.resolve()),
            "database": str((directory / manifest["db"]).resolve()),
            "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
            "db_sha256": manifest["db_sha256"],
        })
    return {"snapshots": evidence, "policy": load_policy(root)}


def gate_binding(spec, snapshot_root, messages, output_dir, reference):
    """Content and identity binding shared by the adapter and offline validator."""
    turn, reference_turn = spec["assistant_turn"], spec["reference_turn"]
    if type(turn) is not int or type(reference_turn) is not int or min(turn, reference_turn) < 0:
        raise ValueError("Invalid local gate turn")
    if (not spec.get("task_key") or not spec.get("skill_id")
            or type(spec.get("skill_version")) is not int or spec["skill_version"] < 1):
        raise ValueError("Local gate requires task and skill-version identity")
    reference_dir = Path(spec["reference_run"]).resolve()
    candidate_dir = Path(output_dir).resolve()
    if Path(snapshot_root).resolve() != candidate_dir / "snapshots":
        raise ValueError("Candidate snapshots must belong to the candidate run")
    if Path(reference.get("snapshot_root", "")).resolve() != reference_dir / "snapshots":
        raise ValueError("Reference snapshots must belong to the reference run")
    if f"{reference.get('scenario')}:{reference.get('task_id')}" != spec["task_key"]:
        raise ValueError("Reference task does not match local gate")
    return {
        "format": 2,
        "candidate_run": str(candidate_dir),
        "reference_run": str(reference_dir),
        "task_key": spec["task_key"], "skill_id": spec["skill_id"],
        "skill_version": spec["skill_version"],
        "assistant_turn": turn, "reference_turn": reference_turn,
        "candidate_boundary_sha256": _digest(_boundary_messages(messages, turn)),
        "reference_boundary_sha256": _digest(_boundary_messages(reference["messages"], reference_turn)),
        "candidate_state": _snapshot_evidence(snapshot_root, turn),
        "reference_state": _snapshot_evidence(reference_dir / "snapshots", reference_turn),
    }


def validate_gate_receipt(receipt, spec, snapshot_root, messages, output_dir,
                          reference, accepted, reason):
    binding = gate_binding(spec, snapshot_root, messages, output_dir, reference)
    if (any(receipt.get(key) != value for key, value in binding.items())
            or receipt.get("checked_before_continuation") is not True
            or receipt.get("accepted") is not accepted
            or receipt.get("reason") != reason):
        raise ValueError("Local transition gate evidence mismatch")


def check_boundary(snapshot_root, iteration, messages, output_dir):
    spec = json.loads(Path(os.environ["STEER_LOCAL_GATE"]).read_text())
    turn = int(spec["assistant_turn"])
    if iteration < turn + 1:
        return True
    reference_dir = Path(spec["reference_run"])
    reference = json.loads((reference_dir / "trajectory.json").read_text())
    reference_turn = int(spec["reference_turn"])
    reference_action = [message for message in reference["messages"]
                        if message.get("role") == "assistant"][reference_turn]
    candidate_actions = [message for message in messages if message.get("role") == "assistant"]
    receipt_path = Path(output_dir, "local_gate.json")
    if iteration == turn + 1 and len(candidate_actions) != turn + 1:
        raise ValueError("Local gate was invoked after continuation")
    if not reference_action.get("tool_calls"):
        accepted, reason = False, "expected_terminal_response"
    elif len(candidate_actions) <= turn or not candidate_actions[turn].get("tool_calls"):
        accepted, reason = False, "candidate_not_action"
    else:
        accepted, reason = compare_transition(snapshot_root, reference_dir / "snapshots", turn,
            reference_turn, messages, reference["messages"])
    binding = gate_binding(spec, snapshot_root, messages, output_dir, reference)
    if iteration > turn + 1:
        # Never manufacture a precontinuation receipt after missing the boundary.
        receipt = json.loads(receipt_path.read_text())
        validate_gate_receipt(receipt, spec, snapshot_root, messages, output_dir,
                              reference, accepted, reason)
        return accepted
    receipt = dict(binding, accepted=accepted, reason=reason, checked_before_continuation=True)
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    return accepted
