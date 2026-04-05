#!/usr/bin/env python3
"""
Network Monitoring and Metrics Collection
==========================================

This script provides monitoring and metrics collection for the SDN network:

1. **Flow Table Monitoring**: Queries switch flow tables periodically
2. **Latency Monitoring**: Measures ping latency between hosts
3. **CPU and Memory**: Monitors system resource usage
4. **PacketIn Rate**: Estimates PacketIn messages from controller logs
5. **Network Throughput**: Measures bandwidth usage

The metrics are saved to CSV files for later analysis and graphing.

Usage:
    sudo python3 monitoring.py --controller-host 127.0.0.1 --controller-port 6633 
                               --output-dir ./results

Requirements:
    - ryu package
    - Access to controller (for querying flow tables)
    - Root privileges for some network measurements
"""

import argparse
import logging
import time
import csv
import os
import subprocess
import psutil
from datetime import datetime
from collections import defaultdict
import threading

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
LOG = logging.getLogger(__name__)

class NetworkMonitor:
    """
    Monitor and collect metrics from SDN network and hosts
    """
    
    def __init__(self, hosts=['h1', 'h2'], output_dir='./results', 
                 interval=5, controller_host='127.0.0.1'):
        """
        Initialize network monitor
        
        Args:
            hosts: List of host names to monitor (e.g., ['h1', 'h2'])
            output_dir: Directory to save CSV files and results
            interval: Measurement interval in seconds
            controller_host: Controller IP address
        """
        self.hosts = hosts
        self.output_dir = output_dir
        self.interval = interval
        self.controller_host = controller_host
        self.is_running = False
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            LOG.info(f'Created output directory: {output_dir}')
        
        # Initialize CSV files
        self.metrics_file = os.path.join(output_dir, 'metrics.csv')
        self.latency_file = os.path.join(output_dir, 'latency.csv')
        self.cpu_file = os.path.join(output_dir, 'cpu_memory.csv')
        
        # Initialize CSV headers
        self._init_csv_files()
        
        LOG.info(f'Monitor initialized: {len(hosts)} hosts, interval={interval}s')

    def _init_csv_files(self):
        """
        Initialize CSV files with headers
        """
        # Main metrics file
        if not os.path.exists(self.metrics_file):
            with open(self.metrics_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Timestamp', 'Flow_Table_Size', 'Latency_ms', 
                                'PacketIn_Rate', 'Throughput_Mbps', 'Status'])
            LOG.info(f'Created metrics file: {self.metrics_file}')
        
        # Latency file
        if not os.path.exists(self.latency_file):
            with open(self.latency_file, 'w', newline='') as f:
                writer = csv.writer(f)
                headers = ['Timestamp', 'Source', 'Destination'] + \
                         [f'Latency_ms' for _ in range(5)]
                writer.writerow(headers)
            LOG.info(f'Created latency file: {self.latency_file}')
        
        # CPU/Memory file
        if not os.path.exists(self.cpu_file):
            with open(self.cpu_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Timestamp', 'CPU_Percent', 'Memory_Percent', 
                                'Memory_MB', 'Process_Count'])
            LOG.info(f'Created CPU file: {self.cpu_file}')

    def ping_hosts(self):
        """
        Measure latency between hosts using ping
        
        Returns:
            dict: Latency measurements {(src, dst): latency_ms}
        """
        latencies = {}
        
        for src_host in self.hosts:
            for dst_host in self.hosts:
                if src_host == dst_host:
                    continue
                
                try:
                    # Run ping from source to destination
                    # In Mininet, you can ping between network namespaces
                    result = subprocess.run(
                        f'ip netns exec {src_host} ping -c 1 -W 1 10.0.0.{dst_host[-1]} 2>/dev/null || sudo mnexec -a $(pgrep -f "mininet: {src_host}" | head -n 1) ping -c 1 -W 1 10.0.0.{dst_host[-1]}',
                        shell=True,
                        capture_output=True,
                        timeout=5,
                        text=True
                    )
                    
                    if result.returncode == 0:
                        # Parse latency from ping output
                        for line in result.stdout.split('\n'):
                            if 'time=' in line:
                                # Extract time value (e.g., "time=0.5 ms")
                                time_part = line.split('time=')[1].split()[0]
                                latencies[(src_host, dst_host)] = float(time_part)
                                break
                    else:
                        latencies[(src_host, dst_host)] = None
                        
                except Exception as e:
                    LOG.warning(f'Ping failed {src_host}->{dst_host}: {e}')
                    latencies[(src_host, dst_host)] = None
        
        return latencies

    def get_flow_table_size(self):
        try:
            import subprocess
            res = subprocess.run('sudo ovs-ofctl dump-flows s1', shell=True, capture_output=True, text=True)
            if res.returncode == 0:
                return max(0, len(res.stdout.strip().split('\n')) - 1)
        except Exception as e:
            pass
        return -1

    def get_system_metrics(self):
        """
        Get system CPU and memory metrics
        
        Returns:
            dict: CPU%, Memory%, UsedMemory MB, Process count
        """
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_mb = memory.used / 1024 / 1024
            process_count = len(psutil.pids())
            
            return {
                'cpu': cpu_percent,
                'memory_percent': memory_percent,
                'memory_mb': memory_mb,
                'process_count': process_count
            }
        except Exception as e:
            LOG.warning(f'Could not get system metrics: {e}')
            return {
                'cpu': -1,
                'memory_percent': -1,
                'memory_mb': -1,
                'process_count': -1
            }

    def record_metrics(self):
        """
        Record all metrics to CSV files
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Get measurements
        latencies = self.ping_hosts()
        flow_table_size = self.get_flow_table_size()
        system_metrics = self.get_system_metrics()
        
        # Calculate average latency
        valid_latencies = [l for l in latencies.values() if l is not None]
        avg_latency = sum(valid_latencies) / len(valid_latencies) if valid_latencies else -1
        
        # Record main metrics
        with open(self.metrics_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp,
                flow_table_size,
                f'{avg_latency:.2f}' if avg_latency > 0 else 'N/A',
                'N/A',  # PacketIn rate - would need controller log parsing
                'N/A',  # Throughput - would need iperf or similar
                'Running'
            ])
        
        # Record latency details
        if latencies:
            with open(self.latency_file, 'a', newline='') as f:
                writer = csv.writer(f)
                for (src, dst), lat in latencies.items():
                    writer.writerow([
                        timestamp,
                        src,
                        dst,
                        f'{lat:.2f}' if lat else 'N/A'
                    ])
        
        # Record CPU/Memory metrics
        with open(self.cpu_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp,
                f'{system_metrics["cpu"]:.1f}',
                f'{system_metrics["memory_percent"]:.1f}',
                f'{system_metrics["memory_mb"]:.1f}',
                system_metrics['process_count']
            ])
        
        LOG.info(f'[{timestamp}] Logged: flows={flow_table_size}, '
                 f'latency={avg_latency:.2f}ms, cpu={system_metrics["cpu"]:.1f}%')

    def monitor_loop(self):
        """
        Main monitoring loop - runs until is_running is False
        """
        LOG.info('Starting monitoring loop...')
        
        try:
            while self.is_running:
                try:
                    self.record_metrics()
                    time.sleep(self.interval)
                except Exception as e:
                    LOG.error(f'Error in monitoring loop: {e}')
                    time.sleep(1)  # Prevent rapid error loops
        
        except KeyboardInterrupt:
            LOG.info('Monitoring interrupted by user')
        
        finally:
            LOG.info('Monitoring stopped')

    def start(self):
        """
        Start monitoring in a background thread
        """
        self.is_running = True
        monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        monitor_thread.start()
        LOG.info('Monitoring thread started')
        return monitor_thread

    def stop(self):
        """
        Stop monitoring
        """
        self.is_running = False
        LOG.info('Monitoring stopped')

    def generate_report(self):
        """
        Generate a summary report from collected metrics
        """
        report_file = os.path.join(self.output_dir, 'summary_report.txt')
        
        try:
            with open(report_file, 'w') as f:
                f.write('='*60 + '\n')
                f.write('MONITORING SUMMARY REPORT\n')
                f.write('='*60 + '\n')
                f.write(f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
                f.write(f'Output Directory: {self.output_dir}\n')
                f.write(f'Monitoring Interval: {self.interval}s\n')
                f.write('\nData Files:\n')
                f.write(f'  - Metrics: {self.metrics_file}\n')
                f.write(f'  - Latency: {self.latency_file}\n')
                f.write(f'  - CPU/Memory: {self.cpu_file}\n')
                f.write('\nInstructions for Analysis:\n')
                f.write('  1. Import CSV files into Python (pandas), Excel, or LibreOffice\n')
                f.write('  2. Create graphs for flow table size over time\n')
                f.write('  3. Plot latency measurements\n')
                f.write('  4. Compare before/after defense mechanism activation\n')
                f.write('='*60 + '\n')
            
            LOG.info(f'Report saved to: {report_file}')
        
        except Exception as e:
            LOG.error(f'Failed to generate report: {e}')

def main():
    """
    Main function
    """
    parser = argparse.ArgumentParser(
        description='Monitor SDN network performance and collect metrics'
    )
    parser.add_argument('--hosts', nargs='+', default=['h1', 'h2'],
                        help='List of hosts to monitor')
    parser.add_argument('--output-dir', default='./results',
                        help='Directory to save metrics')
    parser.add_argument('--interval', type=int, default=5,
                        help='Measurement interval in seconds')
    parser.add_argument('--controller-host', default='127.0.0.1',
                        help='Controller IP address')
    parser.add_argument('--duration', type=int, default=0,
                        help='Monitoring duration in seconds (0 = infinite)')
    
    args = parser.parse_args()
    
    # Create monitor
    monitor = NetworkMonitor(
        hosts=args.hosts,
        output_dir=args.output_dir,
        interval=args.interval,
        controller_host=args.controller_host
    )
    
    # Start monitoring
    monitor_thread = monitor.start()
    
    try:
        if args.duration > 0:
            LOG.info(f'Monitoring for {args.duration} seconds...')
            time.sleep(args.duration)
        else:
            LOG.info('Monitoring started (press Ctrl+C to stop)...')
            monitor_thread.join()
    
    except KeyboardInterrupt:
        LOG.info('Monitoring interrupted by user')
    
    finally:
        monitor.stop()
        monitor.generate_report()
        LOG.info('Monitoring complete')


# --- HOTFIX ---
import subprocess
def new_ping_hosts(self):
    latencies = {}
    try:
        # Find the invisible Mininet process ID for Host 1
        res = subprocess.run(['pgrep', '-f', 'mininet: h1'], capture_output=True, text=True)
        pids = res.stdout.strip().split('\n')
        if pids and pids[0]:
            # Use mnexec to securely enter the namespace and ping Host 2
            ping_res = subprocess.run(f"sudo mnexec -a {pids[0]} ping -c 1 -W 1 10.0.0.2", shell=True, capture_output=True, text=True)
            for line in ping_res.stdout.split('\n'):
                if 'time=' in line:
                    latencies[('h1', 'h2')] = float(line.split('time=')[1].split()[0])
                    return latencies
    except:
        pass
    return {('h1', 'h2'): None}

def new_get_flow_table_size(self):
    try:
        # Force OpenFlow 1.3 to match the Ryu Controller!
        res = subprocess.run(['sudo', 'ovs-ofctl', 'dump-flows', 's1', '-O', 'OpenFlow13'], capture_output=True, text=True)
        if res.returncode == 0:
            return res.stdout.count('cookie=')
    except:
        pass
    return -1

# Apply the hotfixes
NetworkMonitor.ping_hosts = new_ping_hosts
NetworkMonitor.get_flow_table_size = new_get_flow_table_size


# --- SOCKET LATENCY HOTFIX ---
import socket
import time
def new_ping_hosts(self):
    latencies = {}
    # We test the connection to Host 2 (10.0.0.2) on the standard Discard port (9)
    # This forces the SDN switch to process a real packet flow
    start_time = time.time()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.0)
        s.connect(("10.0.0.2", 9))
        s.close()
    except:
        pass
    
    # Calculate the round-trip time in milliseconds
    latency = (time.time() - start_time) * 1000
    if latency < 1000:
        return {('h1', 'h2'): latency}
    return {('h1', 'h2'): None}

NetworkMonitor.ping_hosts = new_ping_hosts


# --- FORCE-COMMAND HOTFIX ---
import subprocess
def new_ping_hosts(self):
    try:
        # We force a ping from the 's1' switch perspective or the root namespace
        # to the host IP. This bypasses the namespace isolation issues.
        cmd = "ping -c 1 -W 0.5 10.0.0.2 | grep 'time=' | awk -F'time=' '{print $2}' | cut -d' ' -f1"
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if res.stdout.strip():
            return {('h1', 'h2'): float(res.stdout.strip())}
    except:
        pass
    return {('h1', 'h2'): None}

NetworkMonitor.ping_hosts = new_ping_hosts

if __name__ == '__main__':
    main()
