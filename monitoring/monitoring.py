#!/usr/bin/env python3
"""
Network Monitoring and Metrics Collection
==========================================

Usage:
    sudo python3 monitoring.py --output-dir ./results --duration 60
"""

import argparse
import logging
import time
import csv
import os
import subprocess
import psutil
from datetime import datetime
import threading

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
LOG = logging.getLogger(__name__)


class NetworkMonitor:

    def __init__(self, hosts=['h1', 'h2'], output_dir='./results',
                 interval=5, controller_host='127.0.0.1'):
        self.hosts = hosts
        self.output_dir = output_dir
        self.interval = interval
        self.controller_host = controller_host
        self.is_running = False

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            LOG.info(f'Created output directory: {output_dir}')

        self.metrics_file = os.path.join(output_dir, 'metrics.csv')
        self.latency_file = os.path.join(output_dir, 'latency.csv')
        self.cpu_file     = os.path.join(output_dir, 'cpu_memory.csv')
        self._init_csv_files()
        LOG.info(f'Monitor initialized: {len(hosts)} hosts, interval={interval}s')

    # ------------------------------------------------------------------
    # CSV init
    # ------------------------------------------------------------------
    def _init_csv_files(self):
        if not os.path.exists(self.metrics_file):
            with open(self.metrics_file, 'w', newline='') as f:
                csv.writer(f).writerow(
                    ['Timestamp', 'Flow_Table_Size', 'Latency_ms',
                     'PacketIn_Rate', 'Throughput_Mbps', 'Status'])
        if not os.path.exists(self.latency_file):
            with open(self.latency_file, 'w', newline='') as f:
                csv.writer(f).writerow(
                    ['Timestamp', 'Source', 'Destination', 'Latency_ms'])
        if not os.path.exists(self.cpu_file):
            with open(self.cpu_file, 'w', newline='') as f:
                csv.writer(f).writerow(
                    ['Timestamp', 'CPU_Percent', 'Memory_Percent',
                     'Memory_MB', 'Process_Count'])

    # ------------------------------------------------------------------
    # LATENCY — find h1's pid by scanning /proc for its ethernet iface
    # ------------------------------------------------------------------
    def _find_host_pid(self, host='h1'):
        """
        Mininet puts each host in its own network namespace but does NOT
        register it with 'ip netns' by default.  The namespace is simply
        the network namespace of the bash process that mnexec spawned.

        We identify it by scanning every PID's /proc/<pid>/net/dev for
        the host's interface name (e.g. 'h1-eth0').  This works regardless
        of how Mininet labels its processes.
        """
        iface = f'{host}-eth0'
        try:
            for pid in os.listdir('/proc'):
                if not pid.isdigit():
                    continue
                net_dev = f'/proc/{pid}/net/dev'
                try:
                    with open(net_dev, 'r') as f:
                        if iface in f.read():
                            return pid
                except (PermissionError, FileNotFoundError):
                    continue
        except Exception as e:
            LOG.debug(f'_find_host_pid error: {e}')
        return None

    def ping_hosts(self):
        """
        Ping 10.0.0.2 from inside h1's network namespace using nsenter.
        Falls back to a direct ping from the root namespace if the PID
        lookup fails (covers the case where OVS bridges are reachable).
        """
        latencies = {}
        target_ip = '10.0.0.2'

        # --- Primary: nsenter into h1's namespace ---
        pid = self._find_host_pid('h1')
        if pid:
            LOG.debug(f'Found h1 namespace via PID {pid}')
            cmd = f'nsenter -t {pid} -n -- ping -c 1 -W 1 {target_ip}'
            try:
                res = subprocess.run(
                    cmd, shell=True, capture_output=True,
                    text=True, timeout=4
                )
                LOG.debug(f'nsenter stdout: {res.stdout.strip()}')
                LOG.debug(f'nsenter stderr: {res.stderr.strip()}')
                for line in res.stdout.split('\n'):
                    if 'time=' in line:
                        val = float(line.split('time=')[1].split()[0])
                        latencies[('h1', 'h2')] = val
                        return latencies
            except Exception as e:
                LOG.debug(f'nsenter ping failed: {e}')
        else:
            LOG.debug('Could not find h1 PID — trying fallback ping')

        # --- Fallback: ping from root namespace ---
        try:
            res = subprocess.run(
                f'ping -c 1 -W 1 {target_ip}',
                shell=True, capture_output=True, text=True, timeout=3
            )
            for line in res.stdout.split('\n'):
                if 'time=' in line:
                    val = float(line.split('time=')[1].split()[0])
                    latencies[('h1', 'h2')] = val
                    return latencies
        except Exception as e:
            LOG.debug(f'Fallback ping failed: {e}')

        LOG.warning('All latency strategies failed — is Mininet running?')
        latencies[('h1', 'h2')] = None
        return latencies

    # ------------------------------------------------------------------
    # FLOW TABLE SIZE
    # ------------------------------------------------------------------
    def get_flow_table_size(self, switch='s1'):
        for of_flag in ['-O OpenFlow13', '']:
            try:
                cmd = f'ovs-ofctl dump-flows {switch} {of_flag}'.strip()
                res = subprocess.run(
                    cmd, shell=True, capture_output=True, text=True, timeout=5
                )
                if res.returncode == 0:
                    return res.stdout.count('cookie=')
                LOG.debug(f'ovs-ofctl stderr: {res.stderr.strip()}')
            except Exception as e:
                LOG.debug(f'ovs-ofctl attempt failed: {e}')
        LOG.warning(f"Could not query switch '{switch}' — is Mininet running?")
        return -1

    # ------------------------------------------------------------------
    # SYSTEM METRICS
    # ------------------------------------------------------------------
    def get_system_metrics(self):
        try:
            cpu = psutil.cpu_percent(interval=0.1)
            mem = psutil.virtual_memory()
            return {
                'cpu':            cpu,
                'memory_percent': mem.percent,
                'memory_mb':      mem.used / 1024 / 1024,
                'process_count':  len(psutil.pids()),
            }
        except Exception as e:
            LOG.warning(f'Could not get system metrics: {e}')
            return {'cpu': -1, 'memory_percent': -1,
                    'memory_mb': -1, 'process_count': -1}

    # ------------------------------------------------------------------
    # RECORD
    # ------------------------------------------------------------------
    def record_metrics(self):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        latencies       = self.ping_hosts()
        flow_table_size = self.get_flow_table_size()
        sys_metrics     = self.get_system_metrics()

        valid = [l for l in latencies.values() if l is not None]
        avg_latency = sum(valid) / len(valid) if valid else -1

        with open(self.metrics_file, 'a', newline='') as f:
            csv.writer(f).writerow([
                timestamp,
                flow_table_size,
                f'{avg_latency:.2f}' if avg_latency > 0 else 'N/A',
                'N/A', 'N/A', 'Running'
            ])

        with open(self.latency_file, 'a', newline='') as f:
            w = csv.writer(f)
            for (src, dst), lat in latencies.items():
                w.writerow([timestamp, src, dst,
                            f'{lat:.2f}' if lat is not None else 'N/A'])

        with open(self.cpu_file, 'a', newline='') as f:
            csv.writer(f).writerow([
                timestamp,
                f'{sys_metrics["cpu"]:.1f}',
                f'{sys_metrics["memory_percent"]:.1f}',
                f'{sys_metrics["memory_mb"]:.1f}',
                sys_metrics['process_count'],
            ])

        LOG.info(f'[{timestamp}] Logged: flows={flow_table_size}, '
                 f'latency={avg_latency:.2f}ms, '
                 f'cpu={sys_metrics["cpu"]:.1f}%')

    # ------------------------------------------------------------------
    # LOOP
    # ------------------------------------------------------------------
    def monitor_loop(self):
        LOG.info('Starting monitoring loop...')
        try:
            while self.is_running:
                try:
                    self.record_metrics()
                    time.sleep(self.interval)
                except Exception as e:
                    LOG.error(f'Error in monitoring loop: {e}')
                    time.sleep(1)
        except KeyboardInterrupt:
            LOG.info('Monitoring interrupted by user')
        finally:
            LOG.info('Monitoring stopped')

    def start(self):
        self.is_running = True
        t = threading.Thread(target=self.monitor_loop, daemon=True)
        t.start()
        LOG.info('Monitoring thread started')
        return t

    def stop(self):
        self.is_running = False

    def generate_report(self):
        report_file = os.path.join(self.output_dir, 'summary_report.txt')
        try:
            with open(report_file, 'w') as f:
                f.write('=' * 60 + '\n')
                f.write('MONITORING SUMMARY REPORT\n')
                f.write('=' * 60 + '\n')
                f.write(f'Generated:  {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
                f.write(f'Output dir: {self.output_dir}\n')
                f.write(f'Interval:   {self.interval}s\n\n')
                f.write('Data files:\n')
                f.write(f'  {self.metrics_file}\n')
                f.write(f'  {self.latency_file}\n')
                f.write(f'  {self.cpu_file}\n')
                f.write('=' * 60 + '\n')
            LOG.info(f'Report saved to: {report_file}')
        except Exception as e:
            LOG.error(f'Failed to generate report: {e}')


# ----------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description='Monitor SDN network performance and collect metrics')
    parser.add_argument('--hosts',           nargs='+', default=['h1', 'h2'])
    parser.add_argument('--output-dir',      default='./results')
    parser.add_argument('--interval',        type=int, default=5)
    parser.add_argument('--controller-host', default='127.0.0.1')
    parser.add_argument('--duration',        type=int, default=0,
                        help='Seconds to run (0 = infinite)')
    args = parser.parse_args()

    monitor = NetworkMonitor(
        hosts=args.hosts,
        output_dir=args.output_dir,
        interval=args.interval,
        controller_host=args.controller_host,
    )

    t = monitor.start()
    try:
        if args.duration > 0:
            LOG.info(f'Monitoring for {args.duration} seconds...')
            time.sleep(args.duration)
        else:
            LOG.info('Monitoring started (Ctrl+C to stop)...')
            t.join()
    except KeyboardInterrupt:
        LOG.info('Interrupted by user')
    finally:
        monitor.stop()
        monitor.generate_report()
        LOG.info('Monitoring complete')


if __name__ == '__main__':
    main()
