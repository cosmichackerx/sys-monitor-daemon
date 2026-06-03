import os
import unittest
import sqlite3
import json
import tempfile
from src.daemon import SystemTelemetryDaemon

class TestTelemetryDaemon(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.test_dir.name, 'test_telemetry.db')
        self.config_path = os.path.join(self.test_dir.name, 'config.json')
        
        self.config_data = {
            "db_path": self.db_path,
            "interval": 1,
            "max_records": 5,
            "webhook_url": "",
            "thresholds": {
                "cpu": 80.0,
                "ram": 80.0,
                "disk": 80.0
            }
        }
        with open(self.config_path, 'w') as f:
            json.dump(self.config_data, f)
        
        self.daemon = SystemTelemetryDaemon(self.config_path)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_database_initialization(self):
        self.assertTrue(os.path.exists(self.db_path))
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='telemetry';")
            self.assertIsNotNone(cursor.fetchone())

    def test_record_metrics_and_pruning(self):
        for i in range(10):
            self.daemon.record_metrics(10.0 + i, 20.0 + i, 30.0 + i)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM telemetry")
            count = cursor.fetchone()[0]
            self.assertEqual(count, 5)

    def test_alert_dispatch_no_url(self):
        try:
            self.daemon.dispatch_alert('cpu', 95.0, 80.0)
            executed = True
        except Exception:
            executed = False
        self.assertTrue(executed)

if __name__ == '__main__':
    unittest.main()