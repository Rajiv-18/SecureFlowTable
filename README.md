# Flow Table Security in Software Defined Networks (SDN)

## Project Overview

This project demonstrates **flow table saturation attacks** in Software Defined Networks (SDN) and implements **defense mechanisms** to mitigate the impact.

### What is this project about?

In traditional networks, switches independently learn network topology. In SDN, a centralized controller manages all switches. When an attacker sends many unique packets, it forces the controller to install many flow rules (flows) in the switch's flow table. This is called a **flow table saturation attack**.

The attack impacts:
- **Flow table memory**: Limited space gets filled with attack flows
- **Controller CPU**: Excessive PacketIn messages overload the controller
- **Network latency**: Processing delays increase significantly
- **Legitimate traffic**: May be dropped or delayed

This project shows how the attack works and how to defend against it.

---

## Project Structure

```
SecureFlowTable/
├── README.md                          # This file
├── SETUP.md                           # Installation and setup instructions
├── ARCHITECTURE.md                    # Architecture diagram and explanations
├── requirements.txt                   # Python dependencies
├── RUN_INSTRUCTIONS.md               # Step-by-step execution guide
├── TROUBLESHOOTING.md                # Common issues and solutions
│
├── topology/                          # Network topology scripts
│   └── simple_topology.py            # Mininet topology with 2 hosts and 1 switch
│
├── controller/                        # Ryu controller implementations
│   ├── basic_controller.py           # Basic L2 learning controller
│   └── defense_controller.py         # Controller with defense mechanisms
│
├── attack/                            # Attack simulation scripts
│   └── attack_script.py              # Scapy-based flow saturation attack
│
├── monitoring/                        # Network monitoring and metrics
│   └── monitoring.py                 # Metrics collection and analysis
│
├── utils/                             # Utility functions and helpers
│   └── sdn_utils.py                  # Common SDN utilities
│
├── logs/                              # Log files (generated during execution)
│   ├── controller.log
│   ├── attack.log
│   └── network.log
│
└── results/                           # Collected metrics and results
    ├── metrics.csv                   # Performance metrics over time
    ├── latency.csv                   # Latency measurements
    ├── cpu_memory.csv                # System resource usage
    └── summary_report.txt            # Generated summary report
```

---

## Quick Start

### Prerequisites
- Linux system (Ubuntu 20.04 recommended)
- Python 3.6+
- Root/sudo access (required for Mininet and packet operations)

### Installation (5 minutes)

```bash
# 1. Clone the repository
cd ~/SecureFlowTable

# 2. Install system dependencies
sudo apt-get update
sudo apt-get install -y mininet openvswitch-switch-dpctl openvswitch-common

# 3. Install Ryu controller
sudo pip install ryu

# 4. Install Python requirements
sudo pip install -r requirements.txt
```

### Run a Basic Test (10 minutes)

```bash
# Terminal 1: Start the Ryu controller
cd controller/
ryu-manager basic_controller.py --observe-links

# Terminal 2: Start Mininet network
cd topology/
sudo python3 simple_topology.py

# Terminal 3: Test basic connectivity
# (Inside Mininet CLI)
mininet> h1 ping h2
mininet> exit

# Terminal 4: Start monitoring (optional)
cd monitoring/
sudo python3 monitoring.py --duration 30
```

---

## Understanding the Project

### 1. Network Topology

The script creates a **simple SDN topology**:

```
    [Controller]
         |
         | OpenFlow
         |
    [Switch: s1]
      /      \
   [h1]      [h2]
   (Host 1)  (Host 2)
```

**Components:**
- **Controller**: Ryu OpenFlow controller (port 6633)
- **Switch**: OVS (Open vSwitch) with OpenFlow support
- **Hosts**: Simple network nodes with IP addresses

### 2. Attack Mechanism

The attack script sends **unique packets** with varying:
- **Source IP addresses**: 10.0.0.1, 10.0.0.2, 10.0.0.3, ...
- **Destination ports**: 5000, 5001, 5002, ...
- **Source MAC addresses** (optional): 00:00:00:00:00:01, 00:00:00:00:00:02, ...

Each unique packet creates a **new flow rule** in the switch:

```
Flow Rule Example:
Match: (src_ip=10.0.0.5, dst_ip=10.0.0.2, sport=5045, dport=80)
Action: Forward to port 1
Timeout: 60 seconds

With 1000 unique packets = 1000 flow rules!
```

**Impact on the Network:**
1. Controller receives many PacketIn messages (one for each unique packet)
2. Controller processes each packet and installs a flow rule
3. Switch's flow table fills up
4. CPU usage increases, latency increases
5. Network performance degrades

### 3. Defense Mechanisms

The `defense_controller.py` implements three defenses:

#### Defense 1: **Packet-in Rate Limiting**
```
Without Defense: 1000+ PacketIns/second
With Defense: Max 100 PacketIns/second
Impact: Reduces CPU load on controller
```

