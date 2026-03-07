#!/usr/bin/env python3
"""
Unit tests for GitHub integration scripts

Tests:
  - generate-per-service-specs.py
  - check-file-size-cods.py
  - create-all-service-projects.py
"""

import sys
import unittest
from pathlib import Path

# Add scripts to path
SCRIPT_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPT_DIR / "utilities"))
sys.path.insert(0, str(SCRIPT_DIR / "core"))


class TestScriptImports(unittest.TestCase):
    """Test that scripts can be imported without errors."""

    def test_import_generate_per_service_specs(self):
        """Test importing generate-per-service-specs.py"""
        # Import should not raise
        # Note: Can't use hyphen in module name, so we test file existence
        script_path = SCRIPT_DIR / "utilities" / "generate-per-service-specs.py"
        self.assertTrue(script_path.exists(), f"Script not found: {script_path}")
        self.assertTrue(script_path.is_file(), f"Not a file: {script_path}")

        # Check it's executable
        import stat

        st = script_path.stat()
        is_executable = bool(st.st_mode & stat.S_IXUSR)
        self.assertTrue(is_executable, f"Script not executable: {script_path}")

    def test_import_check_file_size_cods(self):
        """Test importing check-file-size-cods.py"""
        script_path = SCRIPT_DIR / "core" / "05-check-file-size-cods.py"
        self.assertTrue(script_path.exists(), f"Script not found: {script_path}")
        self.assertTrue(script_path.is_file(), f"Not a file: {script_path}")

        import stat

        st = script_path.stat()
        is_executable = bool(st.st_mode & stat.S_IXUSR)
        self.assertTrue(is_executable, f"Script not executable: {script_path}")

    def test_import_create_all_service_projects(self):
        """Test importing create-all-service-projects.py"""
        script_path = SCRIPT_DIR / "utilities" / "create-all-service-projects.py"
        self.assertTrue(script_path.exists(), f"Script not found: {script_path}")
        self.assertTrue(script_path.is_file(), f"Not a file: {script_path}")

        import stat

        st = script_path.stat()
        is_executable = bool(st.st_mode & stat.S_IXUSR)
        self.assertTrue(is_executable, f"Script not executable: {script_path}")


class TestScriptStructure(unittest.TestCase):
    """Test script structure and conventions."""

    def test_scripts_have_shebang(self):
        """Test that Python scripts have proper shebang."""
        scripts = [
            SCRIPT_DIR / "utilities" / "generate-per-service-specs.py",
            SCRIPT_DIR / "core" / "05-check-file-size-cods.py",
            SCRIPT_DIR / "utilities" / "create-all-service-projects.py",
        ]

        for script_path in scripts:
            with open(script_path, "r") as f:
                first_line = f.readline().strip()
                self.assertTrue(
                    first_line.startswith("#!/usr/bin/env python"), f"Script missing shebang: {script_path.name}"
                )

    def test_scripts_have_docstrings(self):
        """Test that Python scripts have module docstrings."""
        scripts = [
            SCRIPT_DIR / "utilities" / "generate-per-service-specs.py",
            SCRIPT_DIR / "core" / "05-check-file-size-cods.py",
            SCRIPT_DIR / "utilities" / "create-all-service-projects.py",
        ]

        for script_path in scripts:
            with open(script_path, "r") as f:
                content = f.read()
                # Check for triple-quoted docstring after shebang
                self.assertIn('"""', content, f"Script missing docstring: {script_path.name}")


class TestScriptConstants(unittest.TestCase):
    """Test script constants and configuration."""

    def test_check_file_size_has_extensions(self):
        """Test that check-file-size-cods.py defines extensions."""
        script_path = SCRIPT_DIR / "core" / "05-check-file-size-cods.py"
        with open(script_path, "r") as f:
            content = f.read()
            self.assertIn("EXTENSIONS", content)
            self.assertIn(".py", content)
            self.assertIn(".ts", content)

    def test_check_file_size_has_exclude_patterns(self):
        """Test that check-file-size-cods.py defines exclude patterns."""
        script_path = SCRIPT_DIR / "core" / "05-check-file-size-cods.py"
        with open(script_path, "r") as f:
            content = f.read()
            self.assertIn("EXCLUDE_PATTERNS", content)
            self.assertIn("node_modules", content)
            self.assertIn("tests/", content)

    def test_check_file_size_respects_gitignore(self):
        """Test that check-file-size-cods.py uses git ls-files."""
        script_path = SCRIPT_DIR / "core" / "05-check-file-size-cods.py"
        with open(script_path, "r") as f:
            content = f.read()
            # Accept either shell-style "git ls-files" or subprocess list ["git", "ls-files"]
            uses_git_ls_files = "git ls-files" in content or '"ls-files"' in content
            self.assertTrue(uses_git_ls_files, "Script should use 'git ls-files' to respect .gitignore")


class TestScriptHelp(unittest.TestCase):
    """Test that scripts provide help messages."""

    def test_scripts_have_argparse(self):
        """Test that Python scripts use argparse."""
        scripts = [
            SCRIPT_DIR / "utilities" / "generate-per-service-specs.py",
            SCRIPT_DIR / "core" / "05-check-file-size-cods.py",
            SCRIPT_DIR / "utilities" / "create-all-service-projects.py",
        ]

        for script_path in scripts:
            with open(script_path, "r") as f:
                content = f.read()
                self.assertIn("argparse", content, f"Script should use argparse: {script_path.name}")
                self.assertIn("ArgumentParser", content, f"Script should use ArgumentParser: {script_path.name}")


if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2)
