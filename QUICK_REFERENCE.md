#!/usr/bin/env python3
"""
Quick Reference - Common Commands and Code Snippets
====================================================

Save this file for quick lookup of common commands and operations.
"""

# ============================================================================
#                      INSTALLATION AND SETUP
# ============================================================================

INSTALL_COMMANDS = """
# Quick Installation (Ubuntu 20.04)
sudo apt-get update
sudo apt-get install -y mininet openvswitch-switch-dpctl python3-pip
sudo pip install ryu scapy psutil pandas requests

# Verify Installation
python3 -c "import ryu; print('Ryu OK')"
python3 -c "from scapy.all import IP; print('Scapy OK')"
sudo mn --version
"""

# ============================================================================
#                      STARTING COMPONENTS
# ============================================================================

START_COMMANDS = """
# Terminal 1: Start Ryu Controller (Basic)
cd ~/SecureFlowTable/controller
ryu-manager basic_controller.py --observe-links

# Terminal 1: Start Ryu Controller (With Defense)
cd ~/SecureFlowTable/controller
ryu-manager defense_controller.py --observe-links

# Terminal 2: Start Mininet Network
cd ~/SecureFlowTable/topology
sudo python3 simple_topology.py

# Terminal 3: Inside Mininet CLI
mininet> h1 ping -c 5 h2
mininet> exit

# Terminal 4: Start Monitoring
cd ~/SecureFlowTable
sudo python3 monitoring/monitoring.py --output-dir ./results --duration 60
"""

# ============================================================================
#                      QUERY AND INSPECTION
# ============================================================================

QUERY_COMMANDS = """
# Check Flow Table Size
sudo ovs-ofctl dump-flows s1 -O OpenFlow13 | grep cookie | wc -l

# View All Flows (detailed)
sudo ovs-ofctl dump-flows s1 -O OpenFlow13

# View Specific Flow by Priority
sudo ovs-ofctl dump-flows s1 -O OpenFlow13 | grep "priority=1"

# Get Port Statistics
sudo ovs-ofctl dump-ports s1

# Monitor Port Counters
watch -n 1 'sudo ovs-ofctl dump-ports s1'

# Check Switch Configuration
sudo ovs-vsctl show

# Check Switch Protocols
sudo ovs-vsctl get Bridge s1 protocols

# Check Controller Connection
sudo ovs-vsctl get-controller s1

# Monitor Flow Table in Real-time
watch -n 0.5 'sudo ovs-ofctl dump-flows s1 -O OpenFlow13 | grep -c cookie'
"""

# ============================================================================
#                      ATTACK COMMANDS
# ============================================================================

ATTACK_COMMANDS = """
# Basic Attack (1000 packets at 100 pps)
mininet> h1 python3 /path/to/attack/attack_script.py \\
          -i h1-eth0 -d 10.0.0.2

# Aggressive Attack (5000 packets at 500 pps)
mininet> h1 python3 /path/to/attack/attack_script.py \\
          -i h1-eth0 -d 10.0.0.2 -n 5000 -r 500

# MAC-based Attack (vary source MAC)
mininet> h1 python3 /path/to/attack/attack_script.py \\
          -i h1-eth0 -d 10.0.0.2 -t mac

# Random Attack (vary both IP and MAC)
mininet> h1 python3 /path/to/attack/attack_script.py \\
          -i h1-eth0 -d 10.0.0.2 -t random

# Low-rate Attack (stealthy)
mininet> h1 python3 /path/to/attack/attack_script.py \\
          -i h1-eth0 -d 10.0.0.2 -n 1000 -r 50 -v
"""

# ============================================================================
#                      MONITORING AND ANALYSIS
# ============================================================================

MONITORING_COMMANDS = """
# Capture OpenFlow Traffic
sudo tcpdump -i lo -n tcp port 6633 -w openflow.pcap

# View Captured Traffic
sudo tcpdump -r openflow.pcap -X

# Monitor in Wireshark
sudo tcpdump -i lo tcp port 6633 -w - -W 2 | wireshark -k -i -

# Analyze CSV Data with Python
python3 << 'EOF'
import pandas as pd
data = pd.read_csv('results/baseline/metrics.csv')
print(data.describe())
print(data['Flow_Table_Size'].mean())
EOF

# Compare Test Results
python3 << 'EOF'
import pandas as pd
b = pd.read_csv('results/baseline/metrics.csv')
a = pd.read_csv('results/attack_no_defense/metrics.csv')
d = pd.read_csv('results/attack_with_defense/metrics.csv')

print("COMPARISON:")
print(f"Baseline flows: {b['Flow_Table_Size'].mean():.0f}")
print(f"Attack (no defense): {a['Flow_Table_Size'].mean():.0f}")
print(f"Attack (with defense): {d['Flow_Table_Size'].mean():.0f}")
EOF
"""

