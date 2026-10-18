"""Load and traverse package dependency graphs."""

import json
import re
from collections import deque
from pathlib import Path


TEST_NAME = re.compile(r"[A-Z]+")


def load_test_graph(path):
    """Load and validate a test graph whose package names are uppercase."""
    graph = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(graph, dict):
        raise ValueError("Test graph must be a JSON object")
    for package, dependencies in graph.items():
        if not TEST_NAME.fullmatch(package):
            raise ValueError(f"Invalid test package name: {package}")
        if not isinstance(dependencies, list):
            raise ValueError(f"Dependencies of {package} must be a list")
        if any(
            not isinstance(name, str) or not TEST_NAME.fullmatch(name)
            for name in dependencies
        ):
            raise ValueError(f"Invalid dependency name in {package}")
    return graph


def expand_queue(
    pending, graph, visited, get_dependencies, filter_text
):
    """Recursively process a BFS queue and record each reachable edge."""
    if not pending:
        return
    package = pending.popleft()
    if package not in visited:
        visited.add(package)
        graph[package] = []
        for dependency in get_dependencies(package):
            if filter_text and filter_text in dependency:
                continue
            graph[package].append(dependency)
            if dependency not in visited:
                pending.append(dependency)
    expand_queue(
        pending, graph, visited, get_dependencies, filter_text
    )


def build_graph(root, get_dependencies, filter_text=""):
    """Build the reachable graph with recursive breadth-first search."""
    graph = {}
    visited = set()
    pending = deque([root])
    expand_queue(
        pending, graph, visited, get_dependencies, filter_text
    )
    return graph