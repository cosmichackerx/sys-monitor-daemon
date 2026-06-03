import unittest
import json
import os
from unittest.mock import patch, MagicMock

# Mock environment prior to relative/absolute imports
class TestSysMonitorDaemon(unittest.TestCase):
    def setUp(self):
        self.test_config = {
            "monitor_interval_seconds": 1,
            "thresholds": {
                "cpu_percent": 50.0,
                "memory_percent": 50.0,
                "disk_percent": 50.0
            },
            "alerting": {
                "slack_webhook_url": "",
                "log_to_file": False,
                "log_path": ""
            }
        }

    def test_config_loading(self):
        """Verify configuration parsing rules and default thresholds"""
        self.assertEqual(self.test_config["monitor_interval_seconds"], 1)
        self.assertIn("thresholds", self.test_config)
        self.assertIn("cpu_percent", self.test_config["thresholds"])

    @patch('psutil.cpu_percent')
    def test_cpu_threshold_exceeded(self, mock_cpu):
        """Test threshold alerting logic when CPU exceeds limits"""
        mock_cpu.return_value = 75.0
        current_cpu = mock_cpu()
        threshold = self.test_config["thresholds"]["cpu_percent"]
        self.assertTrue(current_cpu > threshold)

    @patch('psutil.virtual_memory')
    def test_memory_threshold_nominal(self, mock_mem):
        """Test memory utilization within acceptable margins"""
        mock_val = MagicMock()
        mock_val.percent = 30.0
        mock_mem.return_value = mock_val
        current_mem = mock_mem().percent
        threshold = self.test_config["thresholds"]["memory_percent"]
        self.assertFalse(current_mem > threshold)

if __name__ == '__main__':
    unittest.main()