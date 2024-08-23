import paramiko
import subprocess

def ssh_connect(host, user, password=None, key_path=None):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    if key_path:
        ssh.connect(host, username=user, key_filename=key_path)
    else:
        ssh.connect(host, username=user, password=password)
    return ssh

def get_host_metrics(ssh):
    """
    Fetch the metrics specific to the host (CPU load, memory, disk, etc.).
    :param ssh: SSH connection object.
    :return: Dictionary with host metrics.
    """
    commands = {
        'cpu_cores': "nproc",  # Get the number of CPU cores
        'total_memory': "free -m | grep Mem | awk '{print $2}'",  # Get total memory in MB
        'used_memory': "free -m | grep Mem | awk '{print $3}'",  # Get used memory in MB
        'total_disk': "df -h / | tail -1 | awk '{print $2}'",  # Get total disk space
        'used_disk': "df -h / | tail -1 | awk '{print $3}'",  # Get used disk space
        'cpu': "cat /proc/loadavg | awk '{print $1, $2, $3}'",  # Get the load averages
        'memory': "free -m | grep Mem | awk '{print $3, $2}'",  # Get used and total memory in MB
        'disk': "df -h / | tail -1 | awk '{print $3, $2}'",  # Get used and total disk space
        'network_interfaces': (
            "awk -F: '$1 !~ /lo/ && $1 ~ /^(eth|eno|vmbr)/ {print $1}' /proc/net/dev"
        ),  # Get network interface names excluding 'lo'
        'containers': "pct list | tail -n +2"  # Get list of containers
    }

    metrics = {}
    for key, cmd in commands.items():
        stdin, stdout, stderr = ssh.exec_command(cmd)
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()

        if error:
            print(f"Error fetching {key}: {error}")
        else:
            metrics[key] = output

    # Process network interface metrics
    if 'network_interfaces' in metrics and isinstance(metrics['network_interfaces'], str):
        interfaces = metrics['network_interfaces'].splitlines()
        network_metrics = {}
        for iface in interfaces:
            iface = iface.strip()  # Remove any extra whitespace
            stdin, stdout, stderr = ssh.exec_command(
                f"awk '/^{iface}/ {{print $1, $2, $10}}' /proc/net/dev"
            )
            line = stdout.read().decode().strip()
            if line:
                iface_name, rx_bytes, tx_bytes = line.split()
                iface_name = iface_name.strip(':')  # Remove trailing colon
                network_metrics[iface_name] = {
                    'received_bytes': int(rx_bytes),
                    'transmitted_bytes': int(tx_bytes)
                }
        metrics['network'] = network_metrics
    else:
        metrics['network'] = {}

    # Process container metrics
    if 'containers' in metrics and isinstance(metrics['containers'], str):
        container_metrics = []
        lines = metrics['containers'].splitlines()
        for line in lines:
            parts = line.split(None, 3)
            if len(parts) == 3:
                vmid, status, name = parts
                lock = ''
            elif len(parts) == 4:
                vmid, status, lock, name = parts
            else:
                continue  # Skip lines that don't have at least 3 parts
            container_metrics.append({
                'vmid': vmid,
                'status': status,
                'lock': lock,
                'name': name.strip()
            })
        metrics['containers'] = container_metrics

    return metrics

def get_container_metrics(ssh, vmid):
    """
    Fetch metrics specific to a container.
    :param ssh: SSH connection object.
    :param vmid: The VMID of the container.
    :return: Dictionary with container-specific metrics.
    """
    commands = {
        'cpu': f"pct exec {vmid} -- cat /proc/loadavg | awk '{{print $1, $2, $3}}'",
        'memory': f"pct exec {vmid} -- free -m | grep Mem | awk '{{print $3, $2}}'"
    }

    metrics = {}
    for key, cmd in commands.items():
        stdin, stdout, stderr = ssh.exec_command(cmd)
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()

        if error:
            print(f"Error fetching {key} for container {vmid}: {error}")
        else:
            metrics[key] = output

    return metrics

def get_container_config(ssh, vmid):
    """
    Retrieve the container configuration using pct config vmid via SSH.
    :param ssh: SSH connection object.
    :param vmid: The VMID of the container.
    :return: Dictionary with container-specific configuration.
    """
    try:
        stdin, stdout, stderr = ssh.exec_command(f"pct config {vmid} | grep cores | awk '{{print $2}}'")
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()

        if error:
            print(f"Error retrieving config for VMID {vmid}: {error}")
            return None

        config = {'cores': int(output)}
        return config

    except Exception as e:
        print(f"Failed to retrieve config for VMID {vmid}: {str(e)}")
        return None
