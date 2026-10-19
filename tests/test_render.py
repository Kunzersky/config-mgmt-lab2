"""Tests for graph text and SVG rendering."""

import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

from src.render import format_ascii_tree, format_graphviz, save_svg


class RenderTests(unittest.TestCase):
    """Check Mermaid, tree, and SVG output."""

    def setUp(self):
        self.graph = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}

    def test_graphviz_contains_nodes_and_edges(self):
        result = format_graphviz(self.graph)
        self.assertIn("digraph dependencies {", result)
        self.assertIn('"A";', result)
        self.assertIn('"A" -> "B";', result)

    def test_graphviz_escapes_quoted_package_names(self):
        result = format_graphviz({'A"B': []})
        self.assertIn('"A\\"B";', result)

    def test_ascii_tree_marks_repeated_dependency(self):
        result = format_ascii_tree(self.graph, "A")
        self.assertIn("|-- B", result)
        self.assertIn("(already shown)", result)

    def test_svg_is_valid_xml_with_all_package_labels(self):
        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "graph.svg"
            dot_path = save_svg(self.graph, output_path)
            root = ET.parse(output_path).getroot()
            dot_text = dot_path.read_text(encoding="utf-8")
        labels = [
            item.text
            for item in root.findall(".//{http://www.w3.org/2000/svg}text")
        ]
        self.assertEqual(labels, ["A", "B", "C", "D"])
        self.assertIn('"C" -> "D";', dot_text)

    @patch("src.render.subprocess.run")
    @patch("src.render.shutil.which", return_value="/usr/bin/dot")
    def test_uses_graphviz_when_installed(self, _which, mocked_run):
        mocked_run.return_value.stdout = "<svg/>"
        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "graph.svg"
            save_svg(self.graph, output_path)
            saved_svg = output_path.read_text(encoding="utf-8")
        self.assertEqual(saved_svg, "<svg/>")
        self.assertIn("-Tsvg", mocked_run.call_args.args[0])


if __name__ == "__main__":
    unittest.main()