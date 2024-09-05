# 🚀 **Proxmox Cluster Balancer**

## 📝 **Summary**
**Proxmox Cluster Balancer** is a Python-based tool designed to optimize and maintain balance in your Proxmox virtual environments. It connects to multiple Proxmox hosts, monitors system load, collects performance metrics, and suggests container migrations to ensure efficient resource allocation and maintain optimal performance.

> [!IMPORTANT]
> This is a **Proof of Concept (PoC)** tool. It is intended solely for **reference purposes** to compare or customize existing Proxmox scaling methods. The tool provides **suggestions only** and does **not automatically perform migrations** or enforce load balancing. Always validate its recommendations before making any changes to your production environment.

## 📂 **Project Structure**
```
.
├── config.py          # 🔧 Loads configuration from YAML
├── config.yaml        # 📝 Configuration file for the system
├── functions.py       # 🔗 SSH connections and metrics retrieval functions
├── logger.py          # 📋 Logging setup module
├── main.py            # 🚀 Main application script
├── sensors.py         # 📊 Monitors and checks system metrics
├── triggers.py        # ⚡ Initiates actions based on monitored metrics
└── utils.py           # 🛠️ General utility functions (e.g., formatting)
```

## ✨ **Key Features**
- **🔒 Secure SSH Connectivity:** Establishes secure connections to Proxmox hosts to collect real-time metrics.
- **📊 Comprehensive Metrics Collection:** Gathers host and container-level metrics such as CPU load, memory usage, disk space, and network activity.
- **📈 Dynamic Load Monitoring:** Utilizes sensor functions to continuously monitor system loads and identify potential performance bottlenecks.
- **🚨 Automated Alerts:** Notifies administrators when critical metrics exceed predefined safety thresholds.
- **🔄 Intelligent Migration Suggestions:** Analyzes collected data to recommend container migrations, optimizing load distribution across the cluster.

## 🔍 **Sensors**
The `sensors.py` module is responsible for monitoring system metrics:
- `check_cpu_load`: Checks if the CPU load on a host exceeds a specified threshold.
- `check_memory_usage`: Evaluates memory usage to ensure it stays within safe limits.
- `get_container_cpu_load`: Retrieves and assesses CPU load for individual containers.
- `get_container_memory_usage`: Retrieves and checks memory usage for specific containers.

These functions help maintain the environment within defined operational limits, avoiding resource saturation and performance degradation.

## ⚙️ **Triggers**
The `triggers.py` module provides actions that are automatically triggered based on monitored events:
- `send_alert`: Sends notifications (email, SMS, etc.) when thresholds are breached to alert the administrators.
- `trigger_migration`: Automatically initiates container migrations to balance the load between Proxmox hosts.

These triggers enable a proactive response to any potential performance issues detected during monitoring.

## 🔧 **Configuration**
The system is configured using the `config.yaml` file, which contains all the necessary parameters for managing and monitoring your Proxmox cluster.

### 📝 **Sample Configuration**
```yaml
proxmox_hosts:
  - name: proxmox1
    address: 192.168.5.1
    user: root
    password: password
    key_path: # Optional, if using key-based authentication
    cpu_threshold: 2.0
    memory_threshold: 0.8
  - name: proxmox2
    address: 192.168.5.2
    user: root
    password: password
    key_path: # Optional, if using key-based authentication
    cpu_threshold: 0.9
    memory_threshold: 0.7

default_params:
  cpu_threshold: 1.0
  memory_threshold: 0.8
  migration_strategy: load_based
```

- **Proxmox Hosts:** List of all Proxmox servers with their addresses, credentials, and threshold settings.
- **Default Parameters:** Global thresholds for CPU and memory usage, and a strategy (`load_based`) for triggering migrations.

## 🛠️ **How to Use**
1. **📦 Install Dependencies:** Ensure all required Python libraries (as listed in `requirements.txt`) are installed.
2. **📝 Configure Settings:** Update the `config.yaml` file with your Proxmox environment details.
3. **▶️ Run the Application:** Execute `main.py` to start monitoring your Proxmox environment and receive real-time optimization suggestions.

## 🌟 **Advantages**
- **Automated Load Balancing Suggestions:** Minimize manual intervention with smart container migration suggestions to balance loads across the cluster.
- **Proactive Monitoring:** Receive alerts before issues affect performance, ensuring high availability and reliability.
- **Flexible Configuration:** Easily customize monitoring thresholds and migration strategies to suit your specific needs.

## 📬 **Feedback and Contributions**
We welcome feedback and contributions! If you encounter any issues or have suggestions for improvement, feel free to open an issue or submit a pull request on our GitHub repository.

## 📜 **License**
This project is licensed under the MIT License, which allows for reuse and modification as long as the original authors are credited.
