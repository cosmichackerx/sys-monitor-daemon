# System Telemetry Monitor Daemon

A zero-dependency, ultra-lightweight Linux telemetry daemon utilizing the `/proc` virtual filesystem and native SQLite persistence to maintain resource usage data with self-pruning cycles. Designed for minimal footprint deployment within strict security profiles.

## Architecture

- **Engine**: Decoupled asynchronous polling loops reading `/proc/stat`, `/proc/meminfo`, and active standard system calls.
- **Storage**: Local SQL database with automatic execution log rotation.
- **Alerts**: Simple HTTP request webhook integrations triggered instantly on metric boundary violations.

## Setup

```bash
# Run validation tests
python3 -m unittest tests/test_daemon.py

# Execution command
python3 src/daemon.py config/sys-monitor.json
```