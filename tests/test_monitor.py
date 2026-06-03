import unittest
from src.monitor import SystemMonitor

class TestSystemMonitor(unittest.TestCase):
    def setUp(self):
        self.monitor = SystemMonitor(cpu_threshold=100.0, memory_threshold=100.0, disk_threshold=100.0)

    def test_thresholds(self):
        self.assertEqual(self.monitor.cpu_threshold, 100.0)
        self.assertEqual(self.monitor.memory_threshold, 100.0)
        self.assertEqual(self.monitor.disk_threshold, 100.0)

if __name__ == '__main__':
    unittest.main()