# SecureFlowTable: SDN Flow Table Security

A project demonstrating flow table saturation attacks in Software Defined Networks (SDN) and implementing defense mechanisms.

## Overview

In SDN, a centralized controller manages switch flow rules via OpenFlow. This project explores **flow table saturation attacks**, where an attacker sends high-entropy traffic (spoofed MAC/IPs) to exhaust the switch's flow table capacity and overload the controller CPU.

### Features
- **Topology**: Mininet-based SDN (1 switch, 2 hosts).
- **Attack**: Scapy-based high-speed MAC flooding.
- **Defense**: Ryu controller with rate limiting, flow timeout reduction, and anomaly detection.
- **Monitoring**: Real-time metrics collection (latency, flow table size, resource usage).

## Installation

### Prerequisites
- Ubuntu 20.04+
- Python 3.6+
- Sudo access

### Dependencies
```bash
# System packages
sudo apt-get update
sudo apt-get install -y mininet openvswitch-switch python3-pip python3-scapy

# Python requirements
sudo pip install ryu
pip install -r requirements.txt
```

## Usage

### 1. Basic Switch (Baseline/Attack)
1. **Controller**: `ryu-manager controller/basic_controller.py`
2. **Topology**: `sudo python3 topology/simple_topology.py`
3. **Attack**: `sudo python3 attack/fast_attack.py`

### 2. Defense Mode
1. **Controller**: `ryu-manager controller/defense_controller.py`
2. **Topology**: `sudo python3 topology/simple_topology.py`
3. **Monitoring**: `sudo python3 monitoring/monitoring.py --duration 60`

## Project Structure
- `controller/`: Ryu implementations (`basic` vs `defense`).
- `attack/`: MAC flooding script.
- `monitoring/`: Metrics collection (latency, CPU, flows).
- `topology/`: Mininet network script.

## Results
Data is logged to the `results/` directory:
- `metrics.csv`: Flow table size and latency.
- `cpu_memory.csv`: System resource usage.
- `latency.csv`: Raw latency measurements.
