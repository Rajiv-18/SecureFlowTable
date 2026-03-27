# Running the Project - Step-by-Step Instructions

This document provides detailed instructions for running each test scenario.

## Before You Start

1. Installation must be complete (see [SETUP.md](SETUP.md))
2. Have 4 terminal windows open
3. All tests require **sudo** for network operations
4. Each test takes 5-10 minutes to run

## Important Notes

- **Always run Mininet with sudo**: `sudo python3`
- **Always run Ryu controller first** before starting Mininet
- **Close previous instances**: Press Ctrl+C to stop, wait 5 seconds before restarting
- **Port 6633**: Free this port between tests (`sudo pkill -f ryu-manager`)

---

## Test 1: Baseline Network (No Attack)

**Duration**: ~10 minutes

This test establishes a baseline of normal network behavior without any attack.

### Step 1.1: Start Ryu Controller

**Terminal 1:**
```bash
cd ~/SecureFlowTable/controller

# Start basic controller
ryu-manager basic_controller.py --observe-links

# Expected output:
# loading app ryu.controller.ofp_event
# loading app basic_controller
# WARNING openstacknetworking (...)
# (1234) wsgi starting up on 0.0.0.0:8080
```

**Status**: Leave this terminal open and running

---

### Step 1.2: Start Mininet Network

**Terminal 2:**
```bash
cd ~/SecureFlowTable/topology

# Start the network
sudo python3 simple_topology.py

# You should see:
# *** Creating Network Topology
# *** Creating switches
# *** Creating hosts
# *** Creating links
# *** Starting Network
# *** Network is running
```

**Status**: This will show a Mininet CLI prompt: `mininet>`

---

### Step 1.3: Test Connectivity

**Terminal 2 (at mininet> prompt):**
```bash
mininet> h1 ping -c 10 h2

# Expected output:
# PING 10.0.0.2 from 10.0.0.1
# 64 bytes from 10.0.0.1: icmp_seq=1 ttl=64 time=0.5 ms
# ...
# 10 packets transmitted, 10 received, 0% packet loss, time 9 ms
```

**Record this**: Baseline latency should be 0.5-1.5 ms

---

### Step 1.4: Check Flow Table

**Terminal 3:**
```bash
cd ~/SecureFlowTable

# Query the switch flow table
sudo ovs-ofctl dump-flows s1 -O OpenFlow13

# Expected output:
# OFPST_FLOW reply (xid=0x4):
#  cookie=0x0, duration_sec=XX, table=0, n_packets=XX, n_bytes=XX, idle_age=XX, priority=0, 
#  match=all, actions=CONTROLLER:65535
#  cookie=..., idle_age=2, priority=1, ..., actions=output:1
#  cookie=..., idle_age=2, priority=1, ..., actions=output:2
```

Count flows (lines with "cookie"):
```bash
sudo ovs-ofctl dump-flows s1 -O OpenFlow13 | grep cookie | wc -l

# For baseline: should be 3-5 flows
```

**Record this**: Baseline flow count

---

### Step 1.5: Monitor Metrics (Optional)

**Terminal 4:**
```bash
cd ~/SecureFlowTable

# Start monitoring for 60 seconds
sudo python3 monitoring/monitoring.py \
  --output-dir ./results/baseline \
  --interval 5 \
  --duration 60

# This creates:
# results/baseline/metrics.csv
# results/baseline/latency.csv
# results/baseline/cpu_memory.csv
```

---

### Step 1.6: Cleanup

**Terminal 2 (at mininet> prompt):**
```bash
mininet> exit

# Expected output:
# All flows have been evacuated
# *** Stopping network
# *** Network stopped
```

**Terminal 1**: Press Ctrl+C to stop Ryu controller

**Wait 5 seconds before starting next test**

---

## Test 2: Under Attack (Without Defense)

**Duration**: ~15 minutes

This test shows what happens when the network is attacked WITHOUT defense mechanisms.

### Step 2.1: Start Ryu Controller (Basic, No Defense)

**Terminal 1:**
```bash
cd ~/SecureFlowTable/controller

# Start basic controller (NOT defense controller)
ryu-manager basic_controller.py --observe-links

# Status: Running and ready for attack
```

---

### Step 2.2: Start Mininet Network

**Terminal 2:**
```bash
cd ~/SecureFlowTable/topology

sudo python3 simple_topology.py

# Status: Waiting at mininet> prompt
```

---

### Step 2.3: Verify Connectivity (Before Attack)

