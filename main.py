from logger import setup_logging
from config import load_config
from functions import ssh_connect, get_host_metrics, get_container_metrics, get_container_config
from sensors import check_cpu_load, check_memory_usage
from triggers import send_alert
from utils import format_metrics_for_logging
import logging
from colorama import init, Fore, Style

# Suppress paramiko INFO-level logs
logging.getLogger("paramiko").setLevel(logging.WARNING)

def can_migrate(container_metrics, target_host_metrics):
    container_memory = int(container_metrics['memory'].split()[0])
    container_cpu_load = float(container_metrics['cpu'].split()[0])

    available_memory = int(target_host_metrics['total_memory']) - int(target_host_metrics['used_memory'])
    available_cpu_cores = int(target_host_metrics['cpu_cores'])

    if container_memory <= available_memory and container_cpu_load < available_cpu_cores:
        return True
    return False

# Initialize colorama
init(autoreset=True)

def suggest_migrations(hosts_metrics, default_params):
    suggestions = []
    migration_reasons = []

    def calculate_balance_score(cpu_load, memory_usage, cpu_threshold, memory_threshold):
        cpu_score = cpu_load / cpu_threshold
        memory_score = memory_usage / memory_threshold
        return cpu_score * 0.7 + memory_score * 0.3

    def calculate_migration_suitability_score(free_memory, free_cores, balance_score_after_migration, original_balance_score):
        score = 0

        if free_memory > 0:
            score += (free_memory / int(target_host_metrics['memory'].split()[1])) * 30

        if free_cores > 0:
            score += (free_cores / int(target_host_metrics['cpu_cores'])) * 30

        balance_improvement = original_balance_score - balance_score_after_migration
        if balance_improvement > 0:
            score += (balance_improvement / original_balance_score) * 40

        return min(int(score), 100)

    sorted_hosts = sorted(hosts_metrics.items(), key=lambda item: calculate_balance_score(
        float(item[1]['cpu'].split()[0]),
        int(item[1]['memory'].split()[0]) / int(item[1]['memory'].split()[1]),
        item[1].get('cpu_threshold', default_params['cpu_threshold']),
        item[1].get('memory_threshold', default_params['memory_threshold'])
    ), reverse=True)

    overloaded_hosts = []
    for host_name, host_metrics in sorted_hosts:
        cpu_threshold = host_metrics.get('cpu_threshold', default_params['cpu_threshold'])
        memory_threshold = host_metrics.get('memory_threshold', default_params['memory_threshold'])
        cpu_overloaded = float(host_metrics['cpu'].split()[0]) > cpu_threshold
        memory_overloaded = int(host_metrics['memory'].split()[0]) / int(host_metrics['memory'].split()[1]) > memory_threshold

        # Debug information
        print(f"🔍 Host: {host_name}, CPU Overloaded: {cpu_overloaded}, Memory Overloaded: {memory_overloaded}")

        total_cores = int(host_metrics['cpu_cores'])
        used_cores = 0
        total_container_memory = 0
        total_container_cpu_load = 0

        ssh = ssh_connect(host_metrics['address'], host_metrics['user'], password=host_metrics.get('password'), key_path=host_metrics.get('key_path'))

        for container in host_metrics['containers']:
            if container['status'] == 'running':
                container_config = get_container_config(ssh, container['vmid'])
                container_metrics = get_container_metrics(ssh, container['vmid'])
                if container_config and 'cores' in container_config and container_metrics:
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

        # Debug information
        print(f"🖥️ Host: {host_name}, Free Cores: {free_cores}, Free Memory: {free_memory} MB")

        host_metrics.update({
            'used_cores': used_cores,
            'free_cores': free_cores,
            'total_container_memory': total_container_memory,
            'total_container_cpu_load': total_container_cpu_load,
            'free_memory': free_memory,
            'balance_score': calculate_balance_score(
                float(host_metrics['cpu'].split()[0]),
                int(host_metrics['memory'].split()[0]) / int(host_metrics['memory'].split()[1]),
                cpu_threshold,
                memory_threshold
            )
        })
        ssh.close()

        if cpu_overloaded or memory_overloaded:
            overloaded_hosts.append((host_name, host_metrics))

    if not overloaded_hosts:
        print(f"{Fore.BLUE}ℹ️  No hosts are overloaded based on the given thresholds.")
    else:
        print(f"{Fore.BLUE}Overloaded Hosts: {', '.join([host[0] for host in overloaded_hosts])}")

    migration_candidates = []

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

    for candidate in migration_candidates:
        source_host_metrics = hosts_metrics[candidate['source_host']]
        best_target = None
        best_score = None
        best_balance_score_after_migration = None
        best_migration_suitability_score = None

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
                target_host_metrics['memory_threshold']
            )

            migration_suitability_score = calculate_migration_suitability_score(
                available_memory,
                available_cores,
                balance_score_after_migration,
                target_host_metrics['balance_score']
            )

            # Debug information
            print(f"🛠️  Evaluating migration to {target_host_name}: Suitability Score = {migration_suitability_score}/100")

            if available_memory >= candidate['container_memory'] and available_cores >= candidate['container_cores']:
                if best_score is None or total_score < best_score:
                    best_target = target_host_name
                    best_score = total_score
                    best_balance_score_after_migration = balance_score_after_migration
                    best_migration_suitability_score = migration_suitability_score

        if best_target:
            reason = f"Better resource distribution: free memory = {available_memory}, free cores = {available_cores}, migration suitability score = {best_migration_suitability_score}/100"
            suggestions.append({
                'container_id': candidate['container_id'],
                'source_host': candidate['source_host'],
                'target_host': best_target,
                'reason': reason,
                'detailed_calc': f"Container CPU Load: {candidate['container_cpu_load']}, Container Memory: {candidate['container_memory']} MB, Target CPU Score: {cpu_score:.2f}, Target Memory Score: {memory_score:.2f}, Total Score: {best_score:.2f}, Balance Score After Migration: {best_balance_score_after_migration:.2f}, Migration Suitability Score: {best_migration_suitability_score}/100"
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

def main():
    logger = setup_logging()
    config = load_config('config.yaml')
    default_params = config.get('default_params', {})

    hosts_metrics = {}

    for host in config['proxmox_hosts']:
        logger.info(f"🔌 Connecting to {host['name']} ({host['address']})...")
        ssh = None
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
                print(f"{Fore.RED}⚠️  Alert! {host['name']} has exceeded the threshold for CPU Load: {host_metrics['cpu']} (Threshold: {host_metrics['cpu_threshold']})")

            if check_memory_usage(host_metrics['memory']):
                print(f"{Fore.RED}⚠️  Alert! {host['name']} has exceeded the threshold for Memory Usage: {host_metrics['memory']} (Threshold: {host_metrics['memory_threshold']})")

        except Exception as e:
            logger.error(f"❌ Error connecting to {host['name']}: {str(e)}")
        finally:
            if ssh:
                ssh.close()

    migration_suggestions = suggest_migrations(hosts_metrics, default_params)

    for suggestion in migration_suggestions:
        logger.info(f"🔄 Suggesting to migrate container {suggestion['container_id']} from {suggestion['source_host']} to {suggestion['target_host']}")

if __name__ == "__main__":
    main()
