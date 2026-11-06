import json
import tempfile
import threading
import unittest
from pathlib import Path

from agentdev.contracts import Task
from agentdev.scheduler import claim_ready


def task(n, path, deps=(), risk="standard", mode="AFK", human_gate=""):
    return Task.from_dict({"issue_number": n, "objective": f"task {n}", "acceptance": ["passing test"],
                           "dependencies": list(deps), "base_sha": "a" * 40,
                           "branch": f"agent/{n}-test", "write_paths": [path], "risk": risk,
                           "mode": mode, "human_gate": human_gate})


class SchedulerTests(unittest.TestCase):
    def test_no_duplicate_ownership_under_concurrency(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "state.json"
            results = []
            threads = [threading.Thread(target=lambda: results.extend(claim_ready([task(1, "src/a")], state)))
                       for _ in range(8)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            self.assertEqual(len(results), 1)
            self.assertEqual(len(json.loads(state.read_text())["claimed"]), 1)

    def test_nonoverlapping_tasks_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = claim_ready([task(1, "src"), task(2, "src/a"), task(3, "docs")],
                                 Path(tmp) / "state.json", max_agents=3)
            self.assertEqual([item["issue_number"] for item in result], [1, 3])

    def test_wait_for_dependency(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "state.json"
            self.assertEqual(claim_ready([task(2, "docs", deps=[1])], state), [])
            state.write_text(json.dumps({"claimed": {}, "done": [1]}))
            self.assertEqual(len(claim_ready([task(2, "docs", deps=[1])], state)), 1)

    def test_restricted_task_not_dispatched(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(claim_ready([task(1, "src", risk="restricted")], Path(tmp) / "state.json"), [])

    def test_human_issue_never_dispatched(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "state.json"
            tasks = [task(1, "docs/human", mode="HUMAN", human_gate="Owner approves host"),
                     task(2, "src/example", deps=(1,))]
            self.assertEqual(claim_ready(tasks, state), [])
            state.write_text(json.dumps({"claimed": {}, "done": [1]}))
            result = claim_ready(tasks, state)
            self.assertEqual([r["issue_number"] for r in result], [2])
            self.assertEqual(result[0]["mode"], "AFK")

    def test_continue_independent_afk_work_while_human_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            tasks = [task(1, "docs/host", mode="HUMAN", human_gate="Host access"),
                     task(2, "src/after-host", deps=(1,)), task(3, "src/independent")]
            result = claim_ready(tasks, Path(tmp) / "state.json", max_agents=3)
            self.assertEqual([r["issue_number"] for r in result], [3])

    def test_reject_dependency_cycles(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "cyclic"):
                claim_ready([task(1, "src/a", deps=(2,)), task(2, "src/b", deps=(1,))],
                            Path(tmp) / "state.json")

    def test_bounded_concurrency(self):
        with tempfile.TemporaryDirectory() as tmp:
            tasks = [task(i, f"scope/{i}") for i in range(1, 6)]
            self.assertEqual(len(claim_ready(tasks, Path(tmp) / "state.json", max_agents=2)), 2)
            with self.assertRaises(ValueError):
                claim_ready(tasks, Path(tmp) / "state.json", max_agents=4)