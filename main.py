from logger import setup_logging
from config import load_config
from functions import ssh_connect, get_host_metrics, get_container_metrics, get_container_config
from sensors import check_cpu_load, check_memory_usage
from triggers import send_alert  # Assuming you have this implemented
from utils import format_metrics_for_logging
import logging
from colorama import init, Fore, Style
import asyncio  # Import asyncio for concurrent tasks

# Initialize colorama
init(autoreset=True)

# Suppress paramiko INFO-level logs
logging.getLogger("paramiko").setLevel(logging.WARNING)


# --- Helper Functions ---
def calculate_balance_score(cpu_load, memory_usage, cpu_threshold, memory_threshold, cpu_weight, memory_weight):
    """Calculates a balance score for a host based on CPU and memory usage."""
    cpu_score = cpu_load / cpu_threshold
    memory_score = memory_usage / memory_threshold
    return cpu_score * cpu_weight + memory_score * memory_weight


def calculate_migration_suitability_score(free_memory, free_cores, balance_score_after_migration, original_balance_score,
                                         memory_weight, core_weight, balance_weight):
    """Calculates a suitability score for migrating to a host."""
    score = 0

    if free_memory > 0:
        score += free_memory * memory_weight  # Normalized at usage
    if free_cores > 0:
        score += free_cores * core_weight  # Normalized at usage

    balance_improvement = original_balance_score - balance_score_after_migration
    if balance_improvement > 0:
        score += (balance_improvement / original_balance_score) * balance_weight

    return score


async def fetch_container_metrics(ssh, container_id):
    """Asynchronously fetches metrics for a single container."""
    try:
        container_metrics = get_container_metrics(ssh, container_id)
        container_config = get_container_config(ssh, container_id)
        return container_metrics, container_config
    except Exception as e:
        logging.error(f"Error fetching metrics for container {container_id}: {e}")
        return None, None


async def calculate_host_capacity(host_name, host_metrics, default_params):
    """Calculates free resources, balance scores, and other metrics for a host."""
    try:
        total_cores = int(host_metrics['cpu_cores'])
        used_cores = 0
        total_container_memory = 0
        total_container_cpu_load = 0
        ssh = ssh_connect(host_metrics['address'], host_metrics['user'],
                            password=host_metrics.get('password'),
                            key_path=host_metrics.get('key_path'))


        tasks = [fetch_container_metrics(ssh, container['vmid']) for container in host_metrics['containers'] if
                 container['status'] == 'running']
        container_results = await asyncio.gather(*tasks)

        for container, (container_metrics, container_config) in zip(
                [container for container in host_metrics['containers'] if container['status'] == 'running'],
                container_results
        ):

            if container_config and container_metrics:
                container_cores = int(container_config['cores'])
                container_memory = int(container_metrics['memory'].split()[0])
                container_cpu_load = float(container_metrics['cpu'].split()[0])

                used_cores += container_cores
                total_container_memory += container_memory
                total_container_cpu_load += container_cpu_load
                # Print container metrics
                print(f"{Fore.CYAN}Container {container['vmid']} metrics:")
                print(f"   - Cores: {container_cores}")
                print(f"   - Memory Usage: {container_memory} MB")
                print(f"   - CPU Load: {container_cpu_load}%")

        free_cores = total_cores - used_cores
        free_memory = int(host_metrics['memory'].split()[1]) - total_container_memory

        balance_score = calculate_balance_score(
            float(host_metrics['cpu'].split()[0]),
            int(host_metrics['memory'].split()[0]) / int(host_metrics['memory'].split()[1]),
            host_metrics.get('cpu_threshold', default_params['cpu_threshold']),
            host_metrics.get('memory_threshold', default_params['memory_threshold']),
            default_params.get('balance_score_cpu_weight', 0.7),
            default_params.get('balance_score_memory_weight', 0.3)
        )

        host_metrics.update({
            'used_cores': used_cores,
            'free_cores': free_cores,
            'total_container_memory': total_container_memory,
            'total_container_cpu_load': total_container_cpu_load,
            'free_memory': free_memory,
            'balance_score': balance_score
        })
        print(f"🖥️ Host: {host_name}, Free Cores: {free_cores}, Free Memory: {free_memory} MB")
        ssh.close()
        return True
    except Exception as e:
        logging.error(f"Error calculating capacity for {host_name}: {e}")
        if ssh:
            ssh.close()
        return False


