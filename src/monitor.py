import os
import sys
import time
import sqlite3
import shutil
import json
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

class SystemMonitor:
    def __init__(self, db_path="metrics.db", interval=60):
        self.db_path = db_path
        self.interval = interval
        self.init_db()

    def init_db(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS system_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        load_1m REAL,
                        load_5m REAL,
                        load_15m REAL,
                        disk_total INTEGER,
                        disk_used INTEGER,
                        disk_free INTEGER,
                        memory_percent REAL
                    )
                """)
                conn.commit()
                logging.info("Database initialized successfully.")
        except Exception as e:
            logging.error(f"Failed to initialize database: {e}")
            sys.exit(1)

    def get_load_average(self):
        try:
            return os.getloadavg()
        except AttributeError:
            return (0.0, 0.0, 0.0)

    def get_disk_metrics(self):
        try:
            total, used, free = shutil.disk_usage("/")
            return total, used, free
        except Exception as e:
            logging.error(f"Error retrieving disk metrics: {e}")
            return (0, 0, 0)

    def get_memory_metrics(self):
        if sys.platform.startswith('linux'):
            try:
                with open('/proc/meminfo', 'r') as f:
                    meminfo = {}
                    for line in f:
                        parts = line.split()
                        if len(parts) >= 2:
                            meminfo[parts[0].rstrip(':')] = int(parts[1])
                total = meminfo.get('MemTotal', 0)
                free = meminfo.get('MemFree', 0)
                buffers = meminfo.get('Buffers', 0)
                cached = meminfo.get('Cached', 0)
                if total > 0:
                    used = total - (free + buffers + cached)
                    return round((used / total) * 100, 2)
            except Exception as e:
                logging.error(f"Error parsing /proc/meminfo: {e}")
        return 0.0

    def collect_metrics(self):
        load_1m, load_5m, load_15m = self.get_load_average()
        disk_total, disk_used, disk_free = self.get_disk_metrics()
        memory_percent = self.get_memory_metrics()

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO system_metrics (load_1m, load_5m, load_15m, disk_total, disk_used, disk_free, memory_percent)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (load_1m, load_5m, load_15m, disk_total, disk_used, disk_free, memory_percent))
                conn.commit()
                logging.info(f"Recorded metrics: Load={load_1m}, Mem={memory_percent}%, DiskFree={disk_free // (1024**2)}MB")
        except Exception as e:
            logging.error(f"Failed to record metrics: {e}")

    def run(self):
        logging.info("Starting System Monitor Daemon loop.")
        try:
            while True:
                self.collect_metrics()
                time.sleep(self.interval)
        except KeyboardInterrupt:
            logging.info("Daemon stopped by user.")
        except Exception as e:
            logging.critical(f"Unexpected error in run loop: {e}")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Lightweight System Monitor Daemon")
    parser.add_argument("--config", default="config/settings.json", help="Path to configuration file")
    args = parser.parse_args()

    interval = 60
    db_path = "metrics.db"
    if os.path.exists(args.config):
        try:
            with open(args.config, 'r') as f:
                config = json.load(f)
                interval = config.get("interval", interval)
                db_path = config.get("db_path", db_path)
        except Exception as e:
            logging.error(f"Error reading config: {e}")

    monitor = SystemMonitor(db_path=db_path, interval=interval)
    monitor.run()