**Terminal 2:**
```bash
mininet> h1 ping -c 3 h2

# Should respond normally
```

---

### Step 2.4: Launch Attack

**Terminal 2 (at mininet> prompt):**
```bash
# Option 1: Default attack (1000 packets at 100 pps)
mininet> h1 python3 /path/to/attack/attack_script.py \
  -i h1-eth0 \
  -d 10.0.0.2

# Option 2: Aggressive attack (5000 packets at 500 pps)
mininet> h1 python3 /path/to/attack/attack_script.py \
  -i h1-eth0 \
  -d 10.0.0.2 \
  -n 5000 \
  -r 500

# Expected output:
# Attack initialized: interface=h1-eth0, target=10.0.0.2, packets=5000, rate=500pps, type=ip
# Starting attack: sending 5000 packets at 500 pps...
# Progress: 100/5000 packets sent (500.0 pps, elapsed: 0.2s)
# Progress: 200/5000 packets sent (500.0 pps, elapsed: 0.4s)
# ...
```

**Status**: Attack is running. Let it continue.

---

### Step 2.5: Monitor Attack Progress (In Different Terminal)

**Terminal 3 (while attack is running):**
```bash
# Check flow table size in real-time
watch -n 1 'sudo ovs-ofctl dump-flows s1 -O OpenFlow13 | grep cookie | wc -l'

# You'll see flow count rapidly increasing:
# Every 1.0s: sudo ovs-ofctl...
#
# 100 # at 10 seconds
# 500 # at 50 seconds
# 2000 # at 200 seconds
```

Press Ctrl+C to stop watching.

---

### Step 2.6: Test Connectivity Under Attack

**Terminal 2 (while attack is in progress, in another window/tab):**

Open a new terminal and SSH into the mininet h1 host, then:

```bash
# From outside mininet, test latency
mininet> h2 tcpdump -i h2-eth0 -c 5

# Back in original window, try ping from h1
# Wait to see if it responds
```

**Expected Observations**:
- Flow table fills rapidly (>1000 flows)
- Ping may timeout or show high latency (50-200ms)
- CPU usage spikes on controller terminal output

---

### Step 2.7: Collect Metrics During Attack

**Terminal 4:**
```bash
# Wait for attack to start, then begin monitoring
sleep 5

# Monitor while attack is running
sudo python3 monitoring/monitoring.py \
  --output-dir ./results/attack_no_defense \
  --interval 2 \
  --duration 120  # Monitor for 2 minutes

# Creates metrics files:
# results/attack_no_defense/metrics.csv
# results/attack_no_defense/latency.csv
# results/attack_no_defense/cpu_memory.csv
```

---

### Step 2.8: Cleanup

After attack completes and monitoring stops:

**Terminal 2:**
```bash
mininet> exit
```

**Terminal 1:** Ctrl+C

**Wait 5 seconds**

---

## Test 3: Under Attack (With Defense)

**Duration**: ~15 minutes

This test runs the same attack but with defense mechanisms active.

### Step 3.1: Start Ryu Controller (With Defense)

**Terminal 1:**
```bash
cd ~/SecureFlowTable/controller

# Start defense controller (NOT basic controller)
ryu-manager defense_controller.py --observe-links

# Expected output (note "DefenseController" instead of "BasicController"):
# loading app defense_controller
# DefenseController initialized with defense mechanisms
# Rate limit: 100 PacketIns/sec
# Flow timeouts: idle=10s, hard=30s
```

---

### Step 3.2: Start Mininet Network

**Terminal 2:**
```bash
cd ~/SecureFlowTable/topology

sudo python3 simple_topology.py
```

---

### Step 3.3: Verify Connectivity (Before Attack)

**Terminal 2:**
```bash
mininet> h1 ping -c 3 h2
```

---

### Step 3.4: Launch Same Attack

**Terminal 2:**
```bash
# Use same attack as Test 2
mininet> h1 python3 /path/to/attack/attack_script.py \
  -i h1-eth0 \
  -d 10.0.0.2 \
  -n 5000 \
  -r 500

# Attack starts - note the defense controller is active
```

---

### Step 3.5: Monitor Flow Table With Defense

**Terminal 3:**
```bash
# Watch flow count - should grow MUCH slower with defense
watch -n 1 'sudo ovs-ofctl dump-flows s1 -O OpenFlow13 | grep cookie | wc -l'

# Expected behavior:
# ~100 flows (stays relatively constant)
# Much slower growth than Test 2
# Some flows removed due to timeout
```

