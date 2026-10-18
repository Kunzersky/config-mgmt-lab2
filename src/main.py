"""Command-line entry point for the dependency graph visualizer."""

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import urlparse


PACKAGE_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")


def build_parser():
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description="Visualize dependencies from crates.io or a test graph."
    )
    parser.add_argument("--package", required=True, help="Package name")
    parser.add_argument(
        "--repository",
        required=True,
        help="crates.io base URL or test graph JSON path",
    )
    parser.add_argument(
        "--test-mode", action="store_true", help="Read a local test graph"
    )
    parser.add_argument(
        "--output", default="dependencies.svg", help="Output SVG path"
    )
    parser.add_argument(
        "--tree", action="store_true", help="Print dependencies as ASCII tree"
    )
    parser.add_argument(
        "--filter", default="", help="Ignore package names containing text"
    )
    return parser


def validate_arguments(args, parser):
    """Validate values that argparse accepts as strings."""
    if not PACKAGE_PATTERN.fullmatch(args.package):
        parser.error(
            "--package must contain only letters, digits, '.', '_' or '-'")
    if args.test_mode:
        if not Path(args.repository).is_file():
            parser.error(
                "--repository must be an existing JSON file in test mode")
    else:
        address = urlparse(args.repository)
        if address.scheme not in {"http", "https"} or not address.netloc:
            parser.error("--repository must be an HTTP or HTTPS URL")
    if not args.output.strip() or Path(args.output).suffix.lower() != ".svg":
        parser.error("--output must be a non-empty .svg path")


def print_configuration(args):
    """Print all user-configurable values in key-value form."""
    for key, value in vars(args).items():
        print(f"{key}={value}")


def main(argv=None):
    """Parse and validate arguments, then display the configuration."""
    parser = build_parser()
    args = parser.parse_args(argv)
    validate_arguments(args, parser)
    print_configuration(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())