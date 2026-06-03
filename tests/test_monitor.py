import unittest
from unittest.mock import patch, mock_open
from src.daemon import SystemMonitor

class TestSystemMonitor(unittest.TestCase):
    def setUp(self):
        self.config_data = '{"interval_seconds": 1, "thresholds": {"cpu_percent": 80.0, "memory_percent": 85.0, "disk_percent": 90.0}, "webhook_url": "http://localhost/test"}'

    @patch('builtins.open', new_callable=mock_open)
    def test_load_config_success(self, mock_file):
        mock_file.return_value.read.return_value = self.config_data
        monitor = SystemMonitor('config/monitor_rules.json')
        self.assertEqual(monitor.config['interval_seconds'], 1)
        self.assertEqual(monitor.config['thresholds']['cpu_percent'], 80.0)

    @patch('builtins.open', new_callable=mock_open, read_data="cpu  100 200 300 400 500")
    def test_get_cpu_usage(self, mock_file):
        monitor = SystemMonitor('dummy_path')
        monitor.config = {"thresholds": {"cpu_percent": 80.0}}
        first_val = monitor.get_cpu_usage()
        self.assertEqual(first_val, 0.0)

    @patch('builtins.open', new_callable=mock_open, read_data="MemTotal: 1000 kB\nMemFree: 200 kB\nBuffers: 100 kB\nCached: 200 kB\n")
    def test_get_memory_usage(self, mock_file):
        monitor = SystemMonitor('dummy_path')
        mem_usage = monitor.get_memory_usage()
        # Used = Total - (Free + Buffers + Cached) = 1000 - (200 + 100 + 200) = 500
        # Percentage = (500 / 1000) * 100 = 50.0%
        self.assertEqual(mem_usage, 50.0)

    @patch('urllib.request.urlopen')
    @patch('builtins.open', new_callable=mock_open)
    def test_alert_threshold_breach(self, mock_file, mock_urlopen):
        mock_file.return_value.read.return_value = self.config_data
        monitor = SystemMonitor('dummy_path')
        monitor.send_alert('cpu_percent', 88.5, 80.0)
        self.assertTrue(mock_urlopen.called)

if __name__ == '__main__':
    unittest.main()