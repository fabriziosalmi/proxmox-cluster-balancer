import logging
from functions import SSHClient # Use the SSHClient
# --- Setup Logger ---
logger = logging.getLogger(__name__)

def check_cpu_load(cpu_load, threshold):
    """
    Check if the CPU load exceeds a given threshold.
    :param cpu_load: Load average string (e.g., "1.23 0.98 0.67")
    :param threshold: The threshold for the 1-minute load average.
    :return: True if the load exceeds the threshold, False otherwise.
    """
    try:
       load_1_min = float(cpu_load.split()[0])
       return load_1_min > threshold
    except Exception as e:
        logger.error(f"❌ Error checking CPU load: {e}")
        return False

def check_memory_usage(memory_info, threshold):
    """
    Check if the memory usage exceeds a given threshold.
    :param memory_info: Memory usage string (e.g., "4096 8192" for used and total memory in MB)
    :param threshold: The threshold percentage for memory usage.
    :return: True if the memory usage exceeds the threshold, False otherwise.
    """
    try:
      used, total = map(int, memory_info.split())
      usage_percentage = (used / total)
      return usage_percentage > threshold
    except Exception as e:
      logger.error(f"❌ Error checking memory usage: {e}")
      return False

def get_container_cpu_load(ssh_client, vmid, threshold):
    """
    Fetch and check the CPU load for a specific container.
    :param ssh_client: SSHClient object.
    :param vmid: The VMID of the container.
    :param threshold: The threshold for the 1-minute load average.
    :return: True if the load exceeds the threshold, False otherwise.
    """
    try:
        cmd = f"pct exec {vmid} -- cat /proc/loadavg"
        cpu_load = ssh_client.exec_command(cmd)
        if not cpu_load:
           return False
        return check_cpu_load(cpu_load, threshold)
    except Exception as e:
        logger.error(f"❌ Error fetching and checking CPU load for container {vmid}: {e}")
        return False

def get_container_memory_usage(ssh_client, vmid, threshold):
    """
    Fetch and check the memory usage for a specific container.
    :param ssh_client: SSHClient object.
    :param vmid: The VMID of the container.
    :param threshold: The threshold fraction for memory usage.
    :return: True if the memory usage exceeds the threshold, False otherwise.
    """
    try:
        cmd = f"pct exec {vmid} -- free -m | grep Mem | awk '{{print $3, $2}}'"
        memory_info = ssh_client.exec_command(cmd)
        if not memory_info:
            return False

        return check_memory_usage(memory_info, threshold)
    except Exception as e:
        logger.error(f"❌ Error fetching and checking memory usage for container {vmid}: {e}")
        return False

if __name__ == '__main__':
    # Example Usage
    try:
        ssh_client = SSHClient("192.168.5.1", "root", password="password")
        ssh_client.connect()

        cpu_load_str = "1.23 0.98 0.67"
        memory_info_str = "4096 8192"

        threshold_cpu = 1.0
        threshold_memory = 0.8


        print(f"CPU load {cpu_load_str} exceeds threshold {threshold_cpu}: {check_cpu_load(cpu_load_str, threshold_cpu)}")
        print(f"Memory usage {memory_info_str} exceeds threshold {threshold_memory}: {check_memory_usage(memory_info_str, threshold_memory)}")

        print(f"Container 100 CPU load exceeds threshold {threshold_cpu}: {get_container_cpu_load(ssh_client, '100', threshold_cpu)}")
        print(f"Container 100 Memory usage exceeds threshold {threshold_memory}: {get_container_memory_usage(ssh_client, '100', threshold_memory)}")

        ssh_client.close()
    except Exception as e:
        print(f"Error in example usage: {e}")
