import os
import sys
import time
import json
import sqlite3
import signal
import psutil
from datetime import datetime

class SysMonitorDaemon:
    def __init__(self, config_path="config/config.json"):
        self.config_path = config_path
        self.running = True
        self.load_config()
        self.init_db()
        signal.signal(signal.SIGINT, self.handle_exit)
        signal.signal(signal.SIGTERM, self.handle_exit)

    def load_config(self):
        try:
            with open(self.config_path, "r") as f:
                self.config = json.load(f)
        except Exception:
            self.config = {
                "interval_seconds": 10,
                "db_path": "data/metrics.db",
                "thresholds": {
                    "cpu_percent": 85.0,
                    "memory_percent": 90.0
                }
            }
        os.makedirs(os.path.dirname(self.config["db_path"]), exist_ok=True)

    def init_db(self):
        conn = sqlite3.connect(self.config["db_path"])
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                cpu_usage REAL,
                memory_usage REAL,
                disk_usage REAL,
                net_sent INTEGER,
                net_recv INTEGER
            )
        """)
        conn.commit()
        conn.close()

    def handle_exit(self, signum, frame):
        self.running = False

    def collect_metrics(self):
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory().percent
        disk = psutil.disk_usage("/").percent
        net = psutil.net_io_counters()
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "cpu_usage": cpu,
            "memory_usage": mem,
            "disk_usage": disk,
            "net_sent": net.bytes_sent,
            "net_recv": net.bytes_recv
        }

    def save_metrics(self, metrics):
        conn = sqlite3.connect(self.config["db_path"])
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO metrics (timestamp, cpu_usage, memory_usage, disk_usage, net_sent, net_recv)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            metrics["timestamp"],
            metrics["cpu_usage"],
            metrics["memory_usage"],
            metrics["disk_usage"],
            metrics["net_sent"],
            metrics["net_recv"]
        ))
        conn.commit()
        conn.close()

    def check_thresholds(self, metrics):
        if metrics["cpu_usage"] > self.config["thresholds"]["cpu_percent"]:
            sys.stderr.write(f"[WARN] CPU usage high: {metrics['cpu_usage']}%\n")
        if metrics["memory_usage"] > self.config["thresholds"]["memory_percent"]:
            sys.stderr.write(f"[WARN] Memory usage high: {metrics['memory_usage']}%\n")

    def run(self):
        while self.running:
            try:
                metrics = self.collect_metrics()
                self.save_metrics(metrics)
                self.check_thresholds(metrics)
                time.sleep(self.config["interval_seconds"])
            except Exception as e:
                sys.stderr.write(f"[ERROR] Daemon loop error: {str(e)}\n")
                time.sleep(1)

if __name__ == "__main__":
    daemon = SysMonitorDaemon()
    daemon.run()