import os
import sys
import time
import json
import sqlite3
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SystemMonitor:
    def __init__(self, db_path='data/metrics.db', interval=60):
        self.db_path = db_path
        self.interval = interval
        self.init_db()

    def init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                cpu_percent REAL,
                memory_percent REAL,
                disk_percent REAL
            )
        ''')
        conn.commit()
        conn.close()

    def get_metrics(self):
        # Read load average as CPU metric fallback without external dependencies
        try:
            load1, load5, load15 = os.getloadavg()
            cpu_percent = (load1 / os.cpu_count()) * 100.0
        except Exception:
            cpu_percent = 0.0

        # Read memory info from /proc/meminfo on Linux
        memory_percent = 0.0
        try:
            with open('/proc/meminfo', 'r') as f:
                lines = f.readlines()
            mem_total = 0
            mem_free = 0
            for line in lines:
                if 'MemTotal:' in line:
                    mem_total = int(line.split()[1])
                elif 'MemFree:' in line:
                    mem_free = int(line.split()[1])
            if mem_total > 0:
                memory_percent = ((mem_total - mem_free) / mem_total) * 100.0
        except Exception:
            memory_percent = 0.0

        # Read disk usage using os.statvfs
        disk_percent = 0.0
        try:
            stat = os.statvfs('/')
            total = stat.f_blocks * stat.f_frsize
            free = stat.f_bfree * stat.f_frsize
            if total > 0:
                disk_percent = ((total - free) / total) * 100.0
        except Exception:
            disk_percent = 0.0

        return cpu_percent, memory_percent, disk_percent

    def log_metrics(self, cpu, memory, disk):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO system_metrics (cpu_percent, memory_percent, disk_percent)
                VALUES (?, ?, ?)
            ''', (cpu, memory, disk))
            conn.commit()
            conn.close()
            logging.info(f'Logged metrics: CPU: {cpu:.2f}%, MEM: {memory:.2f}%, DISK: {disk:.2f}%')
        except Exception as e:
            logging.error(f'Failed to write metrics to DB: {e}')

    def run(self):
        logging.info('Starting system monitor daemon...')
        try:
            while True:
                cpu, memory, disk = self.get_metrics()
                self.log_metrics(cpu, memory, disk)
                time.sleep(self.interval)
        except KeyboardInterrupt:
            logging.info('Daemon stopped by user.')
        except Exception as e:
            logging.critical(f'Daemon encountered fatal error: {e}')

if __name__ == "__main__":
    monitor = SystemMonitor(interval=10)
    monitor.run()