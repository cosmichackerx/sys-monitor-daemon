import unittest
import os
import json
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.daemon import MonitorDaemon

class TestMonitorDaemon(unittest.TestCase):
    def setUp(self):
        self.config_path = "config/test_settings.json"
        os.makedirs("config", exist_ok=True)
        self.test_config = {
            "cpu_threshold": 95.0,
            "mem_threshold": 95.0,
            "disk_threshold": 95.0,
            "interval_sec": 1,
            "http_port": 9101,
            "webhook_url": ""
        }
        with open(self.config_path, "w") as f:
            json.dump(self.test_config, f)
        self.daemon = MonitorDaemon(config_path=self.config_path)

    def tearDown(self):
        if os.path.exists(self.config_path):
            os.remove(self.config_path)

    def test_daemon_metric_integrity(self):
        self.daemon.update_metrics()
        self.assertIn("cpu_load", self.daemon.metrics)
        self.assertIn("mem_used_pct", self.daemon.metrics)
        self.assertIn("disk_used_pct", self.daemon.metrics)
        self.assertTrue(0 <= self.daemon.metrics["disk_used_pct"] <= 100)

if __name__ == "__main__":
    unittest.main()