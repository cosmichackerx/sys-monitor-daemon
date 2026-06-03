import unittest
import os
import json
from src.daemon import SystemMonitorDaemon

class TestSystemMonitor(unittest.TestCase):
    def setUp(self):
        self.config_path = "/tmp/test_config.json"
        self.test_config = {
            "interval": 1,
            "log_file": "/tmp/test_sys_monitor.log",
            "state_file": "/tmp/test_sys_monitor_state.json",
            "thresholds": {
                "cpu_percent": 50.0,
                "memory_percent": 50.0,
                "disk_percent": 50.0
            }
        }
        with open(self.config_path, 'w') as f:
            json.dump(self.test_config, f)
        self.daemon = SystemMonitorDaemon(self.config_path)

    def tearDown(self):
        for path in [self.config_path, "/tmp/test_sys_monitor.log", "/tmp/test_sys_monitor_state.json"]:
            if os.path.exists(path):
                os.remove(path)

    def test_load_config(self):
        self.assertEqual(self.daemon.config["interval"], 1)
        self.assertEqual(self.daemon.config["thresholds"]["cpu_percent"], 50.0)

    def test_collect_metrics(self):
        metrics = self.daemon.collect_metrics()
        self.assertIn("cpu_usage_percent", metrics)
        self.assertIn("memory_usage_percent", metrics)
        self.assertIn("disk_usage_percent", metrics)
        self.assertIsInstance(metrics["cpu_usage_percent"], float)

if __name__ == "__main__":
    unittest.main()