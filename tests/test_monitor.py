import unittest
import os
import json
from src.monitor import SystemMonitorDaemon

class TestSystemMonitorDaemon(unittest.TestCase):
    def setUp(self):
        self.config_path = "config/settings_test.json"
        self.test_config = {
            "interval_sec": 1,
            "cpu_threshold_pct": 80.0,
            "mem_threshold_pct": 80.0,
            "disk_threshold_pct": 80.0,
            "log_file": "sys_monitor_test.log"
        }
        os.makedirs("config", exist_ok=True)
        with open(self.config_path, "w") as f:
            json.dump(self.test_config, f)
        self.daemon = SystemMonitorDaemon(config_path=self.config_path)

    def tearDown(self):
        if os.path.exists(self.config_path):
            os.remove(self.config_path)
        if os.path.exists("sys_monitor_test.log"):
            os.remove("sys_monitor_test.log")

    def test_load_config(self):
        self.assertEqual(self.daemon.config["cpu_threshold_pct"], 80.0)

    def test_calculate_cpu_pct(self):
        prev = (100, 1000)
        curr = (150, 1200)
        usage = self.daemon.calculate_cpu_pct(prev, curr)
        self.assertAlmostEqual(usage, 75.0)

    def test_get_disk_usage(self):
        pct = self.daemon.get_disk_usage()
        self.assertTrue(0.0 <= pct <= 100.0)

    def test_run_once(self):
        status = self.daemon.run_once()
        self.assertIn("cpu_pct", status)
        self.assertIn("mem_pct", status)
        self.assertIn("disk_pct", status)

if __name__ == '__main__':
    unittest.main()