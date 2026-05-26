from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from app.services.state_store import read_json_file, write_json_file


class StateStoreTests(unittest.TestCase):
    def test_write_then_read_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "nested" / "state.json"
            payload = {"name": "Agu", "count": 3, "enabled": True}

            written = write_json_file(path, payload)

            self.assertEqual(written, payload)
            self.assertTrue(path.exists())
            self.assertEqual(read_json_file(path), payload)

    def test_read_missing_file_uses_default_factory(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "missing.json"

            payload = read_json_file(path, default_factory=lambda: {"items": []})

            self.assertEqual(payload, {"items": []})

    def test_read_invalid_json_falls_back_to_default_factory(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "broken.json"
            path.write_text("{not-json}", encoding="utf-8")

            payload = read_json_file(path, default_factory=lambda: {"recovered": True})

            self.assertEqual(payload, {"recovered": True})


if __name__ == "__main__":
    unittest.main()
