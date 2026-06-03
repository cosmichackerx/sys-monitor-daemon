import os
import sys
import json
import time
import logging
from datetime import datetime

class SystemMonitorDaemon:
    def __init__(self, config_path="config/settings.json"):
        self.config_path = config_path
        self.config = self.load_config()
        self.setup_logging()

    def load_config(self):
        default_config = {
            "interval_seconds": 10,
            "thresholds": {"cpu_percent": 80.0, "memory_percent": 85.0, "disk_percent": 90.0},
            "log_file": "sys_monitor.log",
            "report_path": "metrics_report.json"
        }
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    return json.load(f)
            except Exception:
                return default_config
        return default_config

    def setup_logging(self):
        logging.basicConfig(
            filename=self.config.get("log_file", "sys_monitor.log"),
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s"
        )
        self.logger = logging.getLogger("sys_monitor")

    def get_metrics(self):
        metrics = {
            "cpu_percent": 0.0,
            "memory_percent": 0.0,
            "disk_percent": 0.0,
            "timestamp": datetime.utcnow().isoformat()
        }
        try:
            if hasattr(os, "getloadavg"):
                cores = os.cpu_count() or 1
                metrics["cpu_percent"] = min(100.0, (os.getloadavg()[0] / cores) * 100.0)
            else:
                metrics["cpu_percent"] = 15.0

            if os.path.exists("/proc/meminfo"):
                with open("/proc/meminfo", "r") as f:
                    meminfo = f.readlines()
                mem_total = 1
                mem_free = 0
                for line in meminfo:
                    if "MemTotal" in line:
                        mem_total = int(line.split()[1])
                    elif "MemFree" in line:
                        mem_free = int(line.split()[1])
                metrics["memory_percent"] = ((mem_total - mem_free) / mem_total) * 100.0
            else:
                metrics["memory_percent"] = 40.0

            if hasattr(os, "statvfs"):
                stat = os.statvfs("/")
                free = stat.f_bavail * stat.f_frsize
                total = stat.f_blocks * stat.f_frsize
                metrics["disk_percent"] = ((total - free) / total) * 100.0
            else:
                metrics["disk_percent"] = 50.0

        except Exception as e:
            self.logger.error(f"Error gathering system metrics: {str(e)}")
        
        return metrics

    def check_thresholds(self, metrics):
        thresholds = self.config.get("thresholds", {})
        alerts = []
        for metric, val in thresholds.items():
            if metric in metrics and metrics[metric] > val:
                alerts.append(f"Threshold breached: {metric} is {metrics[metric]:.2f}% (Limit: {val}%)")
        return alerts

    def write_report(self, metrics):
        report_path = self.config.get("report_path", "metrics_report.json")
        try:
            with open(report_path, "w") as f:
                json.dump(metrics, f, indent=4)
        except Exception as e:
            self.logger.error(f"Failed to write report payload: {str(e)}")

    def run_cycle(self):
        metrics = self.get_metrics()
        alerts = self.check_thresholds(metrics)
        for alert in alerts:
            self.logger.warning(alert)
        self.write_report(metrics)
        return metrics, alerts

if __name__ == "__main__":
    monitor = SystemMonitorDaemon()
    monitor.logger.info("Initializing background monitoring telemetry loop.")
    try:
        while True:
            monitor.run_cycle()
            time.sleep(monitor.config.get("interval_seconds", 10))
    except KeyboardInterrupt:
        monitor.logger.info("Termination sequence initiated. Exiting loop.")