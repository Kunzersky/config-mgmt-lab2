"""Tests for dependency graph loading and traversal."""

import json
import tempfile
import unittest
from pathlib import Path

from src.graph import build_graph, installation_order, load_test_graph


class GraphTests(unittest.TestCase):
    """Check breadth-first traversal, filtering, and cyclic graphs."""

    def test_breadth_first_walk_and_shared_dependency(self):
        source = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}
        visited_in_order = []

        def dependencies(package):
            visited_in_order.append(package)
            return source[package]

        result = build_graph("A", dependencies)

        self.assertEqual(visited_in_order, ["A", "B", "C", "D"])
        self.assertEqual(result["C"], ["D"])
        self.assertEqual(result["D"], [])

    def test_filter_excludes_matching_dependency(self):
        source = {"A": ["B", "SKIP"], "B": ["C"], "C": []}
        visited = []

        def dependencies(package):
            """Record the packages fetched by the graph traversal."""
            visited.append(package)
            return source.get(package, [])

        result = build_graph("A", dependencies, "SKIP")
        self.assertEqual(result, {"A": ["B"], "B": ["C"], "C": []})
        self.assertEqual(visited, ["A", "B", "C"])

    def test_filter_rejects_matching_root(self):
        with self.assertRaisesRegex(ValueError, "Root package SKIP"):
            build_graph("SKIP_ROOT", lambda _package: [], "SKIP")

    def test_cycle_terminates(self):
        source = {"A": ["B"], "B": ["C"], "C": ["A"]}
        result = build_graph("A", source.get)
        self.assertEqual(result, source)

    def test_installation_order_places_dependencies_first(self):
        graph = {
            "A": ["B", "C"],
            "B": ["D"],
            "C": ["D", "E"],
            "D": [],
            "E": ["F"],
            "F": [],
        }
        order = installation_order(graph, "A")
        self.assertEqual(order[-1], "A")
        self.assertEqual(len(order), len(set(order)))
        self.assertLess(order.index("D"), order.index("B"))
        self.assertLess(order.index("D"), order.index("C"))

    def test_installation_order_rejects_cycles(self):
        with self.assertRaisesRegex(ValueError, "cyclic dependency"):
            installation_order({"A": ["B"], "B": ["A"]}, "A")

    def test_test_graph_requires_uppercase_names(self):
        with tempfile.TemporaryDirectory() as directory:
            graph_path = Path(directory) / "graph.json"
            graph_path.write_text(json.dumps({"A": ["bad"]}), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_test_graph(graph_path)


if __name__ == "__main__":
    unittest.main()