# ============================================================================
#                      CLEANUP AND RESET
# ============================================================================

CLEANUP_COMMANDS = """
# Clean Up Mininet
sudo mn -c

# Kill Ryu Controller
sudo pkill -f ryu-manager

# Kill Mininet
sudo pkill -f mininet

# Kill OVS
sudo systemctl restart openvswitch-switch

# Clear All Switches/Bridges
sudo ovs-vsctl list-br | xargs -I {} sudo ovs-vsctl del-br {}

# Verify Cleanup
sudo ovs-vsctl show  # Should be mostly empty
ps aux | grep ryu     # Should show no matches
sudo mn -c            # Should complete quickly
"""

# ============================================================================
#                      ADVANCED OPERATIONS
# ============================================================================

ADVANCED_COMMANDS = """
# Delete All Flows from Switch (WARNING!)
sudo ovs-ofctl del-flows s1 -O OpenFlow13

# Set Specific Flow Parameter
sudo ovs-vsctl -- --id=@p get port s1 -- set port @p name=s1-eth1

# Query Flow Statistics
sudo ovs-ofctl dump-aggregate s1 -O OpenFlow13

# Enable OpenFlow Logging
sudo ovs-appctl vlog/set ANY:DBG

# Get OpenFlow Module Debug Info
sudo ovs-appctl module/list

# Connect to Different Controller Port
sudo ovs-vsctl set-controller s1 tcp:127.0.0.1:6634

# Remove Controller Connection
sudo ovs-vsctl del-controller s1

# Set OpenFlow Protocol Versions
sudo ovs-vsctl set Bridge s1 other_config:datapath-type=system
"""

# ============================================================================
#                      TROUBLESHOOTING QUICK FIXES
# ============================================================================

TROUBLESHOOTING_COMMANDS = """
# Port Already in Use
sudo lsof -i :6633
sudo pkill -9 -f ryu-manager

# Permission Denied
# Always use sudo!
sudo python3 topology/simple_topology.py

# Connection Refused
# Make sure controller is running first:
ryu-manager controller/basic_controller.py &
sleep 2
sudo python3 topology/simple_topology.py

# No Ping Response
# Check flows are installed:
sudo ovs-ofctl dump-flows s1 -O OpenFlow13 | grep "output:2"

# Controller Not Responding
# Check if it's running:
ps aux | grep ryu-manager
# Check logs for errors:
ryu-manager basic_controller.py 2>&1 | tail -20

# Flow Table Not Growing
# Verify attack is sending packets:
mininet> h1 python3 attack_script.py ... -v
# Watch flow table:
watch -n 0.5 'sudo ovs-ofctl dump-flows s1 -O OF13 | grep -c cookie'
"""

# ============================================================================
#                      TEST EXECUTION TIMELINE
# ============================================================================

TEST_TIMELINE = """
TEST 1: BASELINE (No Attack)
==============================
T+0:  Start Ryu controller (Terminal 1)
T+2:  Start Mininet topology (Terminal 2)
T+5:  Verify ping works (Terminal 2: "h1 ping -c 3 h2")
T+7:  Check flow count (Terminal 3: sudo ovs-ofctl dump-flows s1 | grep -c cookie)
T+10: Start monitoring (Terminal 4)
T+15: Check flows again
T+20: Stop monitoring, exit Mininet, stop controller
Expected: ~5 flows, 1-2ms latency, 10% CPU

TEST 2: UNDER ATTACK - NO DEFENSE
===================================
T+0:  Start Ryu (basic controller) (Terminal 1)
T+2:  Start Mininet (Terminal 2)
T+5:  Start attack (Terminal 2: "h1 python3 attack_script.py...")
T+7:  Monitor flows grow rapidly
T+15: Check latency (Terminal 3: some pings may timeout)
T+20: Stop attack
T+25: Stop monitoring and cleanup
Expected: 1000+ flows, 50-200ms latency, 80%+ CPU, packet loss

TEST 3: UNDER ATTACK - WITH DEFENSE
=====================================
T+0:  Start Ryu (defense controller) (Terminal 1)
T+2:  Start Mininet (Terminal 2)
T+5:  Start attack (Terminal 2: "h1 python3 attack_script.py...")
T+7:  Monitor flows grow slowly (rate limited!)
T+15: Check latency (should be much better than test 2)
T+20: Stop attack
T+25: Stop monitoring and cleanup
Expected: ~300-500 flows, 2-5ms latency, 20-30% CPU, no packet loss
"""

