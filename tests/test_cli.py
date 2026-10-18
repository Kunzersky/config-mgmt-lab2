"""Tests for the initial command-line prototype."""

import contextlib
import io
import unittest

from src.main import build_parser, main, validate_arguments


class CliTests(unittest.TestCase):
    """Check configuration output and invalid parameter handling."""

    def test_prints_all_options_as_key_value(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = main(
                ["--package", "serde", "--repository", "https://crates.io"]
            )
        self.assertEqual(result, 0)
        self.assertIn("package=serde", output.getvalue())
        self.assertIn("test_mode=False", output.getvalue())
        self.assertIn("filter=", output.getvalue())

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