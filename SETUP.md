# Setup and Installation Guide

Complete step-by-step installation instructions for the SDN Flow Table Security project.

## Prerequisites

- **OS**: Ubuntu 20.04 LTS (recommended) or similar Linux distribution
- **CPU**: Multi-core processor recommended
- **RAM**: 4GB minimum (8GB recommended)
- **Disk**: 10GB free space
- **Network**: Stable internet connection for package downloads

## Installation Steps

### Step 1: System Updates

```bash
# Update package manager
sudo apt-get update
sudo apt-get upgrade -y

# Install build tools (needed for compiling some packages)
sudo apt-get install -y build-essential python3-dev
```

### Step 2: Install Mininet

Mininet is a network emulator that creates virtual networks.

**Option A: From Ubuntu Repositories (Recommended)**
```bash
sudo apt-get install -y mininet
```

**Option B: From Source (Latest Version)**
```bash
git clone https://github.com/mininet/mininet
cd mininet
# Try to install openvswitch from system packages first
sudo apt-get install -y openvswitch-switch openvswitch-testcontroller
# Then install mininet itself
sudo util/install.sh -a
```

**Verify Installation:**
```bash
sudo mn --version
# Should show version number like "2.3.0"
```

### Step 3: Install Open vSwitch

Open vSwitch is the virtual switch software used by Mininet.

```bash
sudo apt-get install -y openvswitch-switch openvswitch-common openvswitch-switch-dpctl

# Verify installation
sudo ovs-vsctl --version
# Should show version like "Open vSwitch"
```

### Step 4: Install Ryu Controller

Ryu is the OpenFlow controller framework we use for this project.

```bash
# Install pip for Python 3
sudo apt-get install -y python3-pip

# Install Ryu
sudo pip install ryu

# Verify installation
ryu-manager --version
# Should show version number
```

### Step 5: Install Additional Dependencies

```bash
# Install required system packages
sudo apt-get install -y python3-scapy net-tools curl wget

# Install Python packages from requirements.txt
cd ~/SecureFlowTable
sudo pip install -r requirements.txt
```

### Step 6: Configure Mininet Network Namespace

Mininet needs certain Linux kernel capabilities. Test that it works:

```bash
# Test basic Mininet topology
sudo mn -c  # Clean up any previous mininet instances

# Create a simple test network (press Ctrl+D to exit)
sudo mn --switch=ovsk --controller=none

# You should see:
# *** Creating network...
# *** Adding controller
# *** Starting network
# *** Starting CLI:
# mininet>
```

If this works, Mininet is properly installed!

If you get permission errors, try:
```bash
sudo usermod -a -G mininet $USER
sudo usermod -a -G ovs-vsctl $USER
# You may need to log out and back in for group changes to take effect
```

### Step 7: Clone and Navigate to Project

```bash
# Navigate to your project directory
cd ~/SecureFlowTable

# Create directories for logs and results if they don't exist
mkdir -p logs results

# Verify project structure
ls -la
# Should show: topology/, controller/, attack/, monitoring/, utils/, logs/, results/
```

### Step 8: Run Installation Test

```bash
# Test Python environment
python3 -c "import ryu; print('Ryu OK')"
python3 -c "import mininet; print('Mininet OK')"
python3 -c "from scapy.all import IP; print('Scapy OK')"

# Test Mininet
cd topology
sudo python3 simple_topology.py
# You should see network startup messages
# Type 'exit' to quit
```

## Detailed Installation Notes

### Ryu Controller Installation

The Ryu controller might require additional setup:

```bash
# If you get import errors, ensure dependencies are installed
sudo pip install netaddr

# For development setup
cd ~/
git clone https://github.com/faucetsdn/ryu.git
cd ryu
sudo pip install -e .  # Development installation
```

### Scapy Configuration

Scapy might need libdnet for packet generation:

```bash
# Linux (Ubuntu/Debian):
sudo apt-get install -y libdnet1

# Test Scapy
python3 << 'EOF'
from scapy.all import *
# Create a test packet
pkt = IP(dst="10.0.0.2")/ICMP()
print("Scapy test OK")
EOF
```

### For Non-Root Users

Some operations require root. To reduce sudo usage:

```bash
# Allow specific commands without password
sudo visudo

# Add at the end of the file:
%sudo ALL=(ALL) NOPASSWD: /sbin/ip
%sudo ALL=(ALL) NOPASSWD: /usr/sbin/ovs-vsctl
%sudo ALL=(ALL) NOPASSWD: /usr/sbin/ovs-ofctl
%sudo ALL=(ALL) NOPASSWD: /usr/bin/mn

# Save and exit (Ctrl+X, then Y, then Enter)
```

