# Troubleshooting Guide

Solutions to common problems when running the SDN Flow Table Security project.

## Installation and Setup Issues

### Issue 1: "mn: command not found"

**Error**: Mininet is not installed or not in PATH

**Solutions**:

```bash
# Option 1: Install from package manager
sudo apt-get install -y mininet

# Option 2: Check if installed
which mn
/usr/bin/mn  # If you see this, it's installed

# Option 3: Add to PATH if installed to non-standard location
echo "export PATH=$PATH:/opt/onf/mininet/bin" >> ~/.bashrc
source ~/.bashrc
```

---

### Issue 2: "ryu-manager: command not found"

**Error**: Ryu is not installed or not in PATH

**Solutions**:

```bash
# Check if installed
pip list | grep ryu

# If not installed
sudo pip install ryu

# If installed but not found
sudo pip show ryu
# Look at Location field

# Add to PATH (example)
echo "export PATH=$PATH:/usr/local/bin" >> ~/.bashrc
source ~/.bashrc

# Try with full path
/usr/local/bin/ryu-manager --version
```

---

### Issue 3: "ModuleNotFoundError: No module named 'ryu'"

**Error**: Python can't find Ryu library

**Solutions**:

```bash
# Install for Python 3 specifically
sudo python3 -m pip install ryu

# Verify installation
python3 -c "import ryu; print(ryu.__version__)"

# Check Python version
python3 --version

# Make sure you're using Python 3
# NOT Python 2!
python --version  # This might be Python 2
python3 --version # This should be 3.6+
```

---

### Issue 4: "Permission denied" errors

**Error**: Running network commands without sudo

**Solutions**:

```bash
# Always use sudo for network operations:
sudo python3 topology/simple_topology.py
sudo ryu-manager controller/basic_controller.py
sudo python3 attack/attack_script.py

# To reduce sudo usage, configure sudoers:
sudo visudo

# At the end, add (replace USER with your username):
# USER ALL=(ALL) NOPASSWD: /sbin/ip
# USER ALL=(ALL) NOPASSWD: /sbin/ifconfig
# USER ALL=(ALL) NOPASSWD: /usr/bin/mn

# Then you can run some commands without sudo:
# (Not all network commands, though)
```

---

### Issue 5: Port 6633 already in use

**Error**: "Address already in use" when starting Ryu controller

**Symptoms**: Controller won't start, error about port 6633

**Solutions**:

```bash
# Find process using port 6633
sudo lsof -i :6633

# Or with netstat
netstat -tlnp | grep 6633

# Kill the process
sudo pkill -f ryu-manager

# Wait a few seconds
sleep 5

# Try again
ryu-manager basic_controller.py

# Alternative: Use different port (if supported)
ryu-manager basic_controller.py --wsapi-host 127.0.0.1 --wsapi-port 8081
```

---

### Issue 6: Scapy errors

**Error**: "No module named scapy" or Scapy import errors

**Solutions**:

```bash
# Install Scapy
sudo pip install scapy

# Or the latest version
sudo pip install --upgrade scapy

# For some Scapy operations, you need libdnet:
sudo apt-get install -y libdnet1 libdnet-dev

# Test Scapy
python3 << 'EOF'
from scapy.all import IP, TCP, send
print("Scapy imported successfully!")
EOF
```

---

### Issue 7: Open vSwitch not working

**Error**: Bridge creation fails or ovs-vsctl commands fail

**Solutions**:

```bash
# Check if OVS is running
sudo systemctl status openvswitch-switch

# Start OVS if not running
sudo systemctl start openvswitch-switch

# Enable on boot
sudo systemctl enable openvswitch-switch

# Check OVS database
sudo ovsdb-tool show-log /var/lib/openvswitch/conf.db

# Restart OVS completely
sudo systemctl restart openvswitch-switch
```

---

## Runtime Issues

### Issue 8: Mininet won't start

**Error**: Network creation fails, or strange errors on startup

**Symptoms**: Error messages about bridges, namespaces, or OVS

**Solutions**:

```bash
# Clean up previous Mininet instances
sudo mn -c

# Check for lingering processes/bridges
sudo ovs-vsctl show
# If you see many bridges, clean them manually

# Check kernel support
uname -r
# Look for (virtualization support expected)

# Restart network services
sudo systemctl restart openvswitch-switch

# Try simple Mininet test
sudo mn --switch=ovsk --controller=none
# Should show mininet> prompt
# Type exit to quit

# If that works, try our topology
sudo python3 topology/simple_topology.py
```