#### Defense 2: **Flow Timeout Reduction**
```
Without Defense: Flow timeout = 60 seconds
With Defense: Flow timeout = 10 seconds (idle) + 30 seconds (hard)
Impact: Forces flows to be evicted faster, freeing flow table space
```

#### Defense 3: **Anomaly Detection**
```
Detects:
- Suspicious traffic patterns (too many flows from one source)
- ARP flooding
- High-entropy source IPs
Action: Drop suspicious packets before processing
```

### 4. Monitoring and Metrics

The monitoring script collects:
- **Flow table size**: Number of flows installed
- **Latency**: Ping time between hosts
- **CPU usage**: System CPU percentage
- **Memory usage**: Amount of RAM used
- **PacketIn rate**: Controller load

These are saved to CSV files for analysis and graphing.

---

## Running Complete Tests

### Test 1: Baseline (No Attack)

```bash
# Terminal 1
ryu-manager controller/basic_controller.py --observe-links

# Terminal 2
sudo python3 topology/simple_topology.py

# Terminal 3 (inside Mininet)
mininet> h1 ping -c 100 h2

# Terminal 4
sudo python3 monitoring/monitoring.py --output-dir ./results/baseline --duration 30
```

**Expected Results:**
- Low PacketIn rate (only for unknown destinations)
- Few flows in table
- Low latency (~1-5ms)
- Low CPU usage

### Test 2: Under Attack (Without Defense)

```bash
# Terminal 1
ryu-manager controller/basic_controller.py --observe-links

# Terminal 2
sudo python3 topology/simple_topology.py

# Terminal 3 (inside Mininet)
mininet> h1 python3 /path/to/attack/attack_script.py -i h1-eth0 -d 10.0.0.2 -n 5000 -r 500

# Terminal 4
sudo python3 monitoring/monitoring.py --output-dir ./results/attack --duration 60
```

**Expected Results:**
- High PacketIn rate (500+/second)
- Many flows in table (5000+)
- Increased latency (may see timeouts)
- High CPU usage

### Test 3: Under Attack (With Defense)

```bash
# Terminal 1
ryu-manager controller/defense_controller.py --observe-links

# Terminal 2
sudo python3 topology/simple_topology.py

# Terminal 3 (inside Mininet)
mininet> h1 python3 /path/to/attack/attack_script.py -i h1-eth0 -d 10.0.0.2 -n 5000 -r 500

# Terminal 4
sudo python3 monitoring/monitoring.py --output-dir ./results/defense --duration 60
```

**Expected Results:**
- Controlled PacketIn rate (capped at 100/second)
- Fewer flows in table (rate limiting prevents massive accumulation)
- Lower latency than under attack (but higher than baseline)
- Lower CPU usage compared to undefended attack

---

## Collecting Metrics and Data

### Flow Table Inspection

```bash
# Query current flows in switch (requires root)
sudo ovs-ofctl dump-flows s1 -O OpenFlow13

# Get count of flows
sudo ovs-ofctl dump-flows s1 -O OpenFlow13 | grep cookie | wc -l

# Get port statistics
sudo ovs-ofctl dump-ports s1 -O OpenFlow13
```

### OpenFlow Traffic Capture

```bash
# Capture OpenFlow messages between switch and controller
sudo tcpdump -i lo -w openflow_traffic.pcap -X tcp port 6633

# View in Wireshark
wireshark openflow_traffic.pcap
```

### Controller Logs

```bash
# Save Ryu controller output
ryu-manager controller/defense_controller.py > controller.log 2>&1

# Analyze packet-in rates
grep "PacketIn" controller.log | wc -l

# Look for attacks detected
grep "Suspicious\|Anomaly\|Detecting" controller.log
```

---

## Understanding the Code

### Key Concepts in `basic_controller.py`

```python
# PacketIn: A packet that doesn't match any flow rule
# When this happens, switch sends packet to controller

@set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
def packet_in_handler(self, ev):
    # Controller learns source MAC
    # Installs flow rule to avoid future PacketIns
```

### Key Concepts in `defense_controller.py`

```python
# Defense 1: Rate Limiting
def check_rate_limit(self, dpid):
    if len(self.packet_in_timestamps[dpid]) >= self.max_packet_in_per_sec:
        return False  # Drop packet
    return True

# Defense 2: Reduced Timeouts
idle_timeout=10,        # Remove flows after 10s of inactivity
hard_timeout=30         # Remove flows after 30s max

# Defense 3: Anomaly Detection
def is_suspicious_source(self, dpid, src_ip):
    if self.source_ip_flows[dpid][src_ip] > self.max_flows_per_source:
        return True  # Too many flows from this source
```

### Key Concepts in `attack_script.py`

```python
# Generate unique packets
for i in range(num_packets):
    src_ip = f'10.0.0.{(i % 254) + 1}'  # Vary source IP
    pkt = IP(src=src_ip, dst=target_ip) / TCP(sport=5000+i)
    send(pkt)
```

---

## Report Suggestions

### Screenshots to Include

