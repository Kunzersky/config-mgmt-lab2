"""Tests for Cargo registry response handling."""

import io
import json
import unittest
from unittest.mock import patch

from src.cargo import fetch_direct_dependencies


class CargoTests(unittest.TestCase):
    """Check stable version lookup and direct dependency selection."""

    @patch("src.cargo.urlopen")
    def test_fetches_normal_and_build_dependencies(self, mocked_urlopen):
        responses = [
            {"crate": {"max_stable_version": "1.2.3"}},
            {
                "dependencies": [
                    {"crate_id": "serde", "kind": "normal"},
                    {"crate_id": "cc", "kind": "build"},
                    {"crate_id": "demo-tests", "kind": "dev"},
                    {"crate_id": "serde", "kind": "normal"},
                ]
            },
        ]
        mocked_urlopen.side_effect = [
            io.BytesIO(json.dumps(item).encode()) for item in responses
        ]

        result = fetch_direct_dependencies("demo", "https://crates.io")

        self.assertEqual(result, ["cc", "serde"])
        self.assertEqual(mocked_urlopen.call_count, 2)
        dependency_request = mocked_urlopen.call_args_list[1].args[0]
        self.assertTrue(
            dependency_request.full_url.endswith("/1.2.3/dependencies")
        )

    @patch("src.cargo.urlopen")
    def test_returns_empty_list_without_dependencies(self, mocked_urlopen):
        responses = [
            {"crate": {"max_version": "0.1.0"}},
            {"dependencies": []},
        ]
        mocked_urlopen.side_effect = [
            io.BytesIO(json.dumps(item).encode()) for item in responses
        ]
        self.assertEqual(
            fetch_direct_dependencies("empty", "https://crates.io"), []
        )


if __name__ == "__main__":
    unittest.main()