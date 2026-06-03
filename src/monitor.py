import os
import time
import logging
import psutil

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("sys_monitor.log"),
        logging.StreamHandler()
    ]
)

class SystemMonitor:
    def __init__(self, cpu_threshold=80.0, memory_threshold=85.0, disk_threshold=90.0):
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold
        self.disk_threshold = disk_threshold

    def check_cpu(self):
        usage = psutil.cpu_percent(interval=1)
        if usage > self.cpu_threshold:
            logging.warning(f"High CPU usage detected: {usage}%")
        else:
            logging.info(f"CPU usage stable: {usage}%")
        return usage

    def check_memory(self):
        memory = psutil.virtual_memory()
        usage = memory.percent
        if usage > self.memory_threshold:
            logging.warning(f"High Memory usage detected: {usage}%")
        else:
            logging.info(f"Memory usage stable: {usage}%")
        return usage

    def check_disk(self):
        disk = psutil.disk_usage('/')
        usage = disk.percent
        if usage > self.disk_threshold:
            logging.warning(f"High Disk usage detected on root: {usage}%")
        else:
            logging.info(f"Disk usage stable: {usage}%")
        return usage

    def run_cycle(self):
        try:
            self.check_cpu()
            self.check_memory()
            self.check_disk()
        except Exception as e:
            logging.error(f"Error during monitoring cycle: {str(e)}")

if __name__ == '__main__':
    monitor = SystemMonitor()
    logging.info("Starting resource monitor cycle...")
    monitor.run_cycle()