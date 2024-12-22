# 🚀 **Proxmox Cluster Balancer**

## 📝 **Summary**

**Proxmox Cluster Balancer** is a Python-based tool designed to optimize resource utilization and maintain balance within your Proxmox virtual environment. It connects to multiple Proxmox hosts via SSH, monitors system and container load, gathers performance metrics, and suggests container migrations to ensure efficient resource allocation and optimal performance.

> [!IMPORTANT]
> This is a **Proof of Concept (PoC)** tool. It is intended solely for **reference purposes**, demonstration and as a starting point to compare or customize existing Proxmox scaling methods. The tool provides **suggestions only** and does **not automatically perform migrations** or enforce load balancing. Always validate its recommendations before making any changes to your production environment. It is crucial to understand the impacts of your configuration before implementing any change.

## 📂 **Project Structure**

```
.
├── config.py          # ⚙️ Loads and validates configuration from YAML
├── config.yaml        # 📝 YAML configuration file for the system
├── functions.py       # 🔗 Handles SSH connections and retrieves system/container metrics
├── logger.py          # 📋 Configures and provides logging capabilities
├── main.py            # 🚀 Main application script for balancing the proxmox cluster
├── sensors.py         # 📊 Monitors system/container metrics, checks against thresholds
├── triggers.py        # ⚡ Handles actions for alerts and container migrations
└── utils.py           # 🛠️ Contains general utility functions
```

## ✨ **Key Features**

- **🔒 Secure SSH Connectivity:** Establishes secure connections to Proxmox hosts using `paramiko` to collect real-time metrics and execute commands.
- **📊 Comprehensive Metrics Collection:** Gathers host and container-level metrics, including CPU load, memory usage, disk usage, and network activity, using Linux system commands.
- **📈 Dynamic Load Monitoring:** Continuously monitors system loads, identifies potential performance bottlenecks, and stores the results for better decision-making.
- **🚨 Configurable Alerts:** Triggers alerts when critical metrics exceed predefined safety thresholds. The tool provides a flexible structure, so it can be extended to support multiple notification channels like email, Slack, or SMS.
- **🔄 Intelligent Migration Suggestions:** Analyzes collected data, identifies overloaded hosts, evaluates potential target hosts, and recommends container migrations to optimize load distribution across the cluster.
- **🧰 Extensible and Modular:** The code is designed with a modular approach, which allows for easy extension of functionality.

## 🔍 **Modules Details**

### `config.py`
This module is responsible for loading the configuration from the `config.yaml` file, validating the structure using the `schema` library, and applying defaults and environment variable overrides. This module is used for setting up the base configuration of the whole tool.

### `functions.py`
This module handles SSH connections to Proxmox hosts using the `paramiko` library. It also includes functions for collecting host and container-level metrics via SSH and Linux system commands, also provides an `SSHClient` class to encapsulate SSH connection related logic.

### `logger.py`
This module sets up the logging system for the application, using Python's `logging` module. It provides console and file logging with configurable log levels and formats.

### `main.py`
This module is the main entry point for the application. It orchestrates the different modules, connecting to Proxmox hosts, collecting metrics, checking thresholds, and generating migration suggestions, it uses `asyncio` to improve performance.

### `sensors.py`
This module is responsible for monitoring system and container metrics. It checks metrics against configured thresholds, returning `True` if the thresholds are exceeded, also provides helper methods to fetch metrics, and uses the `SSHClient` to run the commands in the Proxmox hosts.

### `triggers.py`
This module provides actions that are triggered based on monitored events. Currently it includes `send_alert` for sending notifications and `trigger_migration` for initiating container migrations, also uses the `SSHClient` to run the commands in the Proxmox hosts.

### `utils.py`
This module contains general utility functions used across the project. Currently empty, but can be used for any future generic functionality.

## 📝 **Configuration**

The system is configured using the `config.yaml` file, which contains all the necessary parameters for managing and monitoring your Proxmox cluster.

### ⚙️ **Sample Configuration**

