import logging
from functions import SSHClient # Use the SSHClient

# --- Setup Logger ---
logger = logging.getLogger(__name__)

def trigger_migration(ssh_client, container_id, target_host, migration_command):
    """Triggers the migration of a container using a given command."""
    try:
      if not migration_command:
        logger.error(f"❌ Migration command is empty, can not proceed.")
        return False
      command = f"{migration_command} {container_id} {target_host}"
      output = ssh_client.exec_command(command)
      if output is not None:
          logger.info(f"✅ Successfully triggered migration of container {container_id} to {target_host}")
          return True
      else:
          logger.error(f"❌ Failed to trigger migration of container {container_id} to {target_host}")
          return False
    except Exception as e:
        logger.error(f"❌ Error triggering migration of container {container_id} to {target_host}: {e}")
        return False


def send_alert(host, metric, value, threshold, alert_type="Threshold Exceeded"):
    """Sends an alert notification, you can add more notification channels here."""
    try:
      message = f"Alert! {alert_type} on {host}: {metric} has value {value}, which exceeds the threshold {threshold}."
      logger.warning(message)
      # Here you can add additional notification methods, like:
      # send_email_notification(message)
      # send_slack_notification(message)
      # send_sms_notification(message)
      return True
    except Exception as e:
      logger.error(f"❌ Error sending alert: {e}")
      return False

if __name__ == "__main__":
    # Example Usage
  try:
    ssh_client = SSHClient("192.168.5.1", "root", password="password")
    ssh_client.connect()

    container_id = "100"
    source_host = "proxmox1"
    target_host = "proxmox2"
    migration_command = "pct migrate"
    if trigger_migration(ssh_client, container_id, target_host, migration_command):
      print("Migration Successfully triggered.")

    host = "proxmox1"
    metric = "CPU Load"
    value = "2.5"
    threshold = "2.0"
    if send_alert(host, metric, value, threshold, alert_type = "CPU Threshold Exceeded"):
     print("Alert Successfully sent.")
    ssh_client.close()
  except Exception as e:
    print(f"Error in example usage: {e}")