---

### Issue 9: Controller and Mininet don't connect

**Error**: "Switch connects" message doesn't appear in controller

**Symptoms**: Mininet starts but no controller messages appear

**Solutions**:

```bash
# Verify Ryu is running on correct port
sudo lsof -i :6633
# Should show: ryu-manager listening

# Check firewall
sudo ufw status
sudo ufw allow 6633

# On Mininet CLI, check switch:
mininet> sh sudo ovs-vsctl show
# Should show bridge s1 and connections

# Manually set controller:
mininet> sh sudo ovs-vsctl set-controller s1 tcp:127.0.0.1:6633

# Check controller connection:
mininet> sh sudo ovs-vsctl get-controller s1
# Should return: tcp:127.0.0.1:6633
```

---

### Issue 10: Ping between hosts doesn't work

**Error**: Hosts can't ping each other

**Symptoms**: "100% packet loss" from ping

**Solutions**:

```bash
# Check host connectivity in Mininet CLI:
mininet> h1 ifconfig
# Should show h1-eth0 with IP 10.0.0.1

mininet> h2 ifconfig
# Should show h2-eth0 with IP 10.0.0.2

# Check ARP tables
mininet> h1 arp -a
# Should eventually show h2's MAC after ping

# Check routing tables
mininet> h1 route -n

# Manually test connectivity:
mininet> h1 ping -c 1 10.0.0.2 -v

# If still fails, controller might not be running:
# Start controller first, then Mininet
```

---

### Issue 11: Attack script won't run in Mininet

**Error**: "Command not found" or Python script doesn't execute

**Symptoms**: Attack script fails to launch from mininet CLI

**Solutions**:

```bash
# Verify script path
mininet> h1 ls -la /path/to/attack/attack_script.py

# Verify script is executable
# (On host machine)
chmod +x attack/attack_script.py

# Try with explicit python3
mininet> h1 python3 /path/to/attack/attack_script.py -h

# Check if Scapy is available in Mininet namespace
mininet> h1 python3 -c "from scapy.all import IP; print('OK')"
# If this fails, Scapy might not be installed for all users

# Solution: Use full path
mininet> h1 /usr/bin/python3 /path/to/attack/attack_script.py -i h1-eth0 -d 10.0.0.2
```

---

### Issue 12: No packet capture or flow table query works

**Error**: "Permission denied" or "command not found" for ovs-ofctl

**Solutions**:

```bash
# Check if ovs-ofctl is installed
which ovs-ofctl
/usr/sbin/ovs-ofctl  # If found

# Install if missing
sudo apt-get install -y openvswitch-switch

# Always use sudo
sudo ovs-ofctl dump-flows s1 -O OpenFlow13

# Check switch exists
sudo ovs-vsctl show
# Should list "Bridge s1"

# Check OpenFlow protocol version
sudo ovs-vsctl get Bridge s1 protocols
# Should include "OpenFlow13"
```

---

## Performance Issues

### Issue 13: High latency baseline (before attack)

**Error**: Even baseline ping latency is >10ms

**Symptoms**: Latency seems high without attack

**Solutions**:

```bash
# Check system load
top
# If CPU >50%, system is busy

# Close unnecessary applications

# Check Mininet CPU settings (less useful, but try)
sudo python3 << 'EOF'
from mininet.net import Mininet
from mininet.node import OVSKernelSwitch

# Adjust CPU-related settings if needed
EOF

# Check for competing network interfaces
ip link show

# The latency includes Mininet emulation overhead
# 1-5ms is typical for emulated networks
```

---

### Issue 14: Attack too fast or too slow

**Error**: Attack packet rate doesn't match requested rate

**Symptoms**: Packets sent faster or slower than specified

**Solutions**:

```bash
# Check system capacity
top  # If CPU >90%, packets may be slower

# Try lower rate
python3 attack/attack_script.py -i h1-eth0 -d 10.0.0.2 -r 50

# Check network interface capacity
ethtool h1-eth0
# Look for Speed

# Scapy performance note:
# - Scapy is slower than native sending
# - Rates >1000 pps may not be achievable
# - Default ~100-500 pps realistic

# For higher rates, consider:
# - tcpreplay (faster)
# - pktgen (kernel-based, much faster)
# - Custom C program with libpcap
```

---

### Issue 15: Monitoring script doesn't collect data

**Error**: CSV files are empty or not created