```yaml
proxmox_hosts:
  - name: proxmox1
    address: 192.168.5.1   # IP Address or hostname of the Proxmox server.
    user: root            # Username for SSH access.
    password: password    # Password for SSH access (use key_path for key-based auth).
    key_path: # /path/to/your/private/key # Optional: Path to your private SSH key for key-based authentication.
    cpu_threshold: 2.0     # CPU load threshold as a fraction (e.g., 2.0 = 200%). If not set, the global threshold will be used.
    memory_threshold: 0.8  # Memory usage threshold as a fraction (e.g., 0.8 = 80%). If not set, the global threshold will be used.

  - name: proxmox2
    address: 192.168.5.2
    user: root
    password: password
    key_path: # /path/to/your/private/key # Optional: Path to your private SSH key for key-based authentication.
    cpu_threshold: 0.9
    memory_threshold: 0.7

default_params:
  cpu_threshold: 1.0  # Default CPU load threshold. If host has its own defined it will be used.
  memory_threshold: 0.8 # Default memory usage threshold. If host has its own defined it will be used.
  migration_strategy: load_based # Strategy for migration (e.g., 'load_based').

  # --- Scoring Parameters ---
  # Weights used for calculating balance scores and suitability scores.
  balance_score_cpu_weight: 0.7   # Weight for CPU load in the balance score calculation.
  balance_score_memory_weight: 0.3 # Weight for memory usage in the balance score calculation.

  migration_memory_weight: 30     # Weight for available memory in migration suitability score calculation.
  migration_core_weight: 30       # Weight for available CPU cores in migration suitability score calculation.
  migration_balance_weight: 40    # Weight for balance score improvement in migration suitability score calculation.
  max_migration_suitability_score: 100 # Maximum score a suitability can achieve.
```
### Configuration Parameters Explained

-   **`proxmox_hosts`**: This section contains a list of Proxmox hosts to be monitored. Each host definition requires:
    -   `name`: A unique identifier for the Proxmox host.
    -   `address`: The IP address or hostname of the Proxmox server.
    -   `user`: The username used to connect via SSH (usually `root`).
    -   `password`: The password for the user.  It is highly recommended to use key-based authentication instead of password.
    -   `key_path` (Optional): Path to your private SSH key file for key-based authentication.
    -   `cpu_threshold`: The threshold for CPU load (as a fraction). If not set, the default threshold will be used.
    -   `memory_threshold`: The threshold for memory usage (as a fraction). If not set, the default threshold will be used.

-   **`default_params`**: This section defines default parameters for the system:
    -   `cpu_threshold`: The default threshold for CPU load (as a fraction).
    -   `memory_threshold`: The default threshold for memory usage (as a fraction).
    -    `migration_strategy`: The strategy used to balance the load in the system (currently always `load_based`).
    -   `balance_score_cpu_weight`: The weight given to the CPU load when calculating the balance score of a host (between 0 and 1, used on `calculate_balance_score`)
    -   `balance_score_memory_weight`: The weight given to the memory usage when calculating the balance score of a host (between 0 and 1, used on `calculate_balance_score`).
    -   `migration_memory_weight`: The weight given to the available memory when evaluating a target host for a migration.
    -   `migration_core_weight`: The weight given to the available CPU cores when evaluating a target host for a migration.
    -   `migration_balance_weight`: The weight given to the balance score improvement when evaluating a target host for a migration.
    -   `max_migration_suitability_score`: The maximum score that a host can achieve when evaluating for a migration target.

### Environment Variables

It is possible to override the configuration parameters via environment variables with the following naming:

-   `PROXMOX_<HOSTNAME>_<CONFIG_KEY>`: For overriding specific configurations of each Proxmox host (e.g.: `export PROXMOX_PROXMOX1_CPU_THRESHOLD=1.2`).
-   `PROXMOX_DEFAULT_<CONFIG_KEY>`: For overriding specific `default_params` values (e.g.: `export PROXMOX_DEFAULT_CPU_THRESHOLD=1.2`).

## 🛠️ **How to Use**

1.  **📦 Install Dependencies:** Ensure all required Python libraries are installed using `pip install -r requirements.txt`. The `requirements.txt` file should include:
    ```
    PyYAML
    paramiko
    schema
    colorama
    ```
2.  **📝 Configure Settings:** Update the `config.yaml` file with your Proxmox environment details.
3.  **▶️ Run the Application:** Execute `python main.py` to start monitoring your Proxmox environment and receive real-time optimization suggestions.
4.  **📄 Review Logs:** Check the generated `proxmox_balancer.log` file for detailed logs, or the console for a real-time overview.

## 🌟 **Advantages**

-   **Automated Load Balancing Suggestions:** Reduces manual intervention with intelligent container migration suggestions, optimizing resource allocation across the cluster.
-   **Proactive Monitoring:** Provides real-time alerts before performance issues escalate, ensuring high availability and reliability.
-   **Flexible Configuration:** Easily customizable monitoring thresholds, scoring parameters, and migration strategies to fit your needs.
-   **Modular Design:** The codebase is designed for extensibility, allowing the addition of new features and support for other notification systems.
-   **Open Source:** The project is open source, allowing users to make modifications to suit their needs.

## 📬 **Feedback and Contributions**

We welcome feedback and contributions! If you encounter any issues or have suggestions for improvement, feel free to open an issue or submit a pull request on our [GitHub repository](https://github.com/yourusername/yourrepository).

## 📜 **License**

This project is licensed under the MIT License, which allows for reuse and modification as long as the original authors are credited.
