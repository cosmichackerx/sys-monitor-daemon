import unittest
import os
import json
from src.monitor import SystemMonitor

class TestSystemMonitor(unittest.TestCase):
    def setUp(self):
        self.config_path = "test_config.json"
        config_data = {
            "cpu_threshold_percent": 80.0,
            "memory_threshold_percent": 80.0,
            "disk_threshold_percent": 80.0,
            "interval_seconds": 1,
            "log_file": "test_monitor.log"
        }
        with open(self.config_path, "w") as f:
            json.dump(config_data, f)
        self.monitor = SystemMonitor(self.config_path)

    def tearDown(self):
        if os.path.exists(self.config_path):
            os.remove(self.config_path)
        if os.path.exists("test_monitor.log"):
            os.remove("test_monitor.log")

    def test_config_loading(self):
        self.assertEqual(self.monitor.cpu_threshold, 80.0)
        self.assertEqual(self.monitor.interval, 1)

    def test_cpu_calculation(self):
        first = (100, 200)
        second = (120, 300)
        pct = self.monitor.calculate_cpu_percent(first, second)
        self.assertAlmostEqual(pct, 80.0)

if __name__ == "__main__":
    unittest.main()