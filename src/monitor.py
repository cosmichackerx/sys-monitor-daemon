import os
import sys
import time
import json
import shutil
import logging
from datetime import datetime

class SystemMonitorDaemon:
    def __init__(self, config_path="config/settings.json"):
        self.config_path = config_path
        self.config = self.load_config()
        self.setup_logging()

    def load_config(self):
        default_config = {
            "interval_sec": 10,
            "cpu_threshold_pct": 85.0,
            "mem_threshold_pct": 90.0,
            "disk_threshold_pct": 95.0,
            "log_file": "sys_monitor.log"
        }
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    return {**default_config, **json.load(f)}
            except Exception:
                pass
        return default_config

    def setup_logging(self):
        logging.basicConfig(
            filename=self.config.get("log_file", "sys_monitor.log"),
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s"
        )
        self.logger = logging.getLogger("SysMonitorDaemon")

    def get_cpu_usage(self):
        if sys.platform.startswith("linux"):
            try:
                with open("/proc/stat", "r") as f:
                    line = f.readline()
                parts = line.split()
                if len(parts) >= 5:
                    fields = [float(x) for x in parts[1:5]]
                    idle = fields[3]
                    total = sum(fields)
                    return (idle, total)
            except Exception as e:
                self.logger.error(f"Error reading CPU stats: {e}")
        return None

    def calculate_cpu_pct(self, prev, current):
        if not prev or not current:
            return 0.0
        prev_idle, prev_total = prev
        curr_idle, curr_total = current
        idle_diff = curr_idle - prev_idle
        total_diff = curr_total - prev_total
        if total_diff == 0:
            return 0.0
        return (1.0 - (idle_diff / total_diff)) * 100.0

    def get_mem_usage(self):
        if sys.platform.startswith("linux"):
            try:
                meminfo = {}
                with open("/proc/meminfo", "r") as f:
                    for line in f:
                        parts = line.split()
                        if len(parts) >= 2:
                            key = parts[0].rstrip(":")
                            val = int(parts[1])
                            meminfo[key] = val
                total = meminfo.get("MemTotal", 1)
                free = meminfo.get("MemFree", 0)
                buffers = meminfo.get("Buffers", 0)
                cached = meminfo.get("Cached", 0)
                used = total - free - buffers - cached
                return (used / total) * 100.0
            except Exception as e:
                self.logger.error(f"Error reading Memory stats: {e}")
        return 0.0

    def get_disk_usage(self):
        try:
            total, used, free = shutil.disk_usage("/")
            return (used / total) * 100.0
        except Exception as e:
            self.logger.error(f"Error reading Disk stats: {e}")
            return 0.0

    def check_thresholds(self):
        cpu_stat_start = self.get_cpu_usage()
        time.sleep(1.0)
        cpu_stat_end = self.get_cpu_usage()
        cpu_pct = self.calculate_cpu_pct(cpu_stat_start, cpu_stat_end)
        mem_pct = self.get_mem_usage()
        disk_pct = self.get_disk_usage()

        status = {
            "cpu_pct": round(cpu_pct, 2),
            "mem_pct": round(mem_pct, 2),
            "disk_pct": round(disk_pct, 2),
            "timestamp": datetime.utcnow().isoformat()
        }

        self.logger.info(f"Metrics tracked: CPU {status['cpu_pct']}% | RAM {status['mem_pct']}% | Disk {status['disk_pct']}%")

        if cpu_pct > self.config["cpu_threshold_pct"]:
            self.logger.warning(f"CRITICAL: CPU threshold exceeded: {status['cpu_pct']}%")
        if mem_pct > self.config["mem_threshold_pct"]:
            self.logger.warning(f"CRITICAL: RAM threshold exceeded: {status['mem_pct']}%")
        if disk_pct > self.config["disk_threshold_pct"]:
            self.logger.warning(f"CRITICAL: Disk threshold exceeded: {status['disk_pct']}%")

        return status

    def run_once(self):
        return self.check_thresholds()