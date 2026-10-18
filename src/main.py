"""Command-line entry point for the dependency graph visualizer."""

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

from src.cargo import CargoRegistryError, fetch_direct_dependencies
from src.graph import build_graph, installation_order, load_test_graph


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
        "--order", action="store_true", help="Print dependency loading order"
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


def main(argv=None):
    """Parse options and print the reachable dependency graph."""
    parser = build_parser()
    args = parser.parse_args(argv)
    validate_arguments(args, parser)
    try:
        if args.test_mode:
            source = load_test_graph(args.repository)
            if args.package not in source:
                raise ValueError(f"Package not found: {args.package}")
            get_dependencies = lambda name: source.get(name, [])
        else:
            get_dependencies = lambda name: fetch_direct_dependencies(
                name, args.repository
            )
        graph = build_graph(args.package, get_dependencies, args.filter)
    except (
        OSError, ValueError, CargoRegistryError
    ) as error:
        parser.error(str(error))
    if args.order:
        try:
            order = installation_order(graph, args.package)
        except ValueError as error:
            parser.error(str(error))
        print("Installation order:")
        print(" -> ".join(order))
        return 0
    print(f"Dependency graph of {args.package}:")
    has_edges = False
    for package, dependencies in graph.items():
        for dependency in dependencies:
            print(f"{package} -> {dependency}")
            has_edges = True
    if not has_edges:
        print("(none)")
    return 0


if __name__ == "__main__":
    sys.exit(main())