## Verification Checklist

Run through this checklist to verify everything is installed correctly:

```bash
# Check Mininet
echo "=== Mininet ==="
which mn
mn --version
sudo mn --help | head -5

# Check Ryu
echo "=== Ryu ==="
which ryu-manager
ryu-manager --version

# Check Open vSwitch
echo "=== Open vSwitch ==="
sudo ovs-vsctl --version
sudo ovs-ofctl --version

# Check Python packages
echo "=== Python Packages ==="
python3 -c "import ryu; print('✓ Ryu')"
python3 -c "import mininet; print('✓ Mininet')"
python3 -c "from scapy.all import *; print('✓ Scapy')"
python3 -c "import psutil; print('✓ psutil')"
python3 -c "import pandas; print('✓ pandas')"

# Test project structure
echo "=== Project Structure ==="
ls -d topology controller attack monitoring utils logs results
```

If all checks pass with ✓ marks, your installation is complete!

## Quick Test Run

Once installation is complete, test everything with:

**Terminal 1 - Start Controller:**
```bash
cd ~/SecureFlowTable/controller
ryu-manager basic_controller.py --observe-links
```

**Terminal 2 - Start Network:**
```bash
cd ~/SecureFlowTable/topology
sudo python3 simple_topology.py
```

**Terminal 3 - Inside Mininet (after prompt appears), test connectivity:**
```bash
mininet> h1 ping -c 4 h2
mininet> exit
```

You should see ping responses confirming connectivity!

## Troubleshooting Installation

### Issue: "mn: command not found"
```bash
# Solution: Mininet not in PATH
sudo apt-get remove mininet
sudo apt-get install -y mininet

# Or install from source (see Step 2, Option B)
```

### Issue: "ryu-manager: command not found"
```bash
# Solution: Ryu not in PATH or not installed
# Try full path:
/usr/local/bin/ryu-manager --version

# If works, add to PATH:
echo "export PATH=$PATH:/usr/local/bin" >> ~/.bashrc
source ~/.bashrc
```

### Issue: "Permission denied" for Mininet
```bash
# Solution: Need to run as root
sudo mn --version
sudo python3 topology/simple_topology.py
```

### Issue: "address already in use" for port 6633
```bash
# Solution: Kill existing Ryu process
sudo pkill -f ryu-manager
# Wait a few seconds, then try again
```

### Issue: Scapy errors with Tcpdump
```bash
# Solution: Install Tcpdump
sudo apt-get install -y tcpdump

# And Libdnet
sudo apt-get install -y libdnet1 libdnet-dev
```

See [README.md](README.md) for more troubleshooting or [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

## Post-Installation Configuration

### Create Convenient Aliases (Optional)

Add to `~/.bashrc`:
```bash
alias sdn-project='cd ~/SecureFlowTable'
alias ryu-start='cd ~/SecureFlowTable/controller && ryu-manager basic_controller.py --observe-links'
alias mn-start='cd ~/SecureFlowTable/topology && sudo python3 simple_topology.py'
```

Then reload:
```bash
source ~/.bashrc
```

### Set Up Logging Directory (Optional)

```bash
# Create logs directory
mkdir -p ~/SecureFlowTable/logs

# Set up log rotation (keep last 10 logs)
# Add to crontab -e:
# @daily find ~/SecureFlowTable/logs -name "*.log" -mtime +10 -delete
```

## Next Steps

After successful installation:

1. Read [RUN_INSTRUCTIONS.md](RUN_INSTRUCTIONS.md) for how to run tests
2. Read [ARCHITECTURE.md](ARCHITECTURE.md) to understand the design
3. Review the code comments in each Python script
4. Start with **Test 1: Baseline** in [README.md](README.md)

## Getting Help

If you encounter issues:

1. **Check error messages carefully** - they often indicate the problem
2. **Try one component at a time** - verify Mininet works before adding Ryu
3. **Use sudo when needed** - most network operations require root
4. **Check version compatibility** - Mininet 2.3.0, Ryu 4.34, Python 3.6+
5. **Search online** - Mininet and Ryu have good community support

---

**Installation Complete!** Continue to [RUN_INSTRUCTIONS.md](RUN_INSTRUCTIONS.md)
