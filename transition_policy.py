"""Derive narrow, task-specific exclusions for generated clock metadata.

Unknown constructs keep strict state comparison. Business dates, logs, primary
keys and user-supplied values are never excluded by name alone.
"""
import ast
import hashlib
import re


def _clock(value):
    if isinstance(value, ast.Call):
        value = value.func
    return (isinstance(value, ast.Attribute) and value.attr == "utcnow"
            and isinstance(value.value, ast.Name) and value.value.id == "datetime")


def compile_policy(source, verifier, task_key):
    result = {"format": 1, "task_key": task_key, "ignored_columns": {},
              "environment_sha256": hashlib.sha256(source.encode()).hexdigest(),
              "verifier_sha256": hashlib.sha256(verifier.encode()).hexdigest()}
    try:
        tree, check = ast.parse(source), ast.parse(verifier)
    except SyntaxError:
        return result
    sql = [node.value for node in ast.walk(check)
           if isinstance(node, ast.Constant) and isinstance(node.value, str)
           and re.search(r"\bSELECT\b", node.value, re.I)]
    if not sql or any(re.search(r"\bSELECT\s+\*|\b\w+\.\*", text, re.I) for text in sql):
        return result
    for node in ast.walk(check):
        if isinstance(node, (ast.JoinedStr, ast.BinOp)):
            text = ast.get_source_segment(verifier, node) or ""
            if re.search(r"\b(SELECT|PRAGMA)\b", text, re.I):
                return result
    parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
    response_models = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.keyword) and node.arg == "response_model":
            response_models.update(item.id for item in ast.walk(node.value) if isinstance(item, ast.Name))
    classes = {node.name: node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
    orm_models = {name for name, definition in classes.items()
                  if any(isinstance(item, ast.Assign) and any(isinstance(t, ast.Name)
                         and t.id == "__tablename__" for t in item.targets) for item in definition.body)}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in {"getattr", "setattr", "eval", "exec"}:
                return result
            if (isinstance(node.func, ast.Name) and node.func.id in orm_models
                    and any(keyword.arg is None for keyword in node.keywords)):
                return result
    pending = list(response_models)
    while pending:
        definition = classes.get(pending.pop())
        if definition is None:
            continue
        for member in definition.body:
            if isinstance(member, ast.AnnAssign):
                for name in ast.walk(member.annotation):
                    if isinstance(name, ast.Name) and name.id in classes and name.id not in response_models:
                        response_models.add(name.id)
                        pending.append(name.id)

    def response_keyword(node):
        parent = parents.get(node)
        return (isinstance(parent, ast.Call) and isinstance(parent.func, ast.Name)
                and parent.func.id in response_models)
    assignments = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assignments.setdefault(target.id, []).append(node.value)

    def generated(value):
        if _clock(value):
            return True
        return (isinstance(value, ast.Name) and bool(assignments.get(value.id))
                and all(_clock(item) for item in assignments[value.id]))

    candidates = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        table = next((item.value.value for item in node.body if isinstance(item, ast.Assign)
                      and any(isinstance(t, ast.Name) and t.id == "__tablename__" for t in item.targets)
                      and isinstance(item.value, ast.Constant) and isinstance(item.value.value, str)), None)
        if table is None:
            continue
        for item in node.body:
            if not (isinstance(item, ast.Assign) and isinstance(item.value, ast.Call)
                    and isinstance(item.value.func, ast.Name) and item.value.func.id == "Column"):
                continue
            if not any(isinstance(arg, ast.Name) and arg.id == "DateTime" for arg in item.value.args):
                continue
            keywords = {kw.arg: kw.value for kw in item.value.keywords}
            if not _clock(keywords.get("default")) or "primary_key" in keywords:
                continue
            for target in item.targets:
                if isinstance(target, ast.Name):
                    candidates.append((table, target.id))

    for table, field in candidates:
        if re.search(r"\b" + re.escape(field) + r"\b", verifier, re.I):
            continue
        safe = True
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if re.search(r"\b" + re.escape(field) + r"\b", node.value):
                    safe = False  # Includes raw SQL, filter/sort names and dynamic access.
            if isinstance(node, ast.keyword) and node.arg == field:
                value = node.value
                serialized = (isinstance(value, ast.Attribute) and value.attr == field
                              and response_keyword(node))
                if not serialized and not generated(value):
                    safe = False
            if isinstance(node, ast.Attribute) and node.attr == field:
                parent = parents.get(node)
                if isinstance(node.ctx, ast.Store):
                    if not isinstance(parent, ast.Assign) or not generated(parent.value):
                        safe = False
                elif not (isinstance(parent, ast.keyword) and parent.arg == field and response_keyword(parent)):
                    safe = False  # Business comparisons, ordering and calculations stay exact.
        if safe:
            result["ignored_columns"].setdefault(table, []).append(field)
    result["ignored_columns"] = {table: sorted(set(fields))
                                  for table, fields in sorted(result["ignored_columns"].items())}
    return result
