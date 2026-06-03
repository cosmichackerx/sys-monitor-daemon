import pytest
import os
import json
from src.daemon import SystemMonitorDaemon

@pytest.fixture
def mock_config(tmp_path):
    cfg_file = tmp_path / "settings.json"
    cfg_data = {
        "interval_seconds": 1,
        "thresholds": {"cpu_percent": 10.0, "memory_percent": 10.0, "disk_percent": 10.0},
        "log_file": str(tmp_path / "sys_monitor.log"),
        "report_path": str(tmp_path / "metrics_report.json")
    }
    with open(cfg_file, "w") as f:
        json.dump(cfg_data, f)
    return str(cfg_file)

def test_config_loader(mock_config):
    daemon = SystemMonitorDaemon(config_path=mock_config)
    assert daemon.config["interval_seconds"] == 1
    assert daemon.config["thresholds"]["cpu_percent"] == 10.0

def test_metrics_evaluation_and_alerts(mock_config):
    daemon = SystemMonitorDaemon(config_path=mock_config)
    metrics = {
        "cpu_percent": 95.0,
        "memory_percent": 8.0,
        "disk_percent": 45.0
    }
    alerts = daemon.check_thresholds(metrics)
    assert len(alerts) == 2
    assert any("cpu_percent" in a for a in alerts)
    assert any("disk_percent" in a for a in alerts)

def test_write_report(mock_config):
    daemon = SystemMonitorDaemon(config_path=mock_config)
    metrics = {
        "cpu_percent": 50.0,
        "memory_percent": 50.0,
        "disk_percent": 50.0,
        "timestamp": "2026-06-03T12:00:00"
    }
    daemon.write_report(metrics)
    assert os.path.exists(daemon.config["report_path"])
    with open(daemon.config["report_path"], "r") as f:
        data = json.load(f)
    assert data["cpu_percent"] == 50.0