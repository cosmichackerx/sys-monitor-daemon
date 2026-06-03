import os
import sys
import time
import json
import signal
import logging
import psutil
from datetime import datetime

class SystemMonitorDaemon:
    def __init__(self, config_path):
        self.config_path = config_path
        self.running = True
        self.load_config()
        self.setup_logging()

    def load_config(self):
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
        except Exception:
            self.config = {
                "interval": 5,
                "log_file": "/tmp/sys_monitor.log",
                "state_file": "/tmp/sys_monitor_state.json",
                "thresholds": {
                    "cpu_percent": 80.0,
                    "memory_percent": 85.0,
                    "disk_percent": 90.0
                }
            }

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler(self.config.get("log_file", "/tmp/sys_monitor.log")),
                logging.StreamHandler(sys.stdout)
            ]
        )

    def handle_signal(self, signum, frame):
        logging.info(f"Signal {signum} received. Shutting down gracefully...")
        self.running = False

    def collect_metrics(self):
        cpu = psutil.cpu_percent(interval=None)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        net_io = psutil.net_io_counters()

        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "cpu_usage_percent": cpu,
            "memory_usage_percent": memory.percent,
            "disk_usage_percent": disk.percent,
            "network_bytes_sent": net_io.bytes_sent,
            "network_bytes_recv": net_io.bytes_recv
        }
        return metrics

    def check_thresholds(self, metrics):
        thresholds = self.config.get("thresholds", {})
        if metrics["cpu_usage_percent"] > thresholds.get("cpu_percent", 80.0):
            logging.warning(f"CPU threshold exceeded: {metrics['cpu_usage_percent']}%")
        if metrics["memory_usage_percent"] > thresholds.get("memory_percent", 85.0):
            logging.warning(f"Memory threshold exceeded: {metrics['memory_usage_percent']}%")
        if metrics["disk_usage_percent"] > thresholds.get("disk_percent", 90.0):
            logging.warning(f"Disk threshold exceeded: {metrics['disk_usage_percent']}%")

    def run(self):
        logging.info("Starting sys-monitor-daemon...")
        signal.signal(signal.SIGTERM, self.handle_signal)
        signal.signal(signal.SIGINT, self.handle_signal)
        psutil.cpu_percent(interval=None)

        while self.running:
            try:
                metrics = self.collect_metrics()
                logging.info(f"Collected Metrics: {json.dumps(metrics)}")
                self.check_thresholds(metrics)
                state_file = self.config.get("state_file", "/tmp/sys_monitor_state.json")
                with open(state_file, 'w') as f:
                    json.dump(metrics, f)
            except Exception as e:
                logging.error(f"Error during metrics collection: {str(e)}")
            time.sleep(self.config.get("interval", 5))

if __name__ == "__main__":
    config_file = sys.argv[1] if len(sys.argv) > 1 else "config/config.json"
    daemon = SystemMonitorDaemon(config_file)
    daemon.run()