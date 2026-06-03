import os
import sys
import time
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

class SystemMonitor:
    def __init__(self, config_path='config/config.json'):
        self.config = self.load_config(config_path)
        self.interval = self.config.get('interval', 10)

    def load_config(self, path):
        try:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logging.error(f'Failed to load config: {e}')
        return {}

    def get_cpu_usage(self):
        try:
            import psutil
            return psutil.cpu_percent(interval=1)
        except ImportError:
            try:
                with open('/proc/stat', 'r') as f:
                    fields = [float(val) for val in f.readline().strip().split()[1:]]
                idle, total = fields[3], sum(fields)
                time.sleep(1)
                with open('/proc/stat', 'r') as f:
                    fields = [float(val) for val in f.readline().strip().split()[1:]]
                idle_next, total_next = fields[3], sum(fields)
                diff_idle = idle_next - idle
                diff_total = total_next - total
                return 100.0 * (1.0 - (diff_idle / diff_total)) if diff_total > 0 else 0.0
            except Exception:
                return 0.0

    def get_memory_usage(self):
        try:
            import psutil
            return psutil.virtual_memory().percent
        except ImportError:
            try:
                with open('/proc/meminfo', 'r') as f:
                    meminfo = {line.split(':')[0]: int(line.split()[1]) for line in f if len(line.split()) > 1}
                total = meminfo.get('MemTotal', 1.0)
                free = meminfo.get('MemFree', 0.0) + meminfo.get('Buffers', 0.0) + meminfo.get('Cached', 0.0)
                return 100.0 * (1.0 - (free / total))
            except Exception:
                return 0.0

    def run(self):
        logging.info('Daemon initialized. Starting metrics harvesting.')
        while True:
            cpu = self.get_cpu_usage()
            mem = self.get_memory_usage()
            logging.info(f'CPU Utilization: {cpu:.2f}% | Memory Utilization: {mem:.2f}%')
            time.sleep(self.interval)

if __name__ == '__main__':
    monitor = SystemMonitor()
    monitor.run()