---

### Step 3.6: Test Connectivity With Defense

During attack in test 2 (without defense), connectivity degraded. Now test if it's better:

```bash
mininet> h2 ping -c 10 h1

# Latency should be:
# - Better than Test 2 (without defense)
# - Slightly worse than Test 1 baseline
# - Typically 2-10ms (vs 50-200ms without defense)
```

---

### Step 3.7: Collect Metrics With Defense

**Terminal 4:**
```bash
sleep 5

sudo python3 monitoring/monitoring.py \
  --output-dir ./results/attack_with_defense \
  --interval 2 \
  --duration 120

# Creates comparison data for defense analysis
```

---

### Step 3.8: Cleanup

After test completes:

**Terminal 2:**
```bash
mininet> exit
```

**Terminal 1:** Ctrl+C

---

## Comparison and Analysis

After running all three tests, you have three result directories:

```bash
cd ~/SecureFlowTable/results

# List collected data
ls -la baseline/
ls -la attack_no_defense/
ls -la attack_with_defense/

# View CSV files
cat baseline/metrics.csv
cat attack_no_defense/metrics.csv
cat attack_with_defense/metrics.csv
```

### Create Comparison Analysis

```bash
cd ~/SecureFlowTable

# Using Python to analyze
python3 << 'EOF'
import pandas as pd
import matplotlib.pyplot as plt

# Load data
baseline = pd.read_csv('results/baseline/metrics.csv')
attack_no_def = pd.read_csv('results/attack_no_defense/metrics.csv')
attack_with_def = pd.read_csv('results/attack_with_defense/metrics.csv')

# Compare flow table sizes
print("FLOW TABLE SIZE COMPARISON:")
print(f"Baseline: {baseline['Flow_Table_Size'].mean():.0f} average flows")
print(f"Attack (no defense): {attack_no_def['Flow_Table_Size'].mean():.0f} average flows")
print(f"Attack (with defense): {attack_with_def['Flow_Table_Size'].mean():.0f} average flows")

# Compare latencies
print("\nLATENCY COMPARISON (ms):")
print(f"Baseline: {baseline['Latency_ms'].mean():.2f}ms")
print(f"Attack (no defense): {attack_no_def['Latency_ms'].mean():.2f}ms")
print(f"Attack (with defense): {attack_with_def['Latency_ms'].mean():.2f}ms")
EOF
```

---

## Advanced Tests

### Test 4: Different Attack Rates

Try attacking at different packet rates:

```bash
# Low rate attack (easy to defend)
mininet> h1 python3 attack_script.py -i h1-eth0 -d 10.0.0.2 -n 1000 -r 50

# Medium rate attack
mininet> h1 python3 attack_script.py -i h1-eth0 -d 10.0.0.2 -n 2000 -r 200

# High rate attack
mininet> h1 python3 attack_script.py -i h1-eth0 -d 10.0.0.2 -n 5000 -r 1000
```

### Test 5: Different Attack Types

The attack script supports different variation types:

```bash
# IP variation (default)
mininet> h1 python3 attack_script.py -i h1-eth0 -d 10.0.0.2 -t ip

# MAC variation
mininet> h1 python3 attack_script.py -i h1-eth0 -d 10.0.0.2 -t mac

# Random (both IP and MAC)
mininet> h1 python3 attack_script.py -i h1-eth0 -d 10.0.0.2 -t random
```

### Test 6: Inspect Flow Table Details

```bash
# Detailed flow information
sudo ovs-ofctl dump-flows s1 -O OpenFlow13

# Count flows by priority
sudo ovs-ofctl dump-flows s1 -O OpenFlow13 | grep "priority=" | sort | uniq -c

# Monitor in real-time (update every 1 second)
watch -n 1 'sudo ovs-ofctl dump-flows s1 -O OpenFlow13 | tail -20'

# Capture OpenFlow messages
sudo tcpdump -i lo -n tcp port 6633 -w openflow.pcap
```

---

## Troubleshooting During Tests

### Issue: Mininet won't start
```bash
# Clean up previous Mininet instances
sudo mn -c

# Check if ports are in use
netstat -tlnp | grep 6633

# Kill rogue processes
sudo pkill -f ryu-manager
sudo pkill -f mininet
sudo pkill -f ovsdb-server
```

### Issue: Attack script won't run in Mininet
```bash
# Make sure script is accessible
mininet> h1 ls -la /path/to/attack/attack_script.py

# Try running with full Python path
mininet> h1 python3 /path/to/attack/attack_script.py -i h1-eth0 -d 10.0.0.2
```

