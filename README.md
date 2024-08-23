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

### `main.py` explained

The `main.py` script is the central part of the Cluster Manager system. It orchestrates the workflow of connecting to Proxmox hosts, gathering metrics, checking system loads, and suggesting possible migrations to balance the load across the hosts.

Here's a step-by-step breakdown of how `main.py` works:

#### 1. **Importing Required Modules**
```python
from logger import setup_logging
from config import load_config
from functions import ssh_connect, get_host_metrics, get_container_metrics, get_container_config
from sensors import check_cpu_load, check_memory_usage
from triggers import send_alert
from utils import format_metrics_for_logging
import logging
from colorama import init, Fore, Style
```
- **Purpose:** Import necessary functions and libraries that will be used throughout the script. 
  - `setup_logging`: Configures logging.
  - `load_config`: Loads the configuration from a YAML file.
  - `ssh_connect`, `get_host_metrics`, `get_container_metrics`, `get_container_config`: Functions for SSH operations and metrics retrieval.
  - `check_cpu_load`, `check_memory_usage`: Sensor functions that monitor CPU and memory usage.
  - `send_alert`: Trigger function that sends alerts.
  - `format_metrics_for_logging`: Utility function for formatting metrics for logging.
  - `logging`, `colorama`: Libraries for logging and text formatting.

#### 2. **Suppressing Paramiko Logs**
```python
logging.getLogger("paramiko").setLevel(logging.WARNING)
```
- **Purpose:** Suppresses the verbose logging from the Paramiko SSH library, focusing the logs only on warnings and errors, making the output more readable.

#### 3. **Defining Helper Functions**
- **Function: `can_migrate`**
  ```python
  def can_migrate(container_metrics, target_host_metrics):
      ...
  ```
  - **Purpose:** Determines whether a container can be migrated to a target host based on the container's resource requirements (CPU and memory) and the available resources on the target host.

- **Function: `suggest_migrations`**
  ```python
  def suggest_migrations(hosts_metrics, default_params):
      ...
  ```
  - **Purpose:** Analyzes the collected metrics from all hosts and suggests container migrations to balance the load. This is done by evaluating which hosts are overloaded and finding suitable target hosts for the containers running on them.

#### 4. **Main Function Execution**
```python
def main():
    logger = setup_logging()
    config = load_config('config.yaml')
    default_params = config.get('default_params', {})

    hosts_metrics = {}
    ...
    migration_suggestions = suggest_migrations(hosts_metrics, default_params)
    ...
```
- **Purpose:** This is the main function where the overall workflow is executed.

1. **Setup Logging:**
   ```python
   logger = setup_logging()
   ```
   - Initializes the logging system to capture information, warnings, and errors during the execution.

2. **Load Configuration:**
   ```python
   config = load_config('config.yaml')
   default_params = config.get('default_params', {})
   ```
   - Loads the configuration file (`config.yaml`), which contains details about the Proxmox hosts, thresholds, and other parameters.
   - Retrieves default parameters, such as CPU and memory thresholds, from the configuration.

3. **Initialize Hosts Metrics Dictionary:**
   ```python
   hosts_metrics = {}
   ```
   - Prepares an empty dictionary to store metrics for each host.

4. **Iterate Over Hosts:**
   ```python
   for host in config['proxmox_hosts']:
       ...
   ```
   - Loops through each Proxmox host defined in the configuration file.

5. **Connect to Each Host:**
   ```python
   ssh = ssh_connect(host['address'], host['user'], password=host.get('password'), key_path=host.get('key_path'))
   ```
   - Establishes an SSH connection to the current host using credentials and key path provided in the configuration.

6. **Fetch and Log Host Metrics:**
   ```python
   host_metrics = get_host_metrics(ssh)
   ...
   logger.info(f"🔍 Host metrics for {host['name']}: {format_metrics_for_logging(host_metrics)}")
   ```
   - Retrieves the metrics (CPU, memory, disk usage, etc.) from the host.
   - Logs these metrics in a readable format.

7. **Check Thresholds Using Sensors:**
   ```python
   if check_cpu_load(host_metrics['cpu'], host_metrics['cpu_threshold']):
       ...
   if check_memory_usage(host_metrics['memory']):
       ...
   ```
   - Uses sensor functions to check if the host's CPU load or memory usage exceeds the defined thresholds.
   - If thresholds are exceeded, alerts are printed to the console.

8. **Close SSH Connection:**
   ```python
   if ssh:
       ssh.close()
   ```
   - Ensures that the SSH connection to the host is closed after all operations are completed.

9. **Suggest Migrations:**
   ```python
   migration_suggestions = suggest_migrations(hosts_metrics, default_params)
   ```
   - Analyzes all the collected metrics and suggests container migrations to balance the load between hosts.

10. **Log Migration Suggestions:**
   ```python
   for suggestion in migration_suggestions:
       logger.info(f"🔄 Suggesting to migrate container {suggestion['container_id']} from {suggestion['source_host']} to {suggestion['target_host']}")
   ```
   - Logs each migration suggestion with detailed information about which container should be moved and why.

#### 5. **Execution Entry Point**
```python
if __name__ == "__main__":
    main()
```
- **Purpose:** Ensures that the `main()` function is executed when the script is run directly (not when imported as a module).


## License
This project is licensed under the MIT License.
