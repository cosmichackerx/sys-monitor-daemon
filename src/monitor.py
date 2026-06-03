import os
import sys
import time
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

class SystemMonitor:
    def __init__(self, interval=10):
        self.interval = interval

    def get_cpu_usage(self):
        try:
            with open('/proc/stat', 'r') as f:
                line = f.readline()
            parts = list(map(int, line.split()[1:5]))
            idle, total = parts[3], sum(parts)
            return idle, total
        except Exception:
            return None, None

    def get_memory_usage(self):
        try:
            meminfo = {}
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    parts = line.split()
                    meminfo[parts[0].replace(':', '')] = int(parts[1])
            total = meminfo.get('MemTotal', 1)
            free = meminfo.get('MemFree', 0) + meminfo.get('Buffers', 0) + meminfo.get('Cached', 0)
            used = total - free
            return {
                'total_mb': total / 1024,
                'used_mb': used / 1024,
                'percent': (used / total) * 100
            }
        except Exception:
            return None

    def get_disk_usage(self):
        try:
            stat = os.statvfs('/')
            total = (stat.f_blocks * stat.f_frsize) / (1024 * 1024)
            free = (stat.f_bavail * stat.f_frsize) / (1024 * 1024)
            used = total - free
            return {
                'total_mb': total,
                'used_mb': used,
                'percent': (used / total) * 100
            }
        except Exception:
            return None

    def collect(self):
        idle1, total1 = self.get_cpu_usage()
        time.sleep(1)
        idle2, total2 = self.get_cpu_usage()
        
        cpu_percent = 0.0
        if idle1 is not None and idle2 is not None:
            diff_idle = idle2 - idle1
            diff_total = total2 - total1
            if diff_total > 0:
                cpu_percent = (1.0 - (diff_idle / diff_total)) * 100
        
        mem = self.get_memory_usage()
        disk = self.get_disk_usage()
        
        return {
            'timestamp': int(time.time()),
            'cpu_percent': round(cpu_percent, 2),
            'memory': mem,
            'disk': disk
        }

    def run(self):
        logging.info('Starting sys-monitor-daemon...')
        while True:
            metrics = self.collect()
            logging.info(f'System Metrics: {json.dumps(metrics)}')
            time.sleep(self.interval)

if __name__ == '__main__':
    monitor = SystemMonitor()
    monitor.run()
