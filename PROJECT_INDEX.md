# Project Index and Navigation Guide

Complete guide to all files, scripts, and documentation in the SDN Flow Table Security project.

## Quick Navigation

**First Time? Start Here:**
1. [README.md](README.md) - Project overview and context
2. [SETUP.md](SETUP.md) - Installation and setup
3. [RUN_INSTRUCTIONS.md](RUN_INSTRUCTIONS.md) - How to run tests
4. [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Common commands cheat sheet
5. [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - If something goes wrong

**Technical Details:**
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design and diagrams
- Code files (see below) - Comments explain each script

---

## Project Files Overview

### Documentation Files

| File | Purpose | Read Time |
|------|---------|-----------|
| [README.md](README.md) | Project overview, learning objectives, future improvements | 15 min |
| [SETUP.md](SETUP.md) | Step-by-step installation and verification | 10 min |
| [RUN_INSTRUCTIONS.md](RUN_INSTRUCTIONS.md) | How to execute all three tests | 20 min |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design, data flows, component descriptions | 20 min |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Common issues and solutions | 15 min |
| [QUICK_REFERENCE.md](QUICK_REFERENCE.md) | Cheat sheet of commands and code snippets | 5 min |
| [PROJECT_INDEX.md](PROJECT_INDEX.md) | This file - navigation guide | 5 min |

### Python Scripts

#### Topology (Network Creation)

| File | Location | Purpose | Lines | Complexity |
|------|----------|---------|-------|-----------|
| simple_topology.py | topology/ | Create Mininet network with hosts and switch | 150 | Beginner |

**Key Concepts**: Mininet, OpenFlow switches, virtual hosts, network linking

---

#### Controllers (SDN Control Logic)

| File | Location | Purpose | Lines | Complexity |
|------|----------|---------|-------|-----------|
| basic_controller.py | controller/ | Simple L2 learning controller (no defense) | 250 | Intermediate |
| defense_controller.py | controller/ | Enhanced controller with 3 defense mechanisms | 350 | Intermediate |

**Key Concepts**: OpenFlow events, packet handling, flow installation, rate limiting, anomaly detection

**Defenses Implemented**:
1. PacketIn Rate Limiting - Cap controller load
2. Flow Timeout Reduction - Force faster eviction
3. Anomaly Detection - Identify suspicious patterns

---

#### Attack (Saturation Attack Simulation)

| File | Location | Purpose | Lines | Complexity |
|------|----------|---------|-------|-----------|
| attack_script.py | attack/ | Generate unique packets to saturate flow table | 400 | Beginner-Intermediate |

**Features**:
- Multiple attack types (IP variation, MAC variation, random)
- Adjustable packet rate and count
- Progress tracking and summary reporting

**Attack Variations**:
```
-t ip       → Vary source IP (10.0.0.1, 10.0.0.2, etc.)
-t mac      → Vary source MAC
-t random   → Vary everything (most aggressive)
```

---

#### Monitoring (Metrics Collection)

| File | Location | Purpose | Lines | Complexity |
|------|----------|---------|-------|-----------|
| monitoring.py | monitoring/ | Collect performance metrics over time | 400 | Intermediate |

**Metrics Collected**:
- Flow table size (ovs-ofctl query)
- Network latency (ping measurements)
- CPU and memory usage (psutil)
- System resource statistics

**Output**: CSV files in results/ directory

---

#### Utilities (Helper Functions)

| File | Location | Purpose | Lines | Complexity |
|------|----------|---------|-------|-----------|
| sdn_utils.py | utils/ | Common SDN utilities and helpers | 300 | Intermediate |

**Utilities Provided**:
```python
query_switch_flow_table()     # Get flows from switch
get_flow_table_size()          # Count flows
get_switch_stats()             # Detailed stats
parse_ryu_controller_log()     # Extract metrics
clear_switch_flows()           # Reset flow table
start_packet_capture()         # tcpdump wrapper
SimpleLogger                   # File logging with timestamps
```

---

### Configuration Files

| File | Purpose |
|------|---------|
| requirements.txt | Python package dependencies (pip install) |
| .gitignore | Files to ignore in version control |

---

### Generated Directories (Created at Runtime)

| Directory | Purpose | Contents |
|-----------|---------|----------|
| logs/ | Controller and application logs | *.log files |
| results/ | Test results and metrics | CSV files, reports |
| results/baseline/ | Baseline test metrics | metrics.csv, latency.csv, cpu_memory.csv |
| results/attack_no_defense/ | Attack without defense metrics | Same as above |
| results/attack_with_defense/ | Attack with defense metrics | Same as above |

---

## Working with the Code

### File Structure Visualization

```
SecureFlowTable/                              # Project root
│
├── 📚 Documentation
│   ├── README.md                            # Main project README
│   ├── SETUP.md                             # Installation guide
│   ├── RUN_INSTRUCTIONS.md                  # How to run tests
│   ├── ARCHITECTURE.md                      # System design
│   ├── TROUBLESHOOTING.md                   # Common issues
│   ├── QUICK_REFERENCE.md                   # Cheat sheet
│   ├── PROJECT_INDEX.md                     # This file
│   └── requirements.txt                     # Dependencies
│
├── 🔧 topology/                             # Network topology
│   └── simple_topology.py                   # Mininet network
│       ├ Creates: hosts (h1, h2)
│       ├ Creates: switch (s1)
│       ├ Creates: connections to controller
│       └ Runs: Mininet CLI for interaction
│
├── 🎛️ controller/                           # SDN Controllers
│   ├── basic_controller.py                  # No defense (for comparison)
│   │   ├ Handles: Switch connections
│   │   ├ Handles: PacketIn messages
│   │   ├ Installs: Flow rules
│   │   └ Logs: Network activity
│   │
│   └── defense_controller.py                # With defense mechanisms
│       ├ Defense 1: Rate limiting (100 pps)
│       ├ Defense 2: Timeout reduction (10s)
│       ├ Defense 3: Anomaly detection
│       └ Tracks: Attack statistics
│
├── 🔨 attack/                               # Attack simulation
│   └── attack_script.py                     # Flow table saturation attack
│       ├ Creates: Unique packets
│       ├ Varies: Source IP/MAC
│       ├ Sends: At specified rate
│       └ Reports: Attack statistics
│
├── 📊 monitoring/                           # Performance monitoring
│   └── monitoring.py                        # Metrics collection
│       ├ Measures: Flow table size
│       ├ Measures: Network latency
│       ├ Measures: CPU/Memory usage
│       └ Outputs: CSV files for analysis
│
├── 🔧 utils/                                # Utilities and helpers
│   └── sdn_utils.py                         # Common SDN utilities
│       ├ Utilities: Flow table queries
│       ├ Tools: Log parsing
│       ├ Tools: Packet capture
│       └ Logger: Timestamped logging
│
├── 📝 logs/                                 # Generated at runtime
│   ├── controller.log                       # Ryu controller logs
│   ├── attack.log                           # Attack script logs
│   └── network.log                          # Network activity logs
│
└── 📈 results/                              # Generated test results
    ├── baseline/
    │   ├── metrics.csv                      # Flow, latency, packet-in
    │   ├── latency.csv                      # Detailed latency data
    │   ├── cpu_memory.csv                   # System resources
    │   └── summary_report.txt               # Generated summary
    ├── attack_no_defense/                   # Same structure as above
    └── attack_with_defense/                 # Same structure as above
```

---

## Reading the Code - Best Practices

### Start with Topology (Easiest)

1. **topology/simple_topology.py** (150 lines)
   - Understand: How Mininet networks are created
   - Learn: OpenFlow switch setup
   - Follow: Comments that explain each section

### Then Study Basic Controller

2. **controller/basic_controller.py** (250 lines)
   - Understand: OpenFlow event handling
   - Learn: PacketIn message processing
   - Study: Flow rule installation

### Understand the Attack

3. **attack/attack_script.py** (400 lines)
   - Understand: Scapy packet generation
   - Learn: Different attack types
   - Study: Packet variation patterns

### Compare With Defense

4. **controller/defense_controller.py** (350 lines)
   - Understand: Defense mechanisms
   - Compare: With basic controller
   - Learn: Detection patterns

### Use the Utilities

5. **utils/sdn_utils.py** (300 lines)
   - Understand: Common operations
   - Learn: OpenFlow queries
   - Study: How to interact with OVS

---

## Code Reading Guide

### Key Concepts by File

**topology/simple_topology.py:**
```python
Mininet()               # Create network
net.addSwitch()         # Add OpenFlow switch
net.addHost()           # Add virtual hosts
net.addLink()           # Connect components
RemoteController()      # Connect to Ryu
net.start()             # Start the network
```

**controller/basic_controller.py:**
```python
RyuApp()                      # Create Ryu application
@set_ev_cls(EventOF...)       # Decorator for event handling
EventOFPSwitchFeatures        # Switch connects to controller
EventOFPPacketIn              # Unknown packet arrives
OFPFlowMod()                  # Install flow rule
add_flow()                    # Helper to install rule
```

**attack/attack_script.py:**
```python
Ether()                       # Ethernet frame
IP(src=..., dst=...)         # IP header with addresses
TCP(sport=..., dport=...)    # TCP header with ports
send(pkt)                     # Send packet via Scapy
generate_attack_packets()     # Generator for packets
execute_attack()              # Main attack loop
```

**controller/defense_controller.py:**
```python
check_rate_limit()            # Defense 1: Rate limiting
is_suspicious_source()        # Defense 3: Anomaly detection
idle_timeout / hard_timeout   # Defense 2: Timeout reduction
packet_in_timestamps[]        # Track PacketIn rate
source_ip_flows[]             # Track flows per source
```

---

## Common Workflows

### Workflow 1: Understanding the System

1. Read: [README.md](README.md) (project overview)
2. Read: [ARCHITECTURE.md](ARCHITECTURE.md) (system design)
3. Study: topology/simple_topology.py (architecture in code)
4. Study: controller/basic_controller.py (how control works)
5. Understand: Data flow diagrams in ARCHITECTURE.md

### Workflow 2: Running a Test

1. Read: [RUN_INSTRUCTIONS.md](RUN_INSTRUCTIONS.md)
2. Follow: Step-by-step test guide
3. Collect: Metrics and results
4. Use: [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for command help

### Workflow 3: Troubleshooting

1. Check: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. Look: For similar issue
3. Try: Suggested solution
4. If stuck: Review relevant documentation

### Workflow 4: Analysis and Reporting

1. Use: Python snippets from [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
2. Load: CSV files from results/
3. Create: Comparison graphs
4. Write: Report with findings

---

## Testing and Validation

### Test Scenarios

| Test | Controller | Expected Result |
|------|-----------|-----------------|
| Baseline | basic_controller | Low flows, low latency |
| Attack (No Defense) | basic_controller | High flows, high latency |
| Attack (Defense) | defense_controller | Controlled flows, recovered latency |

### Expected Results

**Baseline**:
- Flows: 3-10
- Latency: 1-2ms
- CPU: <10%

**Attack (No Defense)**:
- Flows: 1000-5000 (!)
- Latency: 50-200ms (!)
- CPU: 80%+ (!)

**Attack (Defense)**:
- Flows: 300-800 (controlled)
- Latency: 2-10ms (recovered)
- CPU: 20-35% (manageable)

---

## Extending the Project

### To Add More Hosts

**Edit**: topology/simple_topology.py
```python
# Line ~45, add:
h3 = net.addHost('h3', ip='10.0.0.3', mac='00:00:00:00:00:03')
net.addLink(h3, s1, bw=100)
```

### To Modify Defense Parameters

**Edit**: controller/defense_controller.py
```python
# Line ~35
max_packet_in_per_sec = 200      # Increase from 100
idle_timeout = 5                  # Decrease from 10
max_flows_per_source = 100        # Increase from 50
```

### To Change Attack Parameters

**Command Line** (no code changes needed):
```bash
python3 attack_script.py -i h1-eth0 -d 10.0.0.2 \
  -n 10000 \    # More packets
  -r 1000       # Faster rate
```

### To Add New Metrics

**Edit**: monitoring/monitoring.py
```python
# Add new measurement function
def get_new_metric():
    # Your measurement code
    return value

# Call in record_metrics()
new_value = get_new_metric()

# Log to CSV
writer.writerow([...existing..., new_value])
```

---

## Project Statistics

### Code Summary

| Aspect | Count |
|--------|-------|
| Total Python files | 6 |
| Total lines of Python code | ~1,850 |
| Total documentation lines | ~3,500 |
| Comments in code | ~35% |
| Test scenarios | 3 |
| Defense mechanisms | 3 |
| Attack types | 3 |
| Metrics collected | 6+ |

### Documentation Summary

| Document | Lines | Reading Time |
|----------|-------|--------------|
| README | 600 | 15 min |
| SETUP | 400 | 10 min |
| RUN_INSTRUCTIONS | 800 | 20 min |
| ARCHITECTURE | 600 | 20 min |
| TROUBLESHOOTING | 500 | 15 min |
| QUICK_REFERENCE | 400 | 5 min |
| Total | 3,300 | ~85 min |

### Total Project Size

- **Code + Configuration**: ~2,000 lines
- **Documentation**: ~3,500 lines
- **Comments**: ~1,000 lines
- **Total**: ~6,500 lines of material

---

## Learning Path

### Beginner (1-2 hours)

1. Read [README.md](README.md)
2. Follow [SETUP.md](SETUP.md) for installation
3. Skim [ARCHITECTURE.md](ARCHITECTURE.md)
4. Look at topology/simple_topology.py (with comments)

### Intermediate (3-5 hours)

1. Fully read [ARCHITECTURE.md](ARCHITECTURE.md)
2. Study all Python scripts (with code comments)
3. Follow [RUN_INSTRUCTIONS.md](RUN_INSTRUCTIONS.md)
4. Run all three test scenarios

### Advanced (6-10 hours)

1. Deep dive into each controller
2. Understand OpenFlow protocol details
3. Modify defense parameters and re-test
4. Implement additional defenses
5. Extend to multi-switch topology

---

## Key Takeaways

### What You'll Learn

✅ SDN and OpenFlow fundamentals  
✅ Network attack simulation and patterns  
✅ Defense mechanism design and implementation  
✅ Performance monitoring and analysis  
✅ Python network programming  
✅ How to measure and compare security solutions  

### What the Project Demonstrates

✅ Flow table saturation attacks are real and damaging  
✅ Simple defenses can significantly reduce impact  
✅ Trade-offs between defense and performance  
✅ Importance of network monitoring  
✅ How to design and test security solutions  

---

## Resources for Further Learning

### Official Documentation
- [OpenFlow Specification](https://www.opennetworking.org/)
- [Ryu Documentation](https://ryu.readthedocs.io/)
- [Mininet Documentation](http://mininet.org/)
- [Scapy Documentation](https://scapy.rtfd.io/)

### Related Topics to Explore
- Software Defined Networking (SDN) architecture
- Network security and DDoS mitigation
- OpenFlow protocol deep dive
- Machine learning for anomaly detection
- Network simulation and testing

---

## Questions and Support

### If You're Stuck

1. **Check**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md) first
2. **Review**: Code comments in relevant script
3. **Search**: [ARCHITECTURE.md](ARCHITECTURE.md) for concept
4. **Look**: For similar issue in documentation

### Common Questions

- **"What's a flow?"** → See ARCHITECTURE.md section "Flow Lifecycle"
- **"Why is latency high?"** → See README.md "Understanding the Project"
- **"How do I modify attack?"** → See QUICK_REFERENCE.md
- **"What's the difference between controllers?"** → See ARCHITECTURE.md "Controller Layer"

---

**Navigation Tip**: Use Ctrl+F to search this index for topics you're interested in.

**Last Updated**: 2024  
**Version**: 1.0  
**Status**: Complete and Ready for Use
