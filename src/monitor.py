import os
import sys
import time
import json
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('system_monitor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class SystemMonitor:
    def __init__(self, interval=60):
        self.interval = interval

    def get_cpu_usage(self):
        try:
            if os.path.exists('/proc/loadavg'):
                with open('/proc/loadavg', 'r') as f:
                    load = f.readline().split()
                return float(load[0])
            return -1.0
        except Exception as e:
            logging.error(f'Error reading CPU usage: {e}')
            return -1.0

    def get_memory_usage(self):
        try:
            if os.path.exists('/proc/meminfo'):
                with open('/proc/meminfo', 'r') as f:
                    lines = f.readlines()
                mem_total = 0
                mem_free = 0
                for line in lines:
                    if 'MemTotal' in line:
                        mem_total = int(line.split()[1])
                    elif 'MemFree' in line:
                        mem_free = int(line.split()[1])
                if mem_total > 0:
                    return round(((mem_total - mem_free) / mem_total) * 100, 2)
            return -1.0
        except Exception as e:
            logging.error(f'Error reading memory usage: {e}')
            return -1.0

    def get_disk_usage(self, path='/'):
        try:
            stat = os.statvfs(path)
            total = stat.f_blocks * stat.f_frsize
            free = stat.f_bfree * stat.f_frsize
            used = total - free
            if total > 0:
                return round((used / total) * 100, 2)
            return -1.0
        except Exception as e:
            logging.error(f'Error reading disk usage: {e}')
            return -1.0

    def run(self):
        logging.info('Starting SystemMonitor daemon loop...')
        while True:
            metrics = {
                'cpu_load_1min': self.get_cpu_usage(),
                'memory_used_percent': self.get_memory_usage(),
                'disk_used_percent': self.get_disk_usage()
            }
            logging.info(f'Metrics recorded: {json.dumps(metrics)}')
            time.sleep(self.interval)

if __name__ == "__main__":
    monitor = SystemMonitor(interval=10)
    try:
        monitor.run()
    except KeyboardInterrupt:
        logging.info('SystemMonitor daemon stopped by user.')
        sys.exit(0)
