import os
import subprocess
import tempfile
import time
from pathlib import Path
import unittest

import regen_doc_registry as registry


class DiscoverDocsTests(unittest.TestCase):
    def test_discover_docs_includes_root_and_nested(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            docs_root = root / "docs"
            docs_root.mkdir()

            (docs_root / "INDEX.md").write_text("# Index\n", encoding="utf-8")
            nested_dir = docs_root / "09_Deployment"
            nested_dir.mkdir()
            (nested_dir / "Order_Status.md").write_text(
                "# Order Status\n", encoding="utf-8"
            )

            subprocess.run(
                ["git", "init"],
                cwd=str(root),
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            subprocess.run(
                ["git", "add", "docs/INDEX.md", "docs/09_Deployment/Order_Status.md"],
                cwd=str(root),
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            discovered = registry._discover_docs(docs_root)
            rels = [p.relative_to(docs_root).as_posix() for p in discovered]
            self.assertIn("INDEX.md", rels)
            self.assertIn("09_Deployment/Order_Status.md", rels)
            self.assertEqual(rels, sorted(rels))


class WriteIfChangedTests(unittest.TestCase):
    def test_write_if_changed_skips_noop_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "test.txt"
            registry.write_if_changed(path, "hello\n")
            first_mtime = path.stat().st_mtime_ns
            time.sleep(0.02)
            registry.write_if_changed(path, "hello\n")
            second_mtime = path.stat().st_mtime_ns
            self.assertEqual(first_mtime, second_mtime)

    def test_write_if_changed_writes_on_change(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "test.txt"
            registry.write_if_changed(path, "hello\n")
            registry.write_if_changed(path, "hello world\n")
            self.assertEqual(path.read_text(encoding="utf-8"), "hello world\n")


if __name__ == "__main__":
    unittest.main()
