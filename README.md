# sys-monitor-daemon

A lightweight, high-performance modular system monitoring daemon. Tracks CPU, memory, storage utilization, and network traffic interfaces, preserving time-series events inside a localized embedded SQLite persistence layer.

## Architecture

- **`src/daemon.py`**: Principal execution engine. Low resource footprint loop, graceful signal-based shutdown (SIGTERM/SIGINT), standard threshold verification alerts.
- **`config/config.json`**: Controls polling rates, thresholds, and target database parameters.
- **`tests/test_daemon.py`**: Isolated unit tests employing mock wrappers to validate logic, recovery, and interface structures.

## Usage

```bash
python3 src/daemon.py
```

## Running Tests

```bash
python3 -m unittest discover -s tests
```