# ============================================================================
#                      FILE STRUCTURE QUICK REFERENCE
# ============================================================================

FILE_REFERENCE = """
SecureFlowTable/
├── README.md                 ← Start here for overview
├── SETUP.md                  ← Installation guide
├── RUN_INSTRUCTIONS.md       ← How to run tests
├── ARCHITECTURE.md           ← System design and diagrams
├── TROUBLESHOOTING.md        ← Common issues and solutions
├── requirements.txt          ← Python dependencies
│
├── topology/
│   └── simple_topology.py   ← Mininet network creation
│
├── controller/
│   ├── basic_controller.py  ← Simple learning controller (no defense)
│   └── defense_controller.py ← Controller with defenses (rate limit, timeout, anomaly detection)
│
├── attack/
│   └── attack_script.py     ← Flow table saturation attack using Scapy
│
├── monitoring/
│   └── monitoring.py        ← Collect metrics (flows, latency, CPU, memory)
│
├── utils/
│   └── sdn_utils.py         ← Utility functions (query flows, parse logs, etc.)
│
├── logs/                    ← Created at runtime
├── results/                 ← Created at runtime
```

# ============================================================================
#                      PYTHON CODE SNIPPETS
# ============================================================================

PYTHON_SNIPPETS = {
    'analyze_metrics': '''
import pandas as pd
import matplotlib.pyplot as plt

# Load data
baseline = pd.read_csv('results/baseline/metrics.csv')
attack = pd.read_csv('results/attack_no_defense/metrics.csv')
defense = pd.read_csv('results/attack_with_defense/metrics.csv')

# Calculate statistics
print("Flow Table Size (flows):")
print(f"  Baseline:       {baseline['Flow_Table_Size'].mean():.0f}")
print(f"  Attack:         {attack['Flow_Table_Size'].mean():.0f}")
print(f"  With Defense:   {defense['Flow_Table_Size'].mean():.0f}")

print("\\nLatency (ms):")
print(f"  Baseline:       {baseline['Latency_ms'].mean():.2f}")
print(f"  Attack:         {attack['Latency_ms'].mean():.2f}")
print(f"  With Defense:   {defense['Latency_ms'].mean():.2f}")

# Create comparison plot
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
axes[0].plot(baseline.index, baseline['Flow_Table_Size'], label='Baseline')
axes[0].plot(attack.index, attack['Flow_Table_Size'], label='Attack')
axes[0].plot(defense.index, defense['Flow_Table_Size'], label='Defense')
axes[0].set_title('Flow Table Size Over Time')
axes[0].legend()
axes[0].grid(True)

axes[1].bar(['Baseline', 'Attack', 'Defense'],
            [baseline['Latency_ms'].mean(), 
             attack['Latency_ms'].mean(),
             defense['Latency_ms'].mean()])
axes[1].set_title('Average Latency Comparison')
axes[1].set_ylabel('Latency (ms)')
plt.tight_layout()
plt.savefig('comparison.png')
plt.show()
    ''',
    
    'query_flows': '''
import subprocess

def get_flows():
    result = subprocess.run(
        'sudo ovs-ofctl dump-flows s1 -O OpenFlow13',
        shell=True, capture_output=True, text=True
    )
    flows = [line for line in result.stdout.split('\\n') if 'cookie' in line]
    return len(flows)

def show_flows():
    result = subprocess.run(
        'sudo ovs-ofctl dump-flows s1 -O OpenFlow13',
        shell=True, capture_output=True, text=True
    )
    print(result.stdout)

print(f"Number of flows: {get_flows()}")
show_flows()
    ''',
    
    'parse_attack_results': '''
import json

def parse_attack_log(log_file):
    metrics = {
        'packets_sent': 0,
        'packets_failed': 0,
        'success_rate': 0,
        'duration': 0,
        'avg_rate': 0
    }
    
    with open(log_file, 'r') as f:
        for line in f:
            if 'packets sent' in line:
                # Extract numbers from log
                pass
            if 'packets failed' in line:
                pass
    
    return metrics
    '''
}

# ============================================================================
#                      QUICK START CHECKLIST
# ============================================================================

QUICK_START = """
QUICK START CHECKLIST:
======================

