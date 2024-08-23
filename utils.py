def calculate_load_imbalance(cpu_loads):
    # Example function to calculate load imbalance between hosts
    imbalance = max(cpu_loads) - min(cpu_loads)
    return imbalance

def format_metrics_for_logging(metrics):
    """
    Utility function to format metrics for easier logging.
    Masks sensitive information like user and password, only includes container VMIDs.
    """
    formatted_metrics = []

    for key, value in metrics.items():
        if key == 'containers' and isinstance(value, list):
            # Only extract vmid from each container
            container_vmids = [container['vmid'] for container in value if 'vmid' in container]
            formatted_metrics.append(f'containers: {container_vmids}')
        elif key in ['user', 'password']:
            # Mask sensitive information
            formatted_metrics.append(f'{key}: ***')
        else:
            formatted_metrics.append(f'{key}: {value}')

    return ', '.join(formatted_metrics)


#def format_metrics_for_logging(metrics):
#    # Utility function to format metrics for easier logging
#    return ', '.join([f'{key}: {value}' for key, value in metrics.items()])