def get_migration_candidates(hosts_metrics, default_params):
    """Identifies potential migration candidates based on overloaded hosts."""
    migration_candidates = []
    overloaded_hosts = []
    for host_name, host_metrics in hosts_metrics.items():
        cpu_threshold = host_metrics.get('cpu_threshold', default_params['cpu_threshold'])
        memory_threshold = host_metrics.get('memory_threshold', default_params['memory_threshold'])
        cpu_overloaded = float(host_metrics['cpu'].split()[0]) > cpu_threshold
        memory_overloaded = int(host_metrics['memory'].split()[0]) / int(host_metrics['memory'].split()[1]) > memory_threshold

        # Debug information
        print(f"🔍 Host: {host_name}, CPU Overloaded: {cpu_overloaded}, Memory Overloaded: {memory_overloaded}")
        if cpu_overloaded or memory_overloaded:
            overloaded_hosts.append((host_name, host_metrics))

    if not overloaded_hosts:
        print(f"{Fore.BLUE}ℹ️  No hosts are overloaded based on the given thresholds.")
        return [], []
    else:
        print(f"{Fore.BLUE}Overloaded Hosts: {', '.join([host[0] for host in overloaded_hosts])}")

    for source_host_name, source_host_metrics in overloaded_hosts:
        for container in source_host_metrics['containers']:
            if container['status'] != 'running':
                continue

            container_id = container['vmid']

            try:
                ssh = ssh_connect(
                    source_host_metrics['address'],
                    source_host_metrics['user'],
                    password=source_host_metrics.get('password'),
                    key_path=source_host_metrics.get('key_path')
                )
                container_metrics = get_container_metrics(ssh, container_id)
                container_config = get_container_config(ssh, container_id)
                ssh.close()
            except Exception as e:
                print(f"{Fore.RED}❌ Error fetching metrics for container {container_id} on {source_host_name}: {str(e)}")
                continue

            if not container_metrics or not container_config:
                continue
            container_cores = int(container_config['cores'])
            container_memory = int(container_metrics['memory'].split()[0])
            container_cpu_load = float(container_metrics['cpu'].split()[0])
            container_priority = container_cpu_load * 0.7 + container_memory / int(source_host_metrics['memory'].split()[1]) * 0.3
            migration_candidates.append({
                'container_id': container_id,
                'source_host': source_host_name,
                'container_priority': container_priority,
                'container_cores': container_cores,
                'container_memory': container_memory,
                'container_cpu_load': container_cpu_load,
            })

    migration_candidates.sort(key=lambda x: x['container_priority'], reverse=True)
    return migration_candidates, overloaded_hosts


def evaluate_migration_target(candidate, hosts_metrics, default_params):
    """Evaluates potential target hosts for a container migration."""
    source_host_metrics = hosts_metrics[candidate['source_host']]
    best_target = None
    best_score = None
    best_balance_score_after_migration = None
    best_migration_suitability_score = None
    sorted_hosts = sorted(hosts_metrics.items(), key=lambda item: item[1]['balance_score'], reverse=True)

    for target_host_name, target_host_metrics in sorted_hosts:
        if target_host_name == candidate['source_host']:
            continue
        available_memory = target_host_metrics['free_memory']
        available_cores = target_host_metrics['free_cores']
        projected_cpu_load = float(target_host_metrics['cpu'].split()[0]) + candidate['container_cpu_load']
        projected_memory_usage = int(target_host_metrics['memory'].split()[0]) + candidate['container_memory']
        cpu_score = projected_cpu_load / target_host_metrics['cpu_threshold']
        memory_score = projected_memory_usage / int(target_host_metrics['memory'].split()[1])
        total_score = cpu_score * 0.7 + memory_score * 0.3

        balance_score_after_migration = calculate_balance_score(
            projected_cpu_load,
            projected_memory_usage / int(target_host_metrics['memory'].split()[1]),
            target_host_metrics['cpu_threshold'],
            target_host_metrics['memory_threshold'],
            default_params.get('balance_score_cpu_weight', 0.7),
            default_params.get('balance_score_memory_weight', 0.3)
        )

        migration_suitability_score = calculate_migration_suitability_score(
            available_memory,
            available_cores,
            balance_score_after_migration,
            target_host_metrics['balance_score'],
            default_params.get('migration_memory_weight', 30),
            default_params.get('migration_core_weight', 30),
            default_params.get('migration_balance_weight', 40)
        )
        # Debug information
        print(f"🛠️  Evaluating migration to {target_host_name}: Suitability Score = {migration_suitability_score:.2f}")

        if available_memory >= candidate['container_memory'] and available_cores >= candidate['container_cores']:
            if best_score is None or total_score < best_score:
                best_target = target_host_name
                best_score = total_score
                best_balance_score_after_migration = balance_score_after_migration
                best_migration_suitability_score = migration_suitability_score

    return best_target, best_score, best_balance_score_after_migration, best_migration_suitability_score


