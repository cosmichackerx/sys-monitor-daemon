import json
import os
import time
import logging

class SystemMonitor:
    def __init__(self, config_path):
        self.config_path = config_path
        self.load_config()
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler()
            ]
        )

    def load_config(self):
        with open(self.config_path, "r") as f:
            config = json.load(f)
        self.cpu_threshold = config.get("cpu_threshold_percent", 80.0)
        self.mem_threshold = config.get("memory_threshold_percent", 80.0)
        self.disk_threshold = config.get("disk_threshold_percent", 90.0)
        self.interval = config.get("interval_seconds", 60)
        self.log_file = config.get("log_file", "monitor.log")

    def get_cpu_usage(self):
        try:
            with open("/proc/stat", "r") as f:
                line = f.readline()
            parts = line.split()
            if len(parts) < 5:
                return None
            idle = float(parts[4])
            total = sum(float(x) for x in parts[1:8])
            return (idle, total)
        except Exception:
            return None

    def calculate_cpu_percent(self, first, second):
        if not first or not second:
            return 0.0
        idle_diff = second[0] - first[0]
        total_diff = second[1] - first[1]
        if total_diff == 0:
            return 0.0
        return (1.0 - (idle_diff / total_diff)) * 100.0

    def get_memory_usage(self):
        try:
            meminfo = {}
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 2:
                        meminfo[parts[0].rstrip(":")] = int(parts[1])
            total = meminfo.get("MemTotal", 0)
            free = meminfo.get("MemFree", 0)
            buffers = meminfo.get("Buffers", 0)
            cached = meminfo.get("Cached", 0)
            if total == 0:
                return 0.0
            used = total - free - buffers - cached
            return (used / total) * 100.0
        except Exception:
            return 0.0

    def get_disk_usage(self):
        try:
            stat = os.statvfs("/")
            total = stat.f_blocks * stat.f_frsize
            free = stat.f_bfree * stat.f_frsize
            used = total - free
            if total == 0:
                return 0.0
            return (used / total) * 100.0
        except Exception:
            return 0.0

    def run_once(self):
        cpu_start = self.get_cpu_usage()
        time.sleep(1)
        cpu_end = self.get_cpu_usage()
        cpu_pct = self.calculate_cpu_percent(cpu_start, cpu_end)
        mem_pct = self.get_memory_usage()
        disk_pct = self.get_disk_usage()

        logging.info(f"Metrics - CPU: {cpu_pct:.1f}%, RAM: {mem_pct:.1f}%, Disk: {disk_pct:.1f}%")

        if cpu_pct > self.cpu_threshold:
            logging.warning(f"CPU threshold exceeded: {cpu_pct:.1f}% > {self.cpu_threshold}%")
        if mem_pct > self.mem_threshold:
            logging.warning(f"Memory threshold exceeded: {mem_pct:.1f}% > {self.mem_threshold}%")
        if disk_pct > self.disk_threshold:
            logging.warning(f"Disk threshold exceeded: {disk_pct:.1f}% > {self.disk_threshold}%")

    def monitor_loop(self):
        logging.info("Starting system monitor daemon loop.")
        while True:
            try:
                self.run_once()
                time.sleep(self.interval)
            except KeyboardInterrupt:
                logging.info("Daemon execution interrupted by user.")
                break
            except Exception as e:
                logging.error(f"Error in monitor loop: {e}")