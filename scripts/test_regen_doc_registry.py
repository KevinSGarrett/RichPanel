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


class MainGenerationTests(unittest.TestCase):
    def test_main_generates_registry_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            docs_root = root / "docs"
            docs_root.mkdir()
            (docs_root / "INDEX.md").write_text("- [A](A.md)\n", encoding="utf-8")
            (docs_root / "A.md").write_text("# A\n", encoding="utf-8")

            subprocess.run(
                ["git", "init"],
                cwd=str(root),
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            subprocess.run(
                ["git", "add", "docs/INDEX.md", "docs/A.md"],
                cwd=str(root),
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            orig_docs_root = registry.DOCS_ROOT
            orig_generated = registry.GENERATED_DIR
            orig_index = registry.INDEX_FILE
            try:
                registry.DOCS_ROOT = docs_root
                registry.GENERATED_DIR = docs_root / "_generated"
                registry.INDEX_FILE = docs_root / "INDEX.md"
                rc = registry.main()
                self.assertEqual(rc, 0)
                registry_path = docs_root / "REGISTRY.md"
                self.assertTrue(registry_path.exists())
                self.assertIn("A.md", registry_path.read_text(encoding="utf-8"))
                self.assertTrue(
                    (docs_root / "_generated" / "doc_registry.json").exists()
                )
            finally:
                registry.DOCS_ROOT = orig_docs_root
                registry.GENERATED_DIR = orig_generated
                registry.INDEX_FILE = orig_index


if __name__ == "__main__":
    unittest.main()
