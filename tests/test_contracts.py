import unittest

from agentdev.contracts import State, Task, scopes_overlap, transition, valid_path


class ContractTests(unittest.TestCase):
    def make_task(self, **kwargs):
        data = {
            "issue_number": 8,
            "objective": "A bounded implementation",
            "acceptance": ["test passes"],
            "dependencies": [],
            "base_sha": "a" * 40,
            "branch": "agent/8-sample",
            "write_paths": ["src/module"],
            "mode": "AFK",
        }
        data.update(kwargs)
        return Task.from_dict(data)

    def test_valid_assignment(self):
        self.assertEqual(self.make_task().issue_number, 8)

    def test_reject_missing_mode(self):
        with self.assertRaisesRegex(ValueError, "mode"):
            Task.from_dict({
                "issue_number": 8, "objective": "slice", "acceptance": ["test"],
                "dependencies": [], "base_sha": "a" * 40,
                "branch": "agent/8-example", "write_paths": ["src"]})

    def test_reject_unknown_mode(self):
        with self.assertRaisesRegex(ValueError, "mode"):
            self.make_task(mode="AUTO")

    def test_human_requires_gate_and_afk_rejects_gate(self):
        with self.assertRaisesRegex(ValueError, "human_gate"):
            self.make_task(mode="HUMAN")
        with self.assertRaisesRegex(ValueError, "human_gate"):
            self.make_task(mode="AFK", human_gate="Approval needed")
        self.assertEqual(self.make_task(mode="HUMAN", human_gate="Target host approval").mode, "HUMAN")

    def test_awaiting_human_transition(self):
        self.assertEqual(transition(State.READY, State.AWAITING_HUMAN), State.AWAITING_HUMAN)
        self.assertEqual(transition(State.AWAITING_HUMAN, State.READY), State.READY)

    def test_reject_missing_acceptance(self):
        with self.assertRaises(ValueError):
            self.make_task(acceptance=[])

    def test_reject_wrong_branch(self):
        with self.assertRaises(ValueError):
            self.make_task(branch="development")

    def test_reject_unpinned_base(self):
        with self.assertRaises(ValueError):
            self.make_task(base_sha="latest")

    def test_reject_self_dependency(self):
        with self.assertRaises(ValueError):
            self.make_task(dependencies=[8])

    def test_write_scope_safe(self):
        for path in ("../secret", "src/../secret", "/absolute", ".", "src/*"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                valid_path(path)

    def test_scopes_overlap_conservatively(self):
        self.assertTrue(scopes_overlap(["src"], ["src/a.py"]))
        self.assertTrue(scopes_overlap(["*"], ["docs"]))
        self.assertFalse(scopes_overlap(["src/a"], ["src/b"]))

    def test_done_is_terminal(self):
        with self.assertRaises(ValueError):
            transition(State.DONE, State.READY)

    def test_review_rejection_reenters_implementation(self):
        self.assertEqual(transition(State.REVIEWING, State.CHANGES_REQUESTED), State.CHANGES_REQUESTED)
        self.assertEqual(transition(State.CHANGES_REQUESTED, State.IMPLEMENTING), State.IMPLEMENTING)