1. **Network Topology Diagram**
   - Show the MinMet topology graphically
   - Indicate controller, switch, and hosts

2. **Flow Table Size Over Time**
   - Graph showing flow table growth during attack
   - Graph showing controlled growth with defense

3. **Latency Measurements**
   - Graph showing latency increase under attack
   - Comparison with and without defense

4. **CPU Usage**
   - CPU spiking during attack without defense
   - Controlled CPU with defense activated

5. **PacketIn Rate**
   - Showing rate limiting in action

### Key Metrics to Report

| Metric | Baseline | Under Attack | With Defense |
|--------|----------|-------------|--------------|
| Flow Table Size | <50 | >5000 | <500 |
| Avg Latency | 1-2ms | 50-100ms | 3-5ms |
| PacketIn Rate | <100/s | >1000/s | <100/s |
| CPU Usage | <10% | >80% | <30% |
| Successful Packets | >99% | <50% | >95% |

### Data for Analysis

Use the CSV files in `results/`:
- `metrics.csv`: Main performance data
- `latency.csv`: Per-flow latency measurements
- `cpu_memory.csv`: System resource usage

**How to analyze:**
```python
import pandas as pd
import matplotlib.pyplot as plt

# Load data
baseline = pd.read_csv('results/baseline/metrics.csv')
attack = pd.read_csv('results/attack/metrics.csv')
defense = pd.read_csv('results/defense/metrics.csv')

# Plot comparison
plt.figure(figsize=(12, 6))
plt.plot(baseline['Timestamp'], baseline['Flow_Table_Size'], label='Baseline')
plt.plot(attack['Timestamp'], attack['Flow_Table_Size'], label='Under Attack')
plt.plot(defense['Timestamp'], defense['Flow_Table_Size'], label='With Defense')
plt.legend()
plt.xlabel('Time')
plt.ylabel('Flow Table Size')
plt.title('Flow Table Size Comparison')
plt.show()
```

---

## Troubleshooting

### Common Issues

#### "Permission denied" errors
```bash
# Solution: Run with sudo
sudo python3 topology/simple_topology.py
```

#### Mininet not installed
```bash
# Solution: Install Mininet
sudo apt-get install mininet
```

#### Ryu controller not found
```bash
# Solution: Install Ryu
sudo pip install ryu
```

#### Port 6633 already in use
```bash
# Solution: Kill existing Ryu process
sudo pkill -f "ryu-manager"
```

#### Scapy errors
```bash
# Solution: Install Scapy
sudo pip install scapy

# Or upgrade Scapy
sudo pip install --upgrade scapy
```

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for more issues and solutions.

---

## Future Improvements

### Defense Enhancements

1. **Machine Learning Detection**
   - Train ML model to detect attack patterns
   - Use clustering algorithms on source IP distributions

2. **Intelligent Flow Eviction**
   - Preferentially remove flows that match attack patterns
   - Keep legitimate flows longer

3. **Dynamic Timeout Adjustment**
   - Adjust timeouts based on current attack level
   - More aggressive during high-traffic periods

4. **Flow Aggregation**
   - Group similar flows into one rule
   - Reduce flow table pressure

### Monitoring Enhancements

1. **Real-time Dashboard**
   - Live web interface showing metrics
   - Real-time flow table visualization

2. **Alert System**
   - Send alerts when attacks detected
   - Automatic defense activation threshold

3. **Historical Analysis**
   - Long-term trend analysis
   - Prediction of attack before full saturation

### Testing Improvements

1. **Multiple Topology Scenarios**
   - Test on larger topologies (10+ hosts)
   - Test on more complex networks

2. **Different Attack Types**
   - Test with different packet patterns
   - Test fragmented packets

3. **Comparison with Other Defenses**
   - Implement blocking-based defenses
   - Compare effectiveness of different strategies

---

## Learning Resources

### SDN and OpenFlow
- [OpenFlow Official Specification](https://www.opennetworking.org/)
- [Ryu Documentation](https://ryu.readthedocs.io/)
- [Mininet Documentation](http://mininet.org/)

### Python Networking
- [Scapy Comprehensive Guide](https://scapy.rtfd.io/)
- [Python Socket Programming](https://docs.python.org/3/library/socket.html)

### Network Security
- [NIST SDN Security Guidelines](https://nvlpubs.nist.gov/)
- [DDoS Mitigation Techniques](https://www.rfc-editor.org/)

---

## Project Authors & Contributions

This is a university project for learning SDN security concepts.

**Learning Objectives:**
- Understand SDN architecture and OpenFlow protocol
- Learn about network security vulnerabilities
- Design and implement security mechanisms
- Measure and analyze system performance
- Document technical findings

---

## License

Educational use only. Please credit appropriately in academic work.

---

## Questions & Support

For issues or questions:
1. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. Review code comments and docstrings
3. Check Ryu and Mininet official documentation
4. Test with simpler scenarios first

---

**Last Updated:** 2024
**Version:** 1.0
