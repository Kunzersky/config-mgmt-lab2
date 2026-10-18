"""Tests for the initial command-line prototype."""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from src.main import build_parser, main, validate_arguments


class CliTests(unittest.TestCase):
    """Check configuration output and invalid parameter handling."""

    def test_print_configuration_prints_all_values(self):
        output = io.StringIO()
        parser = build_parser()
        args = parser.parse_args(
            ["--package", "serde", "--repository", "https://crates.io"]
        )
        with contextlib.redirect_stdout(output):
            from src.main import print_configuration

            print_configuration(args)
        self.assertIn("package=serde", output.getvalue())
        self.assertIn("test_mode=False", output.getvalue())
        self.assertIn("filter=", output.getvalue())

    def test_test_mode_prints_direct_dependencies(self):
        with tempfile.TemporaryDirectory() as directory:
            graph_path = Path(directory) / "graph.json"
            graph_path.write_text(
                json.dumps({"A": ["B", "C"]}), encoding="utf-8"
            )
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = main(
                    ["--package", "A", "--repository", str(graph_path),
                     "--test-mode"]
                )
        self.assertEqual(result, 0)
        self.assertIn("B", output.getvalue())
        self.assertIn("C", output.getvalue())

    def test_rejects_invalid_package(self):
        parser = build_parser()
        args = parser.parse_args(
            ["--package", "bad name", "--repository", "https://crates.io"]
        )
        with self.assertRaises(SystemExit):
            validate_arguments(args, parser)

    def test_rejects_invalid_repository_url(self):
        parser = build_parser()
        args = parser.parse_args(["--package", "serde", "--repository", "file"])
        with self.assertRaises(SystemExit):
            validate_arguments(args, parser)

    def test_rejects_missing_test_file(self):
        parser = build_parser()
        args = parser.parse_args(
            ["--package", "A", "--repository", "missing.json", "--test-mode"]
        )
        with self.assertRaises(SystemExit):
            validate_arguments(args, parser)

    def test_rejects_non_svg_output(self):
        parser = build_parser()
        args = parser.parse_args(
            ["--package", "serde", "--repository", "https://crates.io",
             "--output", "graph.png"]
        )
        with self.assertRaises(SystemExit):
            validate_arguments(args, parser)


if __name__ == "__main__":
    unittest.main()