"""Tests for the initial command-line prototype."""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from src.main import build_parser, collect_graph, main, validate_arguments


class CliTests(unittest.TestCase):
    """Check configuration output and invalid parameter handling."""

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
                     "--test-mode", "--output",
                     str(Path(directory) / "test.svg")]
                )
        self.assertEqual(result, 0)
        self.assertIn("B", output.getvalue())
        self.assertIn("C", output.getvalue())

    def test_explicit_version_is_passed_to_registry(self):
        from unittest.mock import patch

        parser = build_parser()
        args = parser.parse_args(
            ["--package", "serde", "--version", "1.0.0",
             "--repository", "https://crates.io"]
        )
        with patch(
            "src.main.fetch_direct_dependencies", return_value=[]
        ) as fetch:
            with patch(
                "src.main.build_graph",
                side_effect=lambda root, getter, filter_text: {
                    root: getter(root)
                },
            ):
                collect_graph(args)
        fetch.assert_called_once_with("serde", "https://crates.io", "1.0.0")

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