**Symptoms**: Results directory exists but CSVs are empty

**Solutions**:

```bash
# Check if monitoring started
ps aux | grep monitoring.py

# Verify output directory
ls -la results/

# Try monitoring manually
sudo python3 monitoring/monitoring.py --output-dir ./results/test --duration 10

# Check for errors
sudo python3 monitoring/monitoring.py --output-dir ./results/test --duration 10 2>&1 | head -20

# Verify flow table queryable:
sudo python3 << 'EOF'
from utils.sdn_utils import get_flow_table_size
size = get_flow_table_size('s1')
print(f"Flow table size: {size}")
EOF

# Check host accessibility:
ping -c 1 h1
# Mininet hosts need to be accessed via mininet namespace
# Monitoring script should handle this
```

---

## OpenFlow and Controller Issues

### Issue 16: Controller shows no PacketIns

**Error**: Even with normal traffic, controller logs show no PacketIn events

**Symptoms**: Quiet controller logs, no learning happening

**Solutions**:

```bash
# Check controller is actually running:
ps aux | grep ryu-manager

# Check logs more carefully:
# Ryu outputs to console - look for:
# "PacketIn" or "packet_in_handler"

# Look for EventOFPPacketIn messages

# Verify switch is actually connected:
# Controller should show "Switch connected: 0x..." message

# Check firewall again
sudo ufw status

# Try simpler controller test:
# Create minimal test script and watch output

# Enable verbose logging:
ryu-manager basic_controller.py --verbose
```

---

### Issue 17: Flow table not updating

**Error**: Flow table size stays the same (usually 3)

**Symptoms**: New flows don't get installed during test

**Solutions**:

```bash
# Verify flows can be seen:
sudo ovs-ofctl dump-flows s1 -O OpenFlow13

# Get just the count:
sudo ovs-ofctl dump-flows s1 -O OpenFlow13 | grep -c cookie

# Check if traffic is actually happening:
mininet> h1 ping h2

# While ping runs, check flows:
sudo watch -n 0.5 'ovs-ofctl dump-flows s1 -O OpenFlow13 | grep -c cookie'

# Look for the table-miss flow (should be there):
sudo ovs-ofctl dump-flows s1 -O OpenFlow13 | grep "priority=0"

# If nothing happens after ping:
1. Verify controller is running and connected
2. Check for errors in controller logs
3. Try with defense controller to see if basic works
```

---

### Issue 18: Defense mechanisms not working

**Error**: Defense controller shows same results as basic controller

**Symptoms**: Attack flows still accumulate, rate limiting not active

**Solutions**:

```bash
# Verify defense controller is running:
ps aux | grep defense_controller

# Look for defense messages in output:
# "DefenseController initialized"
# "Rate limit: 100 PacketIns/sec"
# "Suspicious source detected"

# Check defense parameters:
# Edit defense_controller.py and verify:
max_packet_in_per_sec = 100     # Should be active
idle_timeout = 10                # Should be short
hard_timeout = 30

# Verify attack is using IP variation:
python3 attack/attack_script.py -i h1-eth0 -d 10.0.0.2 -t ip

# Look for defense log messages:
# "PacketIn rate limit exceeded"
# "Suspicious source detected"
# "Dropping packet from"

# If still not working:
1. Verify attack is actually sent (check attack_script output)
2. Check flow table is actually growing (watch ovs-ofctl)
3. Look for Python errors in controller output
```

---

## Analysis and Reporting Issues

### Issue 19: Can't generate comparison graphs

**Error**: Python script fails when creating graphs

**Symptoms**: matplotlib errors, file not found, etc.

**Solutions**:

```bash
# Install matplotlib
pip install matplotlib

# Verify CSV files exist
ls -la results/baseline/metrics.csv
ls -la results/attack_no_defense/metrics.csv
ls -la results/attack_with_defense/metrics.csv

# Check CSV is not empty
head results/baseline/metrics.csv

# Try simple plot first
python3 << 'EOF'
import pandas as pd
data = pd.read_csv('results/baseline/metrics.csv')
print(data.head())
EOF

# If pandas error:
pip install pandas

# If matplotlib error:
pip install --upgrade matplotlib

# Check for permission issues
ls -la results/
# Should be readable
```

---

### Issue 20: Metrics don't match expectations

**Error**: Results don't show expected differences

**Symptoms**: Similar metrics for all tests, no clear defense benefit

**Reasons and Solutions**:

