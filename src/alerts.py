import json
import urllib.request
import logging

logger = logging.getLogger("sys-monitor-daemon")

class AlertSystem:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    def trigger(self, resource, current_val, threshold):
        msg = f"[ALERT] {resource} utilization threshold breached: {current_val}% (Threshold: {threshold}%)"
        logger.warning(msg)
        if not self.webhook_url:
            return False

        payload = json.dumps({"text": msg}).encode("utf-8")
        req = urllib.request.Request(
            self.webhook_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Webhook dispatch failed: {e}")
            return False