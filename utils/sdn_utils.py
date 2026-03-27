#!/usr/bin/env python3
"""
Utility Functions for SDN Project
==================================

This module provides common utilities for the project such as:
- OpenFlow utilities
- Path validation
- Log parsing
- Flow table query helpers
"""

import subprocess
import logging
from datetime import datetime

LOG = logging.getLogger(__name__)

def query_switch_flow_table(switch_name='s1'):
    """
    Query switch flow table using ovs-ofctl
    
    Args:
        switch_name: Name of switch (e.g., 's1')
    
    Returns:
        str: Flow information or None if failed
    """
    try:
        result = subprocess.run(
            f'sudo ovs-ofctl dump-flows {switch_name} -O OpenFlow13',
            shell=True,
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            return result.stdout
        else:
            LOG.error(f'Failed to query {switch_name}: {result.stderr}')
            return None
    except Exception as e:
        LOG.error(f'Failed to query {switch_name}: {e}')
        return None

def get_flow_table_size(switch_name='s1'):
    """
    Get number of flows in switch flow table
    
    Args:
        switch_name: Name of switch
    
    Returns:
        int: Number of flows or -1 if failed
    """
    output = query_switch_flow_table(switch_name)
    if output is None:
        return -1
    
    # Count non-header, non-empty lines
    flows = [line for line in output.split('\n') 
             if line.strip() and 'cookie' in line]
    return len(flows)

def get_switch_stats(switch_name='s1'):
    """
    Get detailed switch statistics
    
    Args:
        switch_name: Name of switch
    
    Returns:
        dict: Statistics information
    """
    stats = {
        'switch': switch_name,
        'timestamp': datetime.now().isoformat(),
        'flows': get_flow_table_size(switch_name)
    }
    
    try:
        # Get port statistics
        result = subprocess.run(
            f'sudo ovs-ofctl dump-ports {switch_name} -O OpenFlow13',
            shell=True,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            stats['ports_output'] = result.stdout
        else:
            LOG.error(f'Failed to get port stats: {result.stderr}')
    except Exception as e:
        LOG.warning(f'Could not get port stats: {e}')
    
    return stats

def parse_ryu_controller_log(log_file):
    """
    Parse Ryu controller log file for key metrics
    
    Args:
        log_file: Path to log file
    
    Returns:
        dict: Extracted metrics
    """
    metrics = {
        'packet_ins': 0,
        'flows_installed': 0,
        'errors': 0
    }
    
    try:
        with open(log_file, 'r') as f:
            for line in f:
                if 'PacketIn' in line:
                    metrics['packet_ins'] += 1
                if 'Flow added' in line or 'OFPFlowMod' in line:
                    metrics['flows_installed'] += 1
                if 'ERROR' in line or 'error' in line:
                    metrics['errors'] += 1
    except Exception as e:
        LOG.error(f'Failed to parse log: {e}')
    
    return metrics

def enable_flow_logging(switch_name='s1'):
    """
    Enable flow logging on a switch for better monitoring
    
    Args:
        switch_name: Name of switch
    
    Returns:
        bool: True if successful
    """
    try:
        # Enable datapath logging for the specified switch
        result = subprocess.run(
            f'sudo ovs-vsctl set Bridge {switch_name} other_config:datapath-log-packets=true',
            shell=True,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            LOG.info(f'Enabled flow logging for {switch_name}')
            return True
        else:
            LOG.error(f'Failed to enable flow logging: {result.stderr}')
            return False
    except Exception as e:
        LOG.warning(f'Could not enable flow logging: {e}')
        return False

def clear_switch_flows(switch_name='s1'):
    """
    Clear all flows from a switch (useful for testing)
    
    WARNING: This will drop all active flows!
    
    Args:
        switch_name: Name of switch
    
    Returns:
        bool: True if successful
    """
    try:
        result = subprocess.run(
            f'sudo ovs-ofctl del-flows {switch_name}',
            shell=True,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            LOG.warning(f'Cleared all flows from {switch_name}')
            return True
        else:
            LOG.error(f'Failed to clear flows: {result.stderr}')
            return False
    except Exception as e:
        LOG.error(f'Failed to clear flows: {e}')
        return False

def start_packet_capture(interface, output_file, filter_str=''):
    """
    Start packet capture using tcpdump
    
    Args:
        interface: Interface to capture on
        output_file: Where to save capture
        filter_str: tcpdump filter expression
    
    Returns:
        subprocess.Popen: Process handle (can be terminated later), or None if failed
    """
    cmd = f'sudo tcpdump -i {interface} -w {output_file}'
    if filter_str:
        cmd += f' "{filter_str}"'
    
    try:
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if proc.poll() is None:  # Process is running
            LOG.info(f'Packet capture started on {interface} -> {output_file}')
            return proc
        else:
            LOG.error('Failed to start packet capture')
            return None
    except Exception as e:
        LOG.error(f'Failed to start capture: {e}')
        return None

def stop_packet_capture(proc):
    """
    Stop a running packet capture
    
    Args:
        proc: Process handle from start_packet_capture
    
    Returns:
        bool: True if successful
    """
    try:
        if proc:
            proc.terminate()
            proc.wait(timeout=5)
            LOG.info('Packet capture stopped')
            return True
    except Exception as e:
        LOG.error(f'Failed to stop capture: {e}')
    
    return False

class SimpleLogger:
    """
    Simple file logger for metrics and events
    """
    
    def __init__(self, log_file):
        """
        Initialize logger
        
        Args:
            log_file: File to write logs to
        """
        self.log_file = log_file
    
    def log_event(self, event_type, message):
        """
        Log an event with timestamp
        
        Args:
            event_type: Type of event (e.g., 'ATTACK', 'DEFENSE', 'METRIC')
            message: Event message
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        
        try:
            with open(self.log_file, 'a') as f:
                f.write(f'[{timestamp}] {event_type}: {message}\n')
        except Exception as e:
            LOG.error(f'Failed to write log: {e}')
    
    def log_metric(self, metric_name, value, unit=''):
        """
        Log a metric value
        
        Args:
            metric_name: Name of metric
            value: Metric value
            unit: Unit of measurement
        """
        self.log_event('METRIC', f'{metric_name}={value}{unit}')

if __name__ == '__main__':
    # Example usage
    print('Flow Table Size:', get_flow_table_size())
    print('Switch Stats:', get_switch_stats())
