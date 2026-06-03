import unittest
import os
import json
import sqlite3
import shutil
from unittest.mock import patch, MagicMock
from src.daemon import SysMonitorDaemon

class TestSysMonitorDaemon(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_env"
        os.makedirs(self.test_dir, exist_ok=True)
        self.config_path = os.path.join(self.test_dir, "config.json")
        self.db_path = os.path.join(self.test_dir, "metrics.db")
        
        self.config_data = {
            "interval_seconds": 1,
            "db_path": self.db_path,
            "thresholds": {
                "cpu_percent": 80.0,
                "memory_percent": 80.0
            }
        }
        with open(self.config_path, "w") as f:
            json.dump(self.config_data, f)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_init_and_config_loading(self):
        daemon = SysMonitorDaemon(config_path=self.config_path)
        self.assertEqual(daemon.config["interval_seconds"], 1)
        self.assertTrue(os.path.exists(self.db_path))

    @patch("psutil.cpu_percent")
    @patch("psutil.virtual_memory")
    @patch("psutil.disk_usage")
    @patch("psutil.net_io_counters")
    def test_collect_metrics(self, mock_net, mock_disk, mock_mem, mock_cpu):
        mock_cpu.return_value = 45.0
        
        mem_mock = MagicMock()
        mem_mock.percent = 60.0
        mock_mem.return_value = mem_mock
        
        disk_mock = MagicMock()
        disk_mock.percent = 30.0
        mock_disk.return_value = disk_mock
        
        net_mock = MagicMock()
        net_mock.bytes_sent = 1000
        net_mock.bytes_recv = 2000
        mock_net.return_value = net_mock

        daemon = SysMonitorDaemon(config_path=self.config_path)
        metrics = daemon.collect_metrics()
        
        self.assertEqual(metrics["cpu_usage"], 45.0)
        self.assertEqual(metrics["memory_usage"], 60.0)
        self.assertEqual(metrics["disk_usage"], 30.0)
        self.assertEqual(metrics["net_sent"], 1000)
        self.assertEqual(metrics["net_recv"], 2000)

    def test_save_metrics(self):
        daemon = SysMonitorDaemon(config_path=self.config_path)
        metrics = {
            "timestamp": "2026-06-03T12:00:00",
            "cpu_usage": 10.0,
            "memory_usage": 20.0,
            "disk_usage": 30.0,
            "net_sent": 500,
            "net_recv": 600
        }
        daemon.save_metrics(metrics)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM metrics")
        rows = cursor.fetchall()
        conn.close()
        
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][2], 10.0)
        self.assertEqual(rows[0][3], 20.0)

if __name__ == "__main__":
    unittest.main()