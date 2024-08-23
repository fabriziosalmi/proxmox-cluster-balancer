import paramiko

def check_cpu_load(cpu_load, threshold=1.0):
    """
    Check if the CPU load exceeds a given threshold.
    :param cpu_load: Load average string (e.g., "1.23 0.98 0.67")
    :param threshold: The threshold for the 1-minute load average.
    :return: True if the load exceeds the threshold, False otherwise.
    """
    load_1_min = float(cpu_load.split()[0])
    return load_1_min > threshold

def check_memory_usage(memory_info, threshold=80):
    """
    Check if the memory usage exceeds a given threshold.
    :param memory_info: Memory usage string (e.g., "4096 8192" for used and total memory in MB)
    :param threshold: The threshold percentage for memory usage.
    :return: True if the memory usage exceeds the threshold, False otherwise.
    """
    used, total = map(int, memory_info.split())
    usage_percentage = (used / total) * 100
    return usage_percentage > threshold

def get_container_cpu_load(ssh, vmid, threshold=1.0):
    """
    Fetch and check the CPU load for a specific container.
    :param ssh: SSH connection object.
    :param vmid: The VMID of the container.
    :param threshold: The threshold for the 1-minute load average.
    :return: True if the load exceeds the threshold, False otherwise.
    """
    cmd = f"pct exec {vmid} -- cat /proc/loadavg"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    cpu_load = stdout.read().decode().strip()

    if stderr.read().decode().strip():
        print(f"Error fetching CPU load for container {vmid}")
        return False

    return check_cpu_load(cpu_load, threshold)

def get_container_memory_usage(ssh, vmid, threshold=80):
    """
    Fetch and check the memory usage for a specific container.
    :param ssh: SSH connection object.
    :param vmid: The VMID of the container.
    :param threshold: The threshold percentage for memory usage.
    :return: True if the memory usage exceeds the threshold, False otherwise.
    """
    cmd = f"pct exec {vmid} -- free -m | grep Mem | awk '{{print $3, $2}}'"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    memory_info = stdout.read().decode().strip()

    if stderr.read().decode().strip():
        print(f"Error fetching memory usage for container {vmid}")
        return False

    return check_memory_usage(memory_info, threshold)

def get_host_cpu_load(cpu_load, threshold=1.0):
    """
    Wrapper function to check the CPU load for a host.
    :param cpu_load: Load average string from the host.
    :param threshold: The threshold for the 1-minute load average.
    :return: True if the load exceeds the threshold, False otherwise.
    """
    return check_cpu_load(cpu_load, threshold)

def get_host_memory_usage(memory_info, threshold=80):
    """
    Wrapper function to check the memory usage for a host.
    :param memory_info: Memory usage string from the host.
    :param threshold: The threshold percentage for memory usage.
    :return: True if the memory usage exceeds the threshold, False otherwise.
    """
    return check_memory_usage(memory_info, threshold)
