#!/usr/bin/env python3
"""Standard-library tests for workflow.py."""

from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

import workflow


class WorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.state_path = self.root / "docs" / "bohrium" / "workflow-state.json"
        self.state_path.parent.mkdir(parents=True)
        self.assertEqual(
            self.run_cli(
                "init",
                "--state",
                str(self.state_path),
                "--project-name",
                "test-app",
                "--repository",
                str(self.root),
            ),
            0,
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_cli(self, *arguments: str) -> int:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
            io.StringIO()
        ):
            return workflow.main(list(arguments))

    def read_state(self) -> dict:
        return json.loads(self.state_path.read_text(encoding="utf-8"))

    def write_state(self, state: dict) -> None:
        self.state_path.write_text(
            json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    def transition(
        self,
        stage: str,
        target: str,
        *extra: str,
        actor: str = "test-agent",
    ) -> int:
        revision = self.read_state()["state_revision"]
        return self.run_cli(
            "transition",
            "--state",
            str(self.state_path),
            "--stage",
            stage,
            "--to",
            target,
            "--actor",
            actor,
            "--expect-revision",
            str(revision),
            *extra,
        )

    def pass_stage(self, stage: str) -> None:
        evidence = self.root / f"{stage}-evidence.txt"
        evidence.write_text("passed\n", encoding="utf-8")
        self.assertEqual(self.transition(stage, "ready"), 0)
        self.assertEqual(self.transition(stage, "in_progress"), 0)
        self.assertEqual(
            self.transition(stage, "review", "--evidence", evidence.name), 0
        )
        self.assertEqual(
            self.transition(stage, "passed", actor="independent-reviewer"), 0
        )

    def test_init_refuses_overwrite(self) -> None:
        before = self.state_path.read_bytes()
        result = self.run_cli(
            "init",
            "--state",
            str(self.state_path),
            "--project-name",
            "replacement",
        )
        self.assertEqual(result, 3)
        self.assertEqual(self.state_path.read_bytes(), before)

    def test_status_and_check_accept_initial_state(self) -> None:
        self.assertTrue(
            (self.state_path.parent / "session-handoff.template.md").is_file()
        )
        self.assertTrue((self.state_path.parent / "handoffs").is_dir())
        self.assertTrue((self.state_path.parent / "evidence" / "local").is_dir())
        self.assertEqual(
            self.run_cli("status", "--state", str(self.state_path), "--json"), 0
        )
        self.assertEqual(
            self.run_cli("check", "--state", str(self.state_path), "--strict"), 0
        )

    def test_optimistic_revision_conflict_preserves_state(self) -> None:
        before = self.state_path.read_bytes()
        result = self.run_cli(
            "transition",
            "--state",
            str(self.state_path),
            "--stage",
            "S0",
            "--to",
            "ready",
            "--actor",
            "orchestrator",
            "--expect-revision",
            "99",
        )
        self.assertEqual(result, 3)
        self.assertEqual(self.state_path.read_bytes(), before)
        self.assertFalse(Path(f"{self.state_path}.lock").exists())

    def test_illegal_transition_is_rejected(self) -> None:
        self.assertEqual(self.transition("S0", "passed"), 1)
        self.assertEqual(self.read_state()["stages"]["S0"]["status"], "pending")

    def test_dependency_must_pass_before_downstream_stage(self) -> None:
        self.assertEqual(self.transition("S1", "ready"), 1)

    def test_passed_stage_requires_evidence(self) -> None:
        self.assertEqual(self.transition("S0", "ready"), 0)
        self.assertEqual(self.transition("S0", "in_progress"), 0)
        self.assertEqual(self.transition("S0", "review"), 0)
        self.assertEqual(self.transition("S0", "passed"), 1)
        self.assertEqual(self.read_state()["stages"]["S0"]["status"], "review")

    def test_passed_stage_with_evidence_advances_current_stage(self) -> None:
        self.pass_stage("S0")
        state = self.read_state()
        self.assertEqual(state["stages"]["S0"]["status"], "passed")
        self.assertEqual(state["current_stage"], "S1")
        self.assertEqual(state["state_revision"], 4)

    def test_check_rejects_multiple_active_stages(self) -> None:
        state = self.read_state()
        state["stages"]["S0"]["status"] = "in_progress"
        state["stages"]["S1"]["status"] = "review"
        self.write_state(state)
        self.assertEqual(self.run_cli("check", "--state", str(self.state_path)), 1)

    def test_check_allows_parallel_worker_assignment_metadata(self) -> None:
        state = self.read_state()
        state["active_assignments"] = [
            {
                "assignment_id": "A-1",
                "stage": "S0",
                "worker": "discovery-worker",
                "write_paths": ["docs/bohrium/app-brief.md"],
            },
            {
                "assignment_id": "A-2",
                "stage": "S0",
                "worker": "runtime-inventory-worker",
                "write_paths": ["docs/bohrium/runtime-inventory.md"],
            },
        ]
        state["locks"] = {
            "docs/bohrium/app-brief.md": "A-1",
            "docs/bohrium/runtime-inventory.md": "A-2",
        }
        self.write_state(state)
        self.assertEqual(self.run_cli("check", "--state", str(self.state_path)), 0)

    def test_downstream_invalidation_stales_evidence_and_claims(self) -> None:
        for index in range(5):
            self.pass_stage(f"S{index}")
        state = self.read_state()
        self.assertTrue(state["claims"]["local_ready"])
        evidence_count = len(state["stages"]["S4"]["evidence"])
        self.assertGreater(evidence_count, 0)

        result = self.transition(
            "S3",
            "pending",
            "--invalidate-downstream",
            "--reason",
            "schema identity changed",
            actor="orchestrator",
        )
        self.assertEqual(result, 0)
        state = self.read_state()
        self.assertEqual(state["current_stage"], "S3")
        self.assertEqual(state["stages"]["S3"]["status"], "pending")
        self.assertEqual(state["stages"]["S4"]["status"], "pending")
        self.assertEqual(state["stages"]["S4"]["evidence"], [])
        self.assertEqual(len(state["stages"]["S4"]["stale_evidence"]), evidence_count)
        self.assertFalse(state["claims"]["local_ready"])

    def test_secret_field_is_rejected_without_value_in_output(self) -> None:
        state = self.read_state()
        state["password"] = "do-not-echo-this-value"
        self.write_state(state)
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            result = workflow.main(["status", "--state", str(self.state_path)])
        self.assertEqual(result, 4)
        self.assertNotIn("do-not-echo-this-value", stdout.getvalue())
        self.assertNotIn("do-not-echo-this-value", stderr.getvalue())

    def test_evidence_outside_repository_is_rejected(self) -> None:
        outside = Path(self.temporary.name).parent / "outside-evidence.txt"
        outside.write_text("not allowed\n", encoding="utf-8")
        self.addCleanup(lambda: outside.unlink(missing_ok=True))
        self.assertEqual(self.transition("S0", "ready"), 0)
        self.assertEqual(self.transition("S0", "in_progress"), 0)
        self.assertEqual(
            self.transition("S0", "review", "--evidence", str(outside)), 4
        )

    def test_lock_conflict_is_rejected(self) -> None:
        lock = Path(f"{self.state_path}.lock")
        lock.write_text("existing\n", encoding="utf-8")
        self.addCleanup(lambda: lock.unlink(missing_ok=True))
        self.assertEqual(self.transition("S0", "ready"), 3)

    def test_begin_and_finish_single_mutation(self) -> None:
        self.pass_stage("S0")
        self.assertEqual(self.transition("S1", "ready"), 0)
        plan = self.root / "mutation.json"
        plan.write_text(
            json.dumps(
                {
                    "mutation_id": "MUT-1",
                    "stage": "S1",
                    "kind": "test_mutation",
                    "exact_target": "test target",
                    "expected_effect": "one object created",
                    "expected_cost": "none",
                    "rollback_or_recovery": "read back by MUT-1",
                    "authorization_ref": "AUTH-1",
                }
            ),
            encoding="utf-8",
        )
        self.assertEqual(
            self.transition(
                "S1", "in_progress", "--begin-mutation", plan.name
            ),
            0,
        )
        self.assertIsNotNone(self.read_state()["active_mutation"])
        readback = self.root / "readback.txt"
        readback.write_text("ok\n", encoding="utf-8")
        self.assertEqual(
            self.transition(
                "S1",
                "review",
                "--finish-mutation",
                "MUT-1",
                "--evidence",
                readback.name,
            ),
            0,
        )
        state = self.read_state()
        self.assertIsNone(state["active_mutation"])
        self.assertEqual(len(state["mutation_history"]), 1)


if __name__ == "__main__":
    unittest.main()
