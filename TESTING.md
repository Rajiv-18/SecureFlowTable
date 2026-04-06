# Testing Procedure

## Test 1: Baseline (Normal Traffic)

1. **Clean up first:** In Terminal 2, type `exit` and run `sudo mn -c`. Then stop any running controller in Terminal 1 (`Ctrl+C`).

2. **Terminal 1:** Start the basic controller:
   ```bash
   cd ~/SecureFlowTable/controller && ryu-manager basic_controller.py --observe-links
   ```

3. **Terminal 2:** Launch the topology:
   ```bash
   cd ~/SecureFlowTable/topology && sudo python3 simple_topology.py
   ```

4. **Terminal 3:** Start monitoring:
   ```bash
   cd ~/SecureFlowTable && sudo python3 monitoring/monitoring.py --output-dir ./results/baseline --duration 60
   ```

5. **Terminal 2 (Quickly!):** Run a long ping so the monitor has data to record:
   ```
   h1 ping -c 60 h2
   ```

6. Wait 60 seconds for Terminal 3 to finish. Then `Ctrl+C` Terminal 1, and type `exit` in Terminal 2.

---

## Test 2: The Attack (Vulnerable Switch)

1. **Clean up:**
   ```bash
   sudo mn -c
   ```

2. **Terminal 1:** Start the basic controller:
   ```bash
   cd ~/SecureFlowTable/controller && ryu-manager basic_controller.py --observe-links
   ```

3. **Terminal 2:** Launch the topology:
   ```bash
   cd ~/SecureFlowTable/topology && sudo python3 simple_topology.py
   ```

4. **Terminal 3:** Start monitoring with a 100-second duration:
   ```bash
   cd ~/SecureFlowTable && sudo python3 monitoring/monitoring.py --output-dir ./results/attack_no_defense --duration 100
   ```

5. **Terminal 2 (Quickly!):** Launch the attack:
   ```
   h1 python3 /home/vboxuser/SecureFlowTable/attack/fast_attack.py
   ```

6. Wait for Terminal 3 to finish. Then `Ctrl+C` Terminal 1, and type `exit` in Terminal 2.

---

## Test 3: The Attack (Defended Switch)

1. **Clean up:**
   ```bash
   sudo mn -c
   ```

2. **Terminal 1:** Start the **defense** controller:
   ```bash
   cd ~/SecureFlowTable/controller && ryu-manager defense_controller.py --observe-links
   ```

3. **Terminal 2:** Launch the topology:
   ```bash
   cd ~/SecureFlowTable/topology && sudo python3 simple_topology.py
   ```

4. **Terminal 3:** Start monitoring:
   ```bash
   cd ~/SecureFlowTable && sudo python3 monitoring/monitoring.py --output-dir ./results/attack_with_defense --duration 100
   ```

5. **Terminal 2 (Quickly!):** Launch the attack:
   ```
   h1 python3 /home/vboxuser/SecureFlowTable/attack/fast_attack.py
   ```

6. Wait for Terminal 3 to finish. Then `Ctrl+C` Terminal 1, and type `exit` in Terminal 2.