### Issue: No ping response during attack
```bash
# This is normal - attack is overwhelming the controller
# With defense, ping latency should recover to  acceptable levels

# If ping never works, check connectivity before attack:
mininet> h1 ping -c 5 h2  # Should work before attack
```

### Issue: High CPU even with defense
```bash
# Defense mechanisms have limits
# Try reducing attack rate:
mininet> h1 python3 attack_script.py -i h1-eth0 -d 10.0.0.2 -n 1000 -r 100

# Or reduce monitoring interval to reduce observer overhead
```

---

## Data Analysis

After collecting data, analyze it:

```bash
# Generate comparison graphs
python3 << 'EOF'
import pandas as pd
import matplotlib.pyplot as plt

# Load all datasets
baseline = pd.read_csv('results/baseline/metrics.csv')
no_def = pd.read_csv('results/attack_no_defense/metrics.csv')
with_def = pd.read_csv('results/attack_with_defense/metrics.csv')

# Create figure with multiple subplots
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Plot 1: Flow table size over time
axes[0, 0].plot(baseline.index, baseline['Flow_Table_Size'], label='Baseline', marker='.')
axes[0, 0].plot(no_def.index, no_def['Flow_Table_Size'], label='Attack (No Defense)', marker='.')
axes[0, 0].plot(with_def.index, with_def['Flow_Table_Size'], label='Attack (With Defense)', marker='.')
axes[0, 0].set_title('Flow Table Size Comparison')
axes[0, 0].set_xlabel('Time (samples)')
axes[0, 0].set_ylabel('Number of Flows')
axes[0, 0].legend()
axes[0, 0].grid(True)

# Plot 2: Latency comparison
axes[0, 1].bar(['Baseline', 'No Defense', 'With Defense'],
              [baseline['Latency_ms'].mean(), no_def['Latency_ms'].mean(), with_def['Latency_ms'].mean()])
axes[0, 1].set_title('Average Latency Comparison')
axes[0, 1].set_ylabel('Latency (ms)')
axes[0, 1].grid(True, axis='y')

# Plot 3: CPU Usage
cpu_baseline = pd.read_csv('results/baseline/cpu_memory.csv')
cpu_no_def = pd.read_csv('results/attack_no_defense/cpu_memory.csv')
cpu_with_def = pd.read_csv('results/attack_with_defense/cpu_memory.csv')

axes[1, 0].plot(cpu_baseline.index, cpu_baseline['CPU_Percent'], label='Baseline', marker='.')
axes[1, 0].plot(cpu_no_def.index, cpu_no_def['CPU_Percent'], label='Attack (No Defense)', marker='.')
axes[1, 0].plot(cpu_with_def.index, cpu_with_def['CPU_Percent'], label='Attack (With Defense)', marker='.')
axes[1, 0].set_title('CPU Usage Over Time')
axes[1, 0].set_xlabel('Time (samples)')
axes[1, 0].set_ylabel('CPU %')
axes[1, 0].legend()
axes[1, 0].grid(True)

# Plot 4: Summary table
summary_data = {
    'Baseline': [baseline['Flow_Table_Size'].mean(), baseline['Latency_ms'].mean()],
    'Attack (No Defense)': [no_def['Flow_Table_Size'].mean(), no_def['Latency_ms'].mean()],
    'Attack (With Defense)': [with_def['Flow_Table_Size'].mean(), with_def['Latency_ms'].mean()]
}

axes[1, 1].axis('off')
summary_text = "SUMMARY STATISTICS\n\n"
for scenario, values in summary_data.items():
    summary_text += f"{scenario}:\n"
    summary_text += f"  Avg Flows: {values[0]:.0f}\n"
    summary_text += f"  Avg Latency: {values[1]:.2f}ms\n\n"
axes[1, 1].text(0.1, 0.5, summary_text, fontsize=10, family='monospace')

plt.tight_layout()
plt.savefig('comparison_analysis.png', dpi=150)
print("Graph saved to comparison_analysis.png")
EOF
```

---

## Next Steps

After running tests:

1. **Analyze Data**: Create graphs from CSV files (see above)
2. **Document Results**: Record flow table sizes, latencies, CPU usage
3. **Write Report**: Prepare presentation with screenshots and metrics
4. **Improvement Ideas**: Consider optimizations from [README.md](README.md) Future Improvements section

---

See [README.md](README.md) for full documentation and [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for additional help.