[ ] Install Mininet: sudo apt-get install -y mininet
[ ] Install Ryu: sudo pip install ryu
[ ] Install Scapy: sudo pip install scapy
[ ] Clone project: git clone ../SecureFlowTable
[ ] cd SEC   ureFlowTable

BASELINE TEST:
[ ] Terminal 1: ryu-manager controller/basic_controller.py --observe-links
[ ] Terminal 2: sudo python3 topology/simple_topology.py
[ ] Terminal 3: mininet> h1 ping -c 10 h2
[ ] Terminal 4: sudo python3 monitoring/monitoring.py --output-dir ./results/baseline --duration 30
[ ] Record: baseline latency and flow count
[ ] Exit Mininet: mininet> exit (Press Ctrl+C in Terminal 1)

ATTACK TEST (No Defense):
[ ] Terminal 1: ryu-manager controller/basic_controller.py --observe-links
[ ] Terminal 2: sudo python3 topology/simple_topology.py
[ ] Terminal 3: mininet> h1 python3 attack/attack_script.py -i h1-eth0 -d 10.0.0.2 -n 5000 -r 500
[ ] Terminal 4: sudo python3 monitoring/monitoring.py --output-dir ./results/attack_no_defense --duration 60
[ ] Record: flow count, latency, CPU usage
[ ] Cleanup and reset (sudo mn -c, Ctrl+C)

ATTACK TEST (With Defense):
[ ] Terminal 1: ryu-manager controller/defense_controller.py --observe-links
[ ] Terminal 2: sudo python3 topology/simple_topology.py
[ ] Terminal 3: mininet> h1 python3 attack/attack_script.py -i h1-eth0 -d 10.0.0.2 -n 5000 -r 500
[ ] Terminal 4: sudo python3 monitoring/monitoring.py --output-dir ./results/attack_with_defense --duration 60
[ ] Record: flow count, latency, CPU usage
[ ] Compare with attack (no defense) - should be better!
[ ] Cleanup

ANALYSIS:
[ ] python3 << 'EOF' ... (See code snippets above)
[ ] Compare metrics.csv from each test
[ ] Create graphs
[ ] Write report
"""

# ============================================================================
#                      PERFORMANCE EXPECTATIONS
# ============================================================================

PERFORMANCE_EXPECTATIONS = """
EXPECTED METRICS BY TEST:
=========================

BASELINE (No Attack):
- Flow count: 3-10 flows
- Latency: 0.5-2 ms
- CPU: <10%
- Memory: <100 MB
- Packet loss: 0%
- Success rate: 100%

ATTACK (No Defense):
- Flow count: 1000-5000 flows (!!)
- Latency: 50-200 ms (or timeouts)
- CPU: 80-95% (saturated!)
- Memory: 200-500 MB
- Packet loss: 20-50% (degraded service)
- Success rate: <50%

ATTACK (With Defense):
- Flow count: 300-800 flows (controlled!)
- Latency: 2-10 ms (recovered!)
- CPU: 20-35% (under control)
- Memory: 150-250 MB
- Packet loss: 0-5% (good)
- Success rate: 95%+

IMPROVEMENT METRICS:
- Flow table reduced by 75% (5000 → 500)
- Latency reduced from 100ms → 5ms (20x!)
- CPU reduced from 90% → 25% (3.6x!)
- Service maintained despite attack
"""

if __name__ == '__main__':
    print("SDN Flow Table Security Project - Quick Reference")
    print("=" * 60)
    print("\nUSAGE: View this file in a text editor or run:")
    print("  python3 quick_reference.py")
    print("\nOr search for specific topics above")
