import os
import sys
import time
import json
import signal
import logging
import urllib.request
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

class SystemMonitor:
    def __init__(self, config_path):
        self.config_path = config_path
        self.config = self.load_config()
        self.running = True
        self.last_cpu_idle = 0
        self.last_cpu_total = 0

    def load_config(self):
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Failed to load config: {e}. Using defaults.")
            return {
                "interval_seconds": 10,
                "thresholds": {
                    "cpu_percent": 85.0,
                    "memory_percent": 90.0,
                    "disk_percent": 95.0
                },
                "webhook_url": ""
            }

    def get_cpu_usage(self):
        try:
            with open('/proc/stat', 'r') as f:
                line = f.readline()
            parts = line.split()
            if len(parts) < 5:
                return 0.0
            cpu_ticks = [int(x) for x in parts[1:5]]
            idle = cpu_ticks[3]
            total = sum(cpu_ticks)
            
            diff_idle = idle - self.last_cpu_idle
            diff_total = total - self.last_cpu_total
            
            self.last_cpu_idle = idle
            self.last_cpu_total = total
            
            if diff_total == 0:
                return 0.0
            return round((1.0 - (diff_idle / diff_total)) * 100.0, 2)
        except FileNotFoundError:
            return 0.0

    def get_memory_usage(self):
        try:
            meminfo = {}
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 2:
                        key = parts[0].replace(':', '')
                        val = int(parts[1])
                        meminfo[key] = val
            total = meminfo.get('MemTotal', 1)
            free = meminfo.get('MemFree', 0)
            buffers = meminfo.get('Buffers', 0)
            cached = meminfo.get('Cached', 0)
            used = total - (free + buffers + cached)
            return round((used / total) * 100.0, 2)
        except FileNotFoundError:
            return 0.0

    def get_disk_usage(self):
        try:
            stat = os.statvfs('/')
            total = stat.f_blocks * stat.f_frsize
            free = stat.f_bfree * stat.f_frsize
            used = total - free
            if total == 0:
                return 0.0
            return round((used / total) * 100.0, 2)
        except Exception:
            return 0.0

    def send_alert(self, metric, value, threshold):
        payload = {
            "timestamp": datetime.utcnow().isoformat() + 'Z',
            "alert": True,
            "metric": metric,
            "value": value,
            "threshold": threshold,
            "message": f"Threshold breached: {metric} is {value}% (Limit: {threshold}%)"
        }
        logging.warning(payload["message"])
        url = self.config.get("webhook_url")
        if not url:
            return
        try:
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=5) as response:
                response.read()
        except Exception as e:
            logging.error(f"Failed to deliver webhook alert: {e}")

    def cycle(self):
        cpu = self.get_cpu_usage()
        mem = self.get_memory_usage()
        disk = self.get_disk_usage()

        limits = self.config.get("thresholds", {})
        
        logging.info(f"Metrics captured -> CPU: {cpu}%, MEM: {mem}%, DISK: {disk}%")

        if cpu > limits.get("cpu_percent", 85.0):
            self.send_alert("cpu_percent", cpu, limits.get("cpu_percent"))
        if mem > limits.get("memory_percent", 90.0):
            self.send_alert("memory_percent", mem, limits.get("memory_percent"))
        if disk > limits.get("disk_percent", 95.0):
            self.send_alert("disk_percent", disk, limits.get("disk_percent"))

    def shutdown(self, signum, frame):
        logging.info("Termination signal received. Shutting down system daemon.")
        self.running = False

if __name__ == '__main__':
    config_file = sys.argv[1] if len(sys.argv) > 1 else 'config/monitor_rules.json'
    monitor = SystemMonitor(config_file)
    signal.signal(signal.SIGINT, monitor.shutdown)
    signal.signal(signal.SIGTERM, monitor.shutdown)
    
    logging.info("System Monitor Daemon successfully initiated.")
    while monitor.running:
        monitor.cycle()
        time.sleep(monitor.config.get("interval_seconds", 10))