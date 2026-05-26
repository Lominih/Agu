from __future__ import annotations

import unittest
from unittest.mock import patch

from app.main import health, refresh_real_data_status


class ApiCoreTests(unittest.TestCase):
    def test_health_endpoint_returns_ok(self) -> None:
        self.assertEqual(health(), {"status": "ok"})

    def test_refresh_status_endpoint_uses_service_result(self) -> None:
        mock_status = {"state": "idle", "message": "ready"}
        with patch("app.main.get_runtime_refresh_status", return_value=mock_status) as mocked:
            payload = refresh_real_data_status()

        mocked.assert_called_once()
        self.assertEqual(payload, mock_status)


if __name__ == "__main__":
    unittest.main()
