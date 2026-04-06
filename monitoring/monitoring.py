#!/usr/bin/env python3
"""
Network Monitoring and Metrics Collection
"""

import argparse
import logging
import time
import csv
import os
import subprocess
import psutil
import threading
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
LOG = logging.getLogger(__name__)

class NetworkMonitor:
    def __init__(self, output_dir='./results', interval=5):
        self.output_dir = output_dir
        self.interval = interval
        self.is_running = False

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        self.metrics_file = os.path.join(output_dir, 'metrics.csv')
        self.latency_file = os.path.join(output_dir, 'latency.csv')
        self.cpu_file = os.path.join(output_dir, 'cpu_memory.csv')
        self._init_csv_files()

    def _init_csv_files(self):
        headers = {
            self.metrics_file: ['Timestamp', 'Flow_Table_Size', 'Latency_ms', 'Status'],
            self.latency_file: ['Timestamp', 'Source', 'Destination', 'Latency_ms'],
            self.cpu_file: ['Timestamp', 'CPU_Percent', 'Memory_Percent', 'Memory_MB', 'Process_Count']
        }
        for file_path, row in headers.items():
            if not os.path.exists(file_path):
                with open(file_path, 'w', newline='') as f:
                    csv.writer(f).writerow(row)

    def _find_host_pid(self, host='h1'):
        iface = f'{host}-eth0'
        try:
            for pid in os.listdir('/proc'):
                if not pid.isdigit():
                    continue
                try:
                    with open(f'/proc/{pid}/net/dev', 'r') as f:
                        if iface in f.read():
                            return pid
                except (PermissionError, FileNotFoundError):
                    continue
        except Exception:
            pass
        return None

    def ping_test(self):
        target_ip = '10.0.0.2'
        pid = self._find_host_pid('h1')
        if pid:
            cmd = f'nsenter -t {pid} -n -- ping -c 1 -W 1 {target_ip}'
            try:
                res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=4)
                for line in res.stdout.split('\n'):
                    if 'time=' in line:
                        return float(line.split('time=')[1].split()[0])
            except Exception:
                pass
        
        # Fallback
        try:
            res = subprocess.run(f'ping -c 1 -W 1 {target_ip}', shell=True, capture_output=True, text=True, timeout=3)
            for line in res.stdout.split('\n'):
                if 'time=' in line:
                    return float(line.split('time=')[1].split()[0])
        except Exception:
            pass
        return None

    def get_flow_table_size(self, switch='s1'):
        try:
            res = subprocess.run(f'ovs-ofctl dump-flows {switch} -O OpenFlow13', shell=True, capture_output=True, text=True, timeout=5)
            if res.returncode == 0:
                return res.stdout.count('cookie=')
        except Exception:
            pass
        return -1

    def get_system_metrics(self):
        try:
            mem = psutil.virtual_memory()
            return {
                'cpu': psutil.cpu_percent(interval=0.1),
                'memory_percent': mem.percent,
                'memory_mb': mem.used / (1024**2),
                'process_count': len(psutil.pids()),
            }
        except Exception:
            return {'cpu': -1, 'memory_percent': -1, 'memory_mb': -1, 'process_count': -1}

    def record(self):
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        latency = self.ping_test()
        flows = self.get_flow_table_size()
        sys = self.get_system_metrics()

        with open(self.metrics_file, 'a', newline='') as f:
            csv.writer(f).writerow([ts, flows, f'{latency:.2f}' if latency else 'N/A', 'Running'])
        
        with open(self.cpu_file, 'a', newline='') as f:
            csv.writer(f).writerow([ts, f'{sys["cpu"]:.1f}', f'{sys["memory_percent"]:.1f}', f'{sys["memory_mb"]:.1f}', sys['process_count']])

        LOG.info(f'[{ts}] Flows: {flows}, Latency: {latency:.2f}ms, CPU: {sys["cpu"]:.1f}%')

    def monitor_loop(self):
        while self.is_running:
            try:
                self.record()
                time.sleep(self.interval)
            except Exception as e:
                LOG.error(f'Loop error: {e}')
                time.sleep(1)

    def start(self):
        self.is_running = True
        t = threading.Thread(target=self.monitor_loop, daemon=True)
        t.start()
        return t

    def stop(self):
        self.is_running = False

def main():
    parser = argparse.ArgumentParser(description='SDN Network Performance Monitor')
    parser.add_argument('--output-dir', default='./results')
    parser.add_argument('--interval', type=int, default=5)
    parser.add_argument('--duration', type=int, default=0)
    args = parser.parse_args()

    monitor = NetworkMonitor(output_dir=args.output_dir, interval=args.interval)
    t = monitor.start()
    try:
        if args.duration > 0:
            time.sleep(args.duration)
        else:
            t.join()
    except KeyboardInterrupt:
        pass
    finally:
        monitor.stop()

if __name__ == '__main__':
    main()