```bash
# Attack might be too weak:
# - Increase packet rate: -r 1000 (instead of 100)
# - Increase packet count: -n 10000 (instead of 1000)

# Defense might be too aggressive:
# - Edit defense_controller.py
# - Increase max_packet_in_per_sec from 100 to 200
# - Increase max_flows_per_source from 50 to 100

# System too fast:
# - Modern systems might not show saturation easily
# - Increase attack aggressiveness

# Monitoring interval too long:
# - Change monitoring interval from 5s to 1s
# - More granular data = clearer trends

# Result interpretation:
# - Even small improvements are significant
# - Defense prevents worst-case scenarios
# - Not eliminating attack entirely
```

---

## System-Specific Issues

### Issue 21: Ubuntu 22.04 or newer

**Error**: Compatibility issues with newer Ubuntu

**Solutions**:

```bash
# Some packages may need updates:
sudo apt-get update
sudo pip install --upgrade ryu mininet

# Python 3.10+ may have compatibility issues:
python3 --version

# Try with python3.9 if available:
sudo apt-get install python3.9
python3.9 -m pip install ryu

# Or use Docker/VM with Ubuntu 20.04
```

---

### Issue 22: Running on Windows/Mac

**Error**: Mininet only runs on Linux

**Solutions**:

```bash
# Option 1: Use Virtual Machine
# - VirtualBox + Ubuntu 20.04 (recommended)
# - VMware + Ubuntu
# - Hyper-V + Ubuntu

# Option 2: Use WSL 2 (Windows Subsystem for Linux)
# - Install Ubuntu 20.04 on WSL 2
# - Follow Linux installation steps
# - Some features might not work perfectly

# Option 3: Docker
# Docker image with Mininet pre-installed
docker pull containernet/containernet
docker run -it containernet/containernet /bin/bash

# Follow installation in Docker container
```

---

## Getting More Help

### Debug Mode

**Enable verbose output**:

```bash
# Ryu with verbose logging:
ryu-manager basic_controller.py --verbose

# Python with debug output:
python3 -u attack/attack_script.py  # unbuffered output

# Check logs:
tail -f logs/*.log
```

### Collect Diagnostic Information

**For troubleshooting with others**:

```bash
# Create diagnostic report:
cat > diagnostic_report.txt << 'EOF'
=== System Info ===
EOF

uname -a >> diagnostic_report.txt
python3 --version >> diagnostic_report.txt
pip list >> diagnostic_report.txt

# Add versions of key packages:
echo "=== Installed Versions ===" >> diagnostic_report.txt
pip show ryu >> diagnostic_report.txt
pip show mininet >> diagnostic_report.txt
pip show scapy >> diagnostic_report.txt

echo "=== Network Info ===" >> diagnostic_report.txt
sudo ovs-vsctl show >> diagnostic_report.txt

# Share this file when asking for help
```

### Common Command Reference

```bash
# Diagnostic commands (always useful):
ps aux | grep ryu          # Is controller running?
ps aux | grep mn           # Is Mininet running?
sudo lsof -i :6633         # What's using port 6633?
sudo ovs-vsctl show        # OVS status
sudo ovs-ofctl dump-flows s1 -O OpenFlow13  # Flow table

# Cleanup commands:
sudo mn -c                 # Clean up Mininet
sudo pkill -f ryu-manager  # Kill Ryu
sudo pkill -f mininet      # Kill Mininet
```

---

## Frequently Asked Questions (FAQ)

**Q: Why is my latency so high?**
A: Mininet emulation adds overhead. Baseline 1-5ms is normal.

**Q: Can I run this on Windows?**
A: No, only Linux. Use VM or WSL 2.

**Q: How do I know if the defense is working?**
A: Compare flow table size, latency, and CPU between tests.

**Q: Can I run with multiple switches?**
A: Yes, edit simple_topology.py to add more switches.

**Q: What if I want to test with more hosts?**
A: Add more hosts in simple_topology.py, e.g., `h3 = net.addHost('h3', ip='10.0.0.3')`

**Q: Can Mininet simulate real network?**
A: Mininet emulates network topology and behavior, but not perfect realism.

**Q: How long should tests run?**
A: 10-15 minutes per test is typical. Longer = more granular data.

---

For more help, check:
- [README.md](README.md) - Project overview
- [SETUP.md](SETUP.md) - Installation details
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design
- [RUN_INSTRUCTIONS.md](RUN_INSTRUCTIONS.md) - How to run tests

**Last Updated:** 2024
