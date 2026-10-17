import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from transition_policy import compile_policy
from transition_verifier import compare_transition


ENVIRONMENT = '''
from datetime import datetime
class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    status = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    scheduled_at = Column(DateTime)
class Item(BaseModel):
    created_at: datetime
class Response(BaseModel):
    item: Item
@app.get("/orders", response_model=Response)
def read(order):
    return Response(item=Item(created_at=order.created_at))
def create():
    now = datetime.utcnow()
    return Order(created_at=now)
'''
VERIFIER = '''
def verify(db):
    return db.execute("SELECT id, status, scheduled_at FROM orders WHERE status = 'confirmed'").fetchall()
'''


class TransitionPolicyTest(unittest.TestCase):
    def test_only_generated_unused_clock_metadata_is_excluded(self):
        policy = compile_policy(ENVIRONMENT, VERIFIER, "s:1")
        self.assertEqual(policy["ignored_columns"], {"orders": ["created_at"]})

    def test_verifier_relevant_time_is_preserved(self):
        verifier = VERIFIER.replace("id, status, scheduled_at", "id, status, created_at, scheduled_at")
        self.assertEqual(compile_policy(ENVIRONMENT, verifier, "s:1")["ignored_columns"], {})

    def test_business_logic_and_user_input_are_preserved(self):
        for suffix in ("\ndef sort(order): return order.created_at\n",
                       "\ndef insert(request): return Order(created_at=request.created_at)\n",
                       "\ndef update(order, request): order.created_at = request.value\n",
                       "\ndef insert(request): return Order(**request.dict())\n",
                       "\ndef inspect(order, field): return getattr(order, field)\n"):
            with self.subTest(suffix=suffix):
                self.assertEqual(compile_policy(ENVIRONMENT + suffix, VERIFIER, "s:1")["ignored_columns"], {})

    def test_dynamic_or_wildcard_verifier_does_not_relax_comparison(self):
        for verifier in ('db.execute("SELECT * FROM orders")',
                         'db.execute(f"SELECT {columns} FROM orders")',
                         'db.execute("SELECT " + columns + " FROM orders")'):
            self.assertEqual(compile_policy(ENVIRONMENT, verifier, "s:1")["ignored_columns"], {})

    def test_timestamp_difference_passes_but_wrong_business_state_fails(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            policy = compile_policy(ENVIRONMENT, VERIFIER, "s:1")
            for name, timestamp, status in (("reference", "2026-01-01", "confirmed"),
                                             ("candidate", "2026-01-02", "confirmed"),
                                             ("wrong", "2026-01-03", "cancelled"),
                                             ("wrong_date", "2026-01-04", "confirmed"),
                                             ("extra_log", "2026-01-05", "confirmed")):
                for turn in (0, 1):
                    directory = root / name / "snapshots" / f"turn_{turn:04d}"
                    directory.mkdir(parents=True)
                    database = directory / "state.db"
                    with sqlite3.connect(database) as connection:
                        connection.execute("CREATE TABLE orders(id INTEGER PRIMARY KEY, status TEXT, created_at TEXT, scheduled_at TEXT)")
                        connection.execute("INSERT INTO orders VALUES(1, ?, ?, ?)",
                            (status if turn else "pending", timestamp,
                             "2026-02-02" if name == "wrong_date" and turn else "2026-02-01"))
                        connection.execute("CREATE TABLE audit_log(event TEXT)")
                        if name == "extra_log" and turn:
                            connection.execute("INSERT INTO audit_log VALUES('unapproved change')")
                    (directory / "manifest.json").write_text(json.dumps({"db": "state.db",
                        "db_sha256": hashlib.sha256(database.read_bytes()).hexdigest()}))
                (root / name / "transition_policy.json").write_text(json.dumps(policy))
            messages = [{"role": "assistant", "content": "confirm"}, {"role": "tool", "content": "ok"}]
            for name, expected in (("candidate", True), ("wrong", False), ("wrong_date", False), ("extra_log", False)):
                accepted, _ = compare_transition(root / name / "snapshots", root / "reference/snapshots", 0, 0, messages, messages)
                self.assertEqual(accepted, expected)
            other = dict(policy, task_key="s:2")
            (root / "candidate/transition_policy.json").write_text(json.dumps(other))
            with self.assertRaisesRegex(ValueError, "different task-state policies"):
                compare_transition(root / "candidate/snapshots", root / "reference/snapshots", 0, 0, messages, messages)


if __name__ == "__main__":
    unittest.main()
