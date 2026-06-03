import sys
import json
import os

def display_metrics(state_file):
    if not os.path.exists(state_file):
        print(f"Error: State file not found at {state_file}. Daemon might not be running.")
        sys.exit(1)

    try:
        with open(state_file, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading state data: {e}")
        sys.exit(1)

    print("=" * 45)
    print(" SYSTEM MONITOR STATUS")
    print("=" * 45)
    print(f"Timestamp:       {data.get('timestamp')}")
    print(f"CPU Usage:       {data.get('cpu_usage_percent')}%")
    print(f"Memory Usage:    {data.get('memory_usage_percent')}%")
    print(f"Disk Usage:      {data.get('disk_usage_percent')}%")
    print(f"Network Sent:    {data.get('network_bytes_sent') / (1024*1024):.2f} MB")
    print(f"Network Recv:    {data.get('network_bytes_recv') / (1024*1024):.2f} MB")
    print("=" * 45)

if __name__ == "__main__":
    state_file = sys.argv[1] if len(sys.argv) > 1 else "/tmp/sys_monitor_state.json"
    display_metrics(state_file)