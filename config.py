import yaml
import os
import logging
from schema import Schema, And, Use, Optional, SchemaError

# --- Setup Logger ---
logger = logging.getLogger(__name__)

# --- Configuration Schema ---
CONFIG_SCHEMA = Schema({
    'proxmox_hosts': [
        {
            'name': And(str, len),  # Ensure it's a non-empty string
            'address': And(str, len),
            'user': And(str, len),
            Optional('password'): str,
            Optional('key_path'): str,
            Optional('cpu_threshold'): Use(float),
            Optional('memory_threshold'): Use(float),
        }
    ],
    Optional('default_params'): {
        Optional('cpu_threshold'): Use(float),
        Optional('memory_threshold'): Use(float),
        Optional('migration_strategy'): And(str, len),
        Optional('balance_score_cpu_weight'): Use(float),
        Optional('balance_score_memory_weight'): Use(float),
        Optional('migration_memory_weight'): Use(int),
        Optional('migration_core_weight'): Use(int),
        Optional('migration_balance_weight'): Use(int),
        Optional('max_migration_suitability_score'): Use(int),

    }
})


def load_config(config_file='config.yaml'):
    """
    Loads configuration from a YAML file, validates it, and supports environment variables.

    Args:
        config_file (str, optional): The path to the configuration file. Defaults to 'config.yaml'.

    Returns:
        dict: The loaded configuration as a Python dictionary.

    Raises:
        FileNotFoundError: If the config file is not found.
        yaml.YAMLError: If there's an issue parsing the YAML.
        SchemaError: If the config doesn't match the expected schema.
    """
    config = {}

    try:
        with open(config_file, 'r') as file:
            config = yaml.safe_load(file)
        if not config:
            raise ValueError(f"Config file {config_file} is empty.")
    except FileNotFoundError:
        logger.error(f"❌ Configuration file not found at '{config_file}'")
        raise  # Re-raise to be handled by caller
    except yaml.YAMLError as e:
        logger.error(f"❌ Error parsing YAML file '{config_file}': {e}")
        raise  # Re-raise for caller to handle
    except ValueError as e:
        logger.error(f"❌ Error reading config file '{config_file}': {e}")
        raise

    try:
        config = CONFIG_SCHEMA.validate(config)
    except SchemaError as e:
        logger.error(f"❌ Invalid configuration format in '{config_file}': {e}")
        raise  # Re-raise for the caller to handle

    # Apply environment variable overrides
    config = _apply_env_overrides(config)

    # Provide defaults
    config = _apply_defaults(config)

    logger.info("✅ Configuration loaded successfully.")
    return config


def _apply_env_overrides(config):
    """Overrides configuration with environment variables."""
    for host in config.get('proxmox_hosts', []):
        for key in host.keys():
            env_key = f"PROXMOX_{host['name'].upper()}_{key.upper()}"
            if env_key in os.environ:
                host[key] = os.environ[env_key]

    if 'default_params' in config:
       for key in config['default_params'].keys():
          env_key = f"PROXMOX_DEFAULT_{key.upper()}"
          if env_key in os.environ:
              config['default_params'][key] = os.environ[env_key]
    return config


def _apply_defaults(config):
  """Apply default values if not set in config"""
  if 'default_params' not in config:
      config['default_params'] = {}
  if 'cpu_threshold' not in config['default_params']:
    config['default_params']['cpu_threshold'] = 1.0
  if 'memory_threshold' not in config['default_params']:
    config['default_params']['memory_threshold'] = 0.8
  if 'balance_score_cpu_weight' not in config['default_params']:
    config['default_params']['balance_score_cpu_weight'] = 0.7
  if 'balance_score_memory_weight' not in config['default_params']:
    config['default_params']['balance_score_memory_weight'] = 0.3
  if 'migration_memory_weight' not in config['default_params']:
    config['default_params']['migration_memory_weight'] = 30
  if 'migration_core_weight' not in config['default_params']:
    config['default_params']['migration_core_weight'] = 30
  if 'migration_balance_weight' not in config['default_params']:
    config['default_params']['migration_balance_weight'] = 40
  if 'max_migration_suitability_score' not in config['default_params']:
    config['default_params']['max_migration_suitability_score'] = 100
  return config
if __name__ == "__main__":
  try:
      config = load_config()
      print("Config loaded successfully:")
      print(config)
  except Exception as e:
      print(f"Failed to load config: {e}")
