# Proxmox Cluster Balancer

## Overview
The Cluster Manager is a Python-based tool designed to monitor and manage Proxmox virtual environments. It connects to multiple Proxmox hosts, retrieves various system and container metrics, and determines whether container migrations are necessary to balance the system load.

## Project Structure
```
.
├── config.py          # Configuration loading module
├── config.yaml        # YAML configuration file
├── functions.py       # Utility functions for SSH connections and metrics retrieval
├── logger.py          # Logging setup module
├── main.py            # Main script, entry point of the application
├── sensors.py         # Functions that monitor and check system metrics
├── triggers.py        # Functions that trigger actions based on monitored metrics
└── utils.py           # Utility functions, e.g., for formatting metrics
```

## Features
- **SSH Connectivity:** Establishes secure connections to Proxmox hosts to gather metrics.
- **Metrics Collection:** Retrieves and processes host and container-level metrics such as CPU load, memory usage, disk space, and network usage.
- **Load Monitoring:** Monitors system load using sensor functions to determine if the system exceeds predefined thresholds.
- **Automated Alerts:** Sends alerts when system metrics exceed safe operational thresholds.
- **Container Migration Suggestions:** Analyzes the collected metrics to suggest container migrations for load balancing.

## Sensors
The `sensors.py` module contains functions that monitor system metrics:
- `check_cpu_load`: Verifies if CPU load exceeds a threshold.
- `check_memory_usage`: Checks if memory usage exceeds a threshold.
- `get_container_cpu_load`: Fetches and checks CPU load for specific containers.
- `get_container_memory_usage`: Fetches and checks memory usage for specific containers.

These functions are used throughout the system to ensure the environment remains within optimal operational limits.

## Triggers
The `triggers.py` module provides functions to trigger specific actions based on monitored metrics:
- `send_alert`: Sends notifications when thresholds are breached.
- `trigger_migration`: Initiates a container migration to balance the load between hosts.

These triggers ensure that the system can react appropriately to monitored events.

## Configuration
The system is configured via the `config.yaml` file, which includes:
- **Proxmox Hosts:** Definitions of the Proxmox servers, their credentials, and thresholds.
- **Default Parameters:** Default thresholds for CPU and memory usage and migration strategies.

## How to Use
1. **Install Dependencies:** Ensure that all required Python libraries (listed in `requirements.txt`) are installed.
2. **Configure Settings:** Modify the `config.yaml` file to match your environment.
3. **Run the Application:** Execute `main.py` to start monitoring your Proxmox environment.

## Future Improvements
- Integration of real-time alerting mechanisms (e.g., via email or Slack).
- Automation of container migration based on suggestions.

## License
This project is licensed under the MIT License.
