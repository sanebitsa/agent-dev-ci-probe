import json
import unittest
from agentdev.review import approved_review

SHA = "b" * 40
APP = 101


def review(**changes):
    result = {"name": "agent-independent-review", "head_sha": SHA,
              "app": {"id": APP}, "status": "completed", "conclusion": "success",
              "external_id": json.dumps({"reviewed_sha": SHA, "reviewer_identity": "reviewer-b",
                                         "review_run_id": "job-92", "verdict": "APPROVED"})}
    result.update(changes)
    return result


class ReviewGateTests(unittest.TestCase):
    def allowed(self, check):
        return approved_review([check], head_sha=SHA, trusted_app_id=APP, author_login="implementer-a")

    def test_trusted_independent_approved_current_sha(self):
        self.assertTrue(self.allowed(review()))

    def test_reject_forged_source(self):
        self.assertFalse(self.allowed(review(app={"id": 202})))

    def test_reject_outdated_review(self):
        self.assertFalse(self.allowed(review(head_sha="a" * 40)))

    def test_reject_failed_or_pending_check(self):
        self.assertFalse(self.allowed(review(conclusion="failure")))
        self.assertFalse(self.allowed(review(status="queued")))

    def test_reject_author_reviewing_own_work(self):
        self.assertFalse(self.allowed(review(external_id=json.dumps({"reviewed_sha": SHA,
                             "reviewer_identity": "implementer-a", "review_run_id": "job-1",
                             "verdict": "APPROVED"}))))

    def test_reject_outdated_attestation_metadata(self):
        self.assertFalse(self.allowed(review(external_id=json.dumps({"reviewed_sha": "a" * 40,
                             "reviewer_identity": "reviewer-b", "review_run_id": "job-2",
                             "verdict": "APPROVED"}))))

    def test_reject_unconfigured_trusted_app(self):
        self.assertFalse(approved_review([review()], head_sha=SHA, trusted_app_id=0,
                                         author_login="implementer-a"))

    def test_reject_reviewer_changes_requested(self):
        self.assertFalse(self.allowed(review(external_id=json.dumps({"reviewed_sha": SHA,
                             "reviewer_identity": "reviewer-b", "review_run_id": "job-3",
                             "verdict": "CHANGES_REQUESTED"}))))
