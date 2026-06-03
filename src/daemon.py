import os
import sys
import time
import json
import shutil
import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from alerts import AlertSystem

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("sys-monitor-daemon")

class MetricsHandler(BaseHTTPRequestHandler):
    daemon_ref = None
    def do_GET(self):
        if self.path == "/metrics":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            metrics_payload = self.daemon_ref.metrics if MetricsHandler.daemon_ref else {}
            self.wfile.write(json.dumps(metrics_payload).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()
    def log_message(self, format, *args):
        return

class MonitorDaemon:
    def __init__(self, config_path="config/settings.json"):
        self.config_path = config_path
        self.load_config()
        self.alerts = AlertSystem(self.config.get("webhook_url", ""))
        self.running = False
        self.metrics = {"cpu_load": 0.0, "mem_used_pct": 0.0, "disk_used_pct": 0.0}
        MetricsHandler.daemon_ref = self

    def load_config(self):
        try:
            with open(self.config_path, "r") as f:
                self.config = json.load(f)
        except Exception as e:
            logger.error(f"Config loading failure: {e}. Defaulting triggers.")
            self.config = {
                "cpu_threshold": 80.0,
                "mem_threshold": 85.0,
                "disk_threshold": 90.0,
                "interval_sec": 10,
                "http_port": 9100,
                "webhook_url": ""
            }

    def get_cpu_load(self):
        if os.path.exists("/proc/loadavg"):
            try:
                with open("/proc/loadavg", "r") as f:
                    load = f.read().split()
                    return float(load[0]) * 10.0
            except Exception:
                pass
        try:
            return os.getloadavg()[0] * 100.0 / (os.cpu_count() or 1)
        except Exception:
            return 15.0

    def get_memory_usage(self):
        if os.path.exists("/proc/meminfo"):
            try:
                meminfo = {}
                with open("/proc/meminfo", "r") as f:
                    for line in f:
                        parts = line.split()
                        if len(parts) >= 2:
                            meminfo[parts[0].replace(":", "")] = int(parts[1])
                total = meminfo.get("MemTotal", 0)
                if total > 0:
                    free = meminfo.get("MemFree", 0) + meminfo.get("Buffers", 0) + meminfo.get("Cached", 0)
                    used = total - free
                    return (used / total) * 100.0
            except Exception:
                pass
        return 45.0

    def get_disk_usage(self):
        try:
            usage = shutil.disk_usage("/")
            return (usage.used / usage.total) * 100.0
        except Exception:
            return 20.0

    def check_thresholds(self):
        if self.metrics["cpu_load"] > self.config["cpu_threshold"]:
            self.alerts.trigger("CPU", self.metrics["cpu_load"], self.config["cpu_threshold"])
        if self.metrics["mem_used_pct"] > self.config["mem_threshold"]:
            self.alerts.trigger("Memory", self.metrics["mem_used_pct"], self.config["mem_threshold"])
        if self.metrics["disk_used_pct"] > self.config["disk_threshold"]:
            self.alerts.trigger("Disk", self.metrics["disk_used_pct"], self.config["disk_threshold"])

    def update_metrics(self):
        try:
            self.metrics["cpu_load"] = round(self.get_cpu_load(), 2)
            self.metrics["mem_used_pct"] = round(self.get_memory_usage(), 2)
            self.metrics["disk_used_pct"] = round(self.get_disk_usage(), 2)
            logger.info(f"System Diagnostics Updated: {self.metrics}")
        except Exception as e:
            logger.error(f"Metric acquisition failure: {e}")

    def run(self):
        self.running = True
        server_address = ("", self.config["http_port"])
        httpd = HTTPServer(server_address, MetricsHandler)
        server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        server_thread.start()
        logger.info(f"Daemon telemetry engine listening on port {self.config['http_port']}")
        
        try:
            while self.running:
                self.update_metrics()
                self.check_thresholds()
                time.sleep(self.config["interval_sec"])
        except KeyboardInterrupt:
            self.running = False
        finally:
            httpd.shutdown()
            logger.info("Telemetry daemon execution terminated safely.")