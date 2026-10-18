"""Tests for graph text and SVG rendering."""

import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from src.render import format_ascii_tree, format_mermaid, save_svg


class RenderTests(unittest.TestCase):
    """Check Mermaid, tree, and SVG output."""

    def setUp(self):
        self.graph = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}

    def test_mermaid_contains_nodes_and_edges(self):
        result = format_mermaid(self.graph)
        self.assertIn("flowchart TD", result)
        self.assertIn('n0["A"]', result)
        self.assertIn("n0 --> n1", result)

    def test_ascii_tree_marks_repeated_dependency(self):
        result = format_ascii_tree(self.graph, "A")
        self.assertIn("|-- B", result)
        self.assertIn("(already shown)", result)

    def test_svg_is_valid_xml_with_all_package_labels(self):
        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "graph.svg"
            save_svg(self.graph, output_path)
            root = ET.parse(output_path).getroot()
        labels = [
            item.text
            for item in root.findall(".//{http://www.w3.org/2000/svg}text")
        ]
        self.assertEqual(labels, ["A", "B", "C", "D"])


if __name__ == "__main__":
    unittest.main()