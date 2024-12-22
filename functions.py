import paramiko
import logging
import re

# --- Setup Logger ---
logger = logging.getLogger(__name__)


class SSHClient:
    """Encapsulates SSH connection and operations."""

    def __init__(self, host, user, password=None, key_path=None):
        self.host = host
        self.user = user
        self.password = password
        self.key_path = key_path
        self.ssh = None  # Initialize ssh to None

    def connect(self):
        """Establishes the SSH connection."""
        try:
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            if self.key_path:
                self.ssh.connect(self.host, username=self.user, key_filename=self.key_path)
            else:
                self.ssh.connect(self.host, username=self.user, password=self.password)
            logger.info(f"✅ Connected to {self.host}")
        except paramiko.SSHException as e:
            logger.error(f"❌ SSH connection error for {self.host}: {e}")
            self.ssh = None  # Make sure to set self.ssh to None if it fails
            raise
        except Exception as e:
            logger.error(f"❌ Error connecting to {self.host}: {e}")
            self.ssh = None  # Make sure to set self.ssh to None if it fails
            raise

    def exec_command(self, command):
        """Executes a command via SSH."""
        if not self.ssh:
           raise Exception(f"❌ SSH connection not established for {self.host}")
        try:
            stdin, stdout, stderr = self.ssh.exec_command(command)
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()

            if error:
                logger.error(f"❌ Error executing command '{command}' on {self.host}: {error}")
                return None
            return output
        except Exception as e:
            logger.error(f"❌ Exception executing command '{command}' on {self.host}: {e}")
            return None


    def close(self):
        """Closes the SSH connection."""
        if self.ssh:
            self.ssh.close()
            logger.info(f"🔌 Connection to {self.host} closed.")
            self.ssh = None #Make sure we set to None after closing


# --- Metric Collection Functions ---
def get_host_metrics(ssh_client):
    """Fetches host-level metrics."""
    commands = {
        'cpu_cores': "nproc",
        'total_memory': "free -m | grep Mem | awk '{print $2}'",
        'used_memory': "free -m | grep Mem | awk '{print $3}'",
        'total_disk': "df -h / | tail -1 | awk '{print $2}'",
        'used_disk': "df -h / | tail -1 | awk '{print $3}'",
        'cpu': "cat /proc/loadavg | awk '{print $1, $2, $3}'",
        'memory': "free -m | grep Mem | awk '{print $3, $2}'",
        'disk': "df -h / | tail -1 | awk '{print $3, $2}'",
        'network_interfaces': (
            "awk -F: '$1 !~ /lo/ && $1 ~ /^(eth|eno|vmbr)/ {print $1}' /proc/net/dev"
        ),
         'containers': "pct list | tail -n +2"
    }
    metrics = {}
    for key, cmd in commands.items():
        output = ssh_client.exec_command(cmd)
        if output is not None:
            metrics[key] = output

    # Process network interface metrics
    if 'network_interfaces' in metrics and isinstance(metrics['network_interfaces'], str):
        interfaces = metrics['network_interfaces'].splitlines()
        network_metrics = {}
        for iface in interfaces:
            iface = iface.strip()  # Remove any extra whitespace
            line = ssh_client.exec_command(
                f"awk '/^{iface}/ {{print $1, $2, $10}}' /proc/net/dev"
            )
            if line:
                parts = line.split()
                if len(parts) == 3:
                    iface_name, rx_bytes, tx_bytes = parts
                    iface_name = iface_name.strip(':')  # Remove trailing colon
                    network_metrics[iface_name] = {
                        'received_bytes': int(rx_bytes),
                        'transmitted_bytes': int(tx_bytes)
                    }

                else:
                    logger.warning(f"Invalid format for interface '{iface}': {line}")

        metrics['network'] = network_metrics
    else:
        metrics['network'] = {}

    # Process container metrics
    if 'containers' in metrics and isinstance(metrics['containers'], str):
        container_metrics = []
        lines = metrics['containers'].splitlines()
        for line in lines:
           parts = re.split(r'\s+', line.strip(), maxsplit=3)
           if len(parts) >=3 :
            if len(parts) == 3:
                vmid, status, name = parts
                lock = ''
            elif len(parts) == 4:
                vmid, status, lock, name = parts
            container_metrics.append({
               'vmid': vmid,
                'status': status,
                'lock': lock,
                'name': name.strip()
             })
           else:
               logger.warning(f"Invalid format in container list: {line}")

        metrics['containers'] = container_metrics

    return metrics


def get_container_metrics(ssh_client, vmid):
    """Fetches container-specific metrics."""
    commands = {
        'cpu': f"pct exec {vmid} -- cat /proc/loadavg | awk '{{print $1, $2, $3}}'",
        'memory': f"pct exec {vmid} -- free -m | grep Mem | awk '{{print $3, $2}}'"
    }
    metrics = {}
    for key, cmd in commands.items():
        output = ssh_client.exec_command(cmd)
        if output is not None:
           metrics[key] = output
    return metrics


def get_container_config(ssh_client, vmid):
    """Retrieves container-specific configuration."""
    try:
      output = ssh_client.exec_command(f"pct config {vmid} | grep cores | awk '{{print $2}}'")

      if output is None:
         return None
      return {'cores': int(output)}
    except Exception as e:
        logger.error(f"Failed to retrieve config for VMID {vmid}: {str(e)}")
        return None

if __name__ == '__main__':
    # Example Usage
    try:
       ssh_client = SSHClient("192.168.5.1", "root", password="password")
       ssh_client.connect()
       host_metrics = get_host_metrics(ssh_client)
       print("Host Metrics:", host_metrics)

       container_metrics = get_container_metrics(ssh_client, "100")
       print("Container Metrics:", container_metrics)

       container_config = get_container_config(ssh_client, "100")
       print("Container config:", container_config)

       ssh_client.close()
    except Exception as e:
        print(f"Error in example usage: {e}")
