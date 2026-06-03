import os
import sys
import time
import json
import sqlite3
import urllib.request
import urllib.error
from datetime import datetime

class SystemTelemetryDaemon:
    def __init__(self, config_path):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        self.db_path = self.config.get('db_path', 'telemetry.db')
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS telemetry (
                    timestamp TEXT PRIMARY KEY,
                    cpu_usage REAL,
                    ram_usage REAL,
                    disk_usage REAL
                )
            ''')
            conn.commit()

    def get_cpu_usage(self):
        try:
            with open('/proc/stat', 'r') as f:
                lines = f.readlines()
            for line in lines:
                if line.startswith('cpu '):
                    fields = [float(column) for column in line.strip().split()[1:]]
                    idle_time = fields[3] + fields[4]
                    total_time = sum(fields)
                    return idle_time, total_time
        except Exception:
            return 0.0, 1.0

    def calculate_cpu_percent(self, prev_idle, prev_total):
        idle, total = self.get_cpu_usage()
        idle_delta = idle - prev_idle
        total_delta = total - prev_total
        if total_delta == 0:
            return 0.0, idle, total
        cpu_pct = 100.0 * (1.0 - idle_delta / total_delta)
        return round(cpu_pct, 2), idle, total

    def get_ram_usage(self):
        try:
            meminfo = {}
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    parts = line.split(':')
                    if len(parts) == 2:
                        meminfo[parts[0].strip()] = int(parts[1].split()[0])
            total = meminfo.get('MemTotal', 1)
            free = meminfo.get('MemFree', 0)
            buffers = meminfo.get('Buffers', 0)
            cached = meminfo.get('Cached', 0)
            used = total - (free + buffers + cached)
            return round((used / total) * 100.0, 2)
        except Exception:
            return 0.0

    def get_disk_usage(self):
        try:
            stat = os.statvfs('/')
            total = stat.f_blocks * stat.f_frsize
            free = stat.f_bfree * stat.f_frsize
            used = total - free
            return round((used / total) * 100.0, 2)
        except Exception:
            return 0.0

    def record_metrics(self, cpu, ram, disk):
        timestamp = datetime.utcnow().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                'INSERT OR REPLACE INTO telemetry (timestamp, cpu_usage, ram_usage, disk_usage) VALUES (?, ?, ?, ?)',
                (timestamp, cpu, ram, disk)
            )
            conn.commit()
        self.prune_old_records()

    def prune_old_records(self):
        max_records = self.config.get('max_records', 10000)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                DELETE FROM telemetry WHERE timestamp NOT IN (
                    SELECT timestamp FROM telemetry ORDER BY timestamp DESC LIMIT ?
                )
            ''', (max_records,))
            conn.commit()

    def dispatch_alert(self, metric, value, threshold):
        payload = json.dumps({
            'alert': 'THRESHOLD_EXCEEDED',
            'metric': metric,
            'value': value,
            'threshold': threshold,
            'timestamp': datetime.utcnow().isoformat()
        }).encode('utf-8')
        webhook_url = self.config.get('webhook_url')
        if not webhook_url:
            return
        try:
            req = urllib.request.Request(
                webhook_url,
                data=payload,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                resp.read()
        except Exception as e:
            sys.stderr.write(f'Alert dispatch failed: {e}\n')

    def execute_evaluation_cycle(self, prev_idle, prev_total):
        cpu, next_idle, next_total = self.calculate_cpu_percent(prev_idle, prev_total)
        ram = self.get_ram_usage()
        disk = self.get_disk_usage()
        self.record_metrics(cpu, ram, disk)
        
        thresholds = self.config.get('thresholds', {})
        if cpu > thresholds.get('cpu', 90.0):
            self.dispatch_alert('cpu', cpu, thresholds.get('cpu'))
        if ram > thresholds.get('ram', 90.0):
            self.dispatch_alert('ram', ram, thresholds.get('ram'))
        if disk > thresholds.get('disk', 90.0):
            self.dispatch_alert('disk', disk, thresholds.get('disk'))
            
        return next_idle, next_total

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: daemon.py <config_path>')
        sys.exit(1)
    daemon = SystemTelemetryDaemon(sys.argv[1])
    idle, total = daemon.get_cpu_usage()
    interval = daemon.config.get('interval', 60)
    try:
        while True:
            time.sleep(interval)
            idle, total = daemon.execute_evaluation_cycle(idle, total)
    except KeyboardInterrupt:
        sys.exit(0)