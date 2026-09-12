#!/usr/bin/env python3
"""Three bounded inventory-policy controls; real temporary Git only, no freeze/build/runner execution."""

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

import freeze_app29_integrated_driver_v3 as inventory


class BackendIdentityControls(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="app29-v3-identity-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.branch = "remediation/app-29-backend-complaints"
        self.backend = self.repository("kira-backend", self.branch)
        self.git(self.backend, "branch", inventory.INTEGRATION_BRANCH)
        self.expected = {"kira-backend": {"branch": self.branch}}

    def git(self, repo, *args):
        env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
        env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
        command = ["git", "-c", "core.hooksPath=" + os.devnull, "-c", "commit.gpgsign=false",
                   "-c", "user.name=Inventory control", "-c", "user.email=inventory@example.invalid", *args]
        return subprocess.run(command, cwd=repo, env=env, check=True, timeout=10,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout

    def repository(self, name, branch):
        repo = self.root / name
        repo.mkdir()
        self.git(repo, "init", "--quiet", "--template=", "--initial-branch=" + branch)
        self.git(repo, "commit", "--quiet", "--allow-empty", "-m", "isolated initial state")
        return repo

    def states(self, frozen=None):
        return inventory._repository_states(self.root, self.expected, inventory._git, frozen=frozen)

    def test_backend_head_drift_is_rejected_against_frozen_identity(self):
        frozen = self.states()
        self.git(self.backend, "commit", "--quiet", "--allow-empty", "-m", "isolated backend advancement")
        with self.assertRaisesRegex(inventory.InventoryError, "Frozen Backend batch identity changed"):
            self.states(frozen)

    def test_unrelated_admin_advancement_does_not_change_backend_batch(self):
        admin = self.repository("kira-admin", "independent-admin-work")
        frozen = self.states()
        self.git(admin, "commit", "--quiet", "--allow-empty", "-m", "isolated unrelated advancement")
        self.git(admin, "branch", inventory.INTEGRATION_BRANCH)
        self.git(admin, "checkout", "--quiet", "-b", "independent-next-issue")
        (admin / "unrelated.txt").write_text("unrelated staged work\n")
        self.git(admin, "add", "unrelated.txt")
        self.assertEqual(self.states(frozen), frozen)
        self.assertEqual(set(frozen["repositories"]), {"kira-backend"})


class SeedPreservationControl(unittest.TestCase):
    def test_every_actual_348_development07_seed_path_is_mandatory(self):
        root = Path(__file__).absolute().parents[2]
        raw = (root / inventory.SEED_MANIFEST).read_bytes()
        self.assertEqual(inventory.sha256(raw), inventory.SEED_SHA256)
        seeds = json.loads(raw)["source_hashes"]
        self.assertEqual(len(seeds), 348)
        self.assertEqual(inventory._seed_preserved_count(seeds, dict(seeds)), 348)
        reduced = dict(seeds)
        reduced.pop(next(iter(reduced)))
        with self.assertRaisesRegex(inventory.InventoryError, "no seed-removal waiver"):
            inventory._seed_preserved_count(seeds, reduced)


if __name__ == "__main__":
    unittest.main(verbosity=2)