def suggest_migrations(hosts_metrics, default_params):
    """Suggests container migrations to balance load across hosts."""
    suggestions = []
    migration_reasons = []
    migration_candidates, overloaded_hosts = get_migration_candidates(hosts_metrics, default_params)

    for candidate in migration_candidates:
        best_target, best_score, best_balance_score_after_migration, best_migration_suitability_score = evaluate_migration_target(
            candidate, hosts_metrics, default_params)

        if best_target:
            reason = f"Better resource distribution: migration suitability score = {best_migration_suitability_score:.2f}"
            suggestions.append({
                'container_id': candidate['container_id'],
                'source_host': candidate['source_host'],
                'target_host': best_target,
                'reason': reason,
                'detailed_calc': f"Container CPU Load: {candidate['container_cpu_load']}, Container Memory: {candidate['container_memory']} MB, Target CPU Score: {cpu_score:.2f}, Target Memory Score: {memory_score:.2f}, Total Score: {best_score:.2f}, Balance Score After Migration: {best_balance_score_after_migration:.2f}, Migration Suitability Score: {best_migration_suitability_score:.2f}"
            })
            migration_reasons.append(f"{Fore.YELLOW}🔄 Considering migrating container {Fore.CYAN}{candidate['container_id']} {Fore.YELLOW}from {Fore.RED}{candidate['source_host']} {Fore.YELLOW}to {Fore.GREEN}{best_target}")
            migration_reasons.append(f"   {Fore.MAGENTA}Reason: {reason}{Style.RESET_ALL}")
            migration_reasons.append(f"   {Fore.MAGENTA}Details: {suggestions[-1]['detailed_calc']}{Style.RESET_ALL}")

    if not suggestions:
        print(f"{Fore.BLUE}ℹ️  No migrations suggested. All hosts are balanced.")
    else:
        print("\n".join(migration_reasons))
        print(f"{Fore.GREEN}🎯 Final Suggested Migrations for Load Balancing:")
        for suggestion in suggestions:
            print(f"{Fore.GREEN}➡️  Migrate container {Fore.CYAN}{suggestion['container_id']} {Fore.GREEN}from {Fore.RED}{suggestion['source_host']} {Fore.GREEN}to {Fore.GREEN}{suggestion['target_host']}")
            print(f"   {Fore.YELLOW}Reason: {Fore.MAGENTA}{suggestion['reason']}{Style.RESET_ALL}")
            print(f"   {Fore.YELLOW}Details: {Fore.MAGENTA}{suggestion['detailed_calc']}{Style.RESET_ALL}")

    return suggestions


async def main():
    """Main entry point for the Proxmox Cluster Balancer."""
    logger = setup_logging()
    config = load_config('config.yaml')
    default_params = config.get('default_params', {})
    hosts_metrics = {}
    tasks = []

    for host in config['proxmox_hosts']:
        logger.info(f"🔌 Connecting to {host['name']} ({host['address']})...")
        try:
            ssh = ssh_connect(
                host['address'],
                host['user'],
                password=host.get('password'),
                key_path=host.get('key_path')
            )
            logger.info("📊 Fetching host metrics...")
            host_metrics = get_host_metrics(ssh)
            host_metrics.update({
                'address': host['address'],
                'user': host['user'],
                'password': host.get('password'),
                'key_path': host.get('key_path'),
                'cpu_threshold': host.get('cpu_threshold', default_params['cpu_threshold']),
                'memory_threshold': host.get('memory_threshold', default_params['memory_threshold']),
            })
            hosts_metrics[host['name']] = host_metrics

            logger.info(f"🔍 Host metrics for {host['name']}: {format_metrics_for_logging(host_metrics)}")

            if check_cpu_load(host_metrics['cpu'], host_metrics['cpu_threshold']):
                print(
                    f"{Fore.RED}⚠️  Alert! {host['name']} has exceeded the threshold for CPU Load: {host_metrics['cpu']} (Threshold: {host_metrics['cpu_threshold']})")

            if check_memory_usage(host_metrics['memory']):
                print(
                    f"{Fore.RED}⚠️  Alert! {host['name']} has exceeded the threshold for Memory Usage: {host_metrics['memory']} (Threshold: {host_metrics['memory_threshold']})")

            ssh.close()
            tasks.append(calculate_host_capacity(host['name'], host_metrics, default_params))
        except ConnectionError as e:
             logger.error(f"❌ Connection Error: Could not connect to {host['name']}: {e}")
        except Exception as e:
            logger.error(f"❌ Error connecting to {host['name']}: {e}")
            if ssh:
                ssh.close()

    await asyncio.gather(*tasks)
    migration_suggestions = suggest_migrations(hosts_metrics, default_params)

    for suggestion in migration_suggestions:
        logger.info(
            f"🔄 Suggesting to migrate container {suggestion['container_id']} from {suggestion['source_host']} to {suggestion['target_host']}")


if __name__ == "__main__":
    asyncio.run(main())
