import simpy
import random
import matplotlib.pyplot as plt
import numpy as np  # Necessary for array handling
import networkx as nx  # For network topology visualization

# Constants
NUM_REQUESTS = 50  # Total number of requests per PC
NUM_PCS = 30  # Number of PCs
NUM_SERVERS = 3  # Number of HTTP servers
NUM_SWITCHES = 12  # Total number of switches (8 FIFO, 8 Priority)
FIFO_COUNT = 8  # Number of FIFO switches
PRIORITY_COUNT = 8  # Number of Priority switches
SWITCH_CAPACITY = 1  # Capacity of each switch

# Data collection
data_loss = {'FIFO': 0, 'Priority': 0}
latencies = {'FIFO': [], 'Priority': []}  # Store latency for each queue type
delays = {'FIFO': [], 'Priority': []}  # Store delay for each queue type
overall_latencies = []  # Store overall latencies
overall_delays = []  # Store overall delays
switch_stats = {f'Switch {i + 1}': {'queue_lengths': [], 'utilization': []} for i in range(NUM_SWITCHES)}

# PC class representing a personal computer
class PC:
    def __init__(self, env, name, http_servers, switches):
        self.env = env
        self.name = name
        self.http_servers = http_servers
        self.switches = switches
        self.successful_requests = 0  # Track successful requests

    def request_http(self):
        for _ in range(NUM_REQUESTS):
            yield self.env.timeout(random.uniform(0.1, 0.5))  # Think time
            request_time = self.env.now

            # Randomly select a switch and server
            switch = random.choice(self.switches)
            server = random.choice(self.http_servers)

            # Request handling
            queue_length = len(switch.queue)  # Track the current queue length
            switch_stats[switch.name]['queue_lengths'].append(queue_length)

            with switch.request() as request:
                yield request
                if random.random() < 0.1:  # Simulate 10% chance of data loss
                    if isinstance(switch, FIFOQueue):
                        data_loss['FIFO'] += 1
                    elif isinstance(switch, PriorityQueue):
                        data_loss['Priority'] += 1
                    continue  # Skip to next request

                # Handle request to the HTTP server
                start_time = self.env.now
                yield self.env.process(server.handle_request(self.name))
                end_time = self.env.now

                self.successful_requests += 1  # Count successful request
                overall_latencies.append(end_time - start_time)  # Overall latency
                overall_delays.append(end_time - request_time)  # Overall delay
                if isinstance(switch, FIFOQueue):
                    latencies['FIFO'].append(end_time - start_time)  # Calculate and record FIFO latency
                    delays['FIFO'].append(end_time - request_time)  # Calculate and record FIFO delay
                else:
                    latencies['Priority'].append(end_time - start_time)
                    delays['Priority'].append(end_time - request_time)

# HTTP Server class
class HTTPServer:
    def __init__(self, env, name):
        self.env = env
        self.name = name

    def handle_request(self, pc_name):
        service_time = random.uniform(0.5, 1.5)  # Simulate processing time
        yield self.env.timeout(service_time)
        print(f"{pc_name} received response from {self.name} at {self.env.now:.2f}")

# Switch classes
class FIFOQueue(simpy.Resource):
    def __init__(self, env, name, capacity):
        super().__init__(env, capacity)
        self.name = name

class PriorityQueue(simpy.PriorityResource):
    def __init__(self, env, name, capacity):
        super().__init__(env, capacity)
        self.name = name

# Setup the environment
env = simpy.Environment()

# Create HTTP servers
http_servers = [HTTPServer(env, f'Server{i + 1}') for i in range(NUM_SERVERS)]

# Create switches
switches = []
for i in range(FIFO_COUNT):
    switch = FIFOQueue(env, f'FIFO Switch {i + 1}', capacity=SWITCH_CAPACITY)
    switches.append(switch)
for i in range(PRIORITY_COUNT):
    switch = PriorityQueue(env, f'Priority Switch {i + 1}', capacity=SWITCH_CAPACITY)
    switches.append(switch)

# Initialize switch statistics
for switch in switches:
    switch_stats[switch.name] = {'queue_lengths': [], 'utilization': []}

# Create PCs
pcs = []
for i in range(NUM_PCS):
    pc = PC(env, f'PC{i + 1}', http_servers, switches)
    pcs.append(pc)
    env.process(pc.request_http())

# Run the simulation
env.run()

# Calculate overall statistics
throughput_value = sum(pc.successful_requests for pc in pcs) / env.now
average_latency_fifo = np.mean(latencies['FIFO']) if latencies['FIFO'] else 0
average_latency_priority = np.mean(latencies['Priority']) if latencies['Priority'] else 0
average_delay_fifo = np.mean(delays['FIFO']) if delays['FIFO'] else 0
average_delay_priority = np.mean(delays['Priority']) if delays['Priority'] else 0

print(f"Throughput: {throughput_value:.2f} requests/second")
for switch_type in data_loss:
    print(f"{switch_type} Data Loss: {data_loss[switch_type]}")
print(f"Average Latency (FIFO): {average_latency_fifo:.2f} seconds")
print(f"Average Latency (Priority): {average_latency_priority:.2f} seconds")
print(f"Average Delay (FIFO): {average_delay_fifo:.2f} seconds")
print(f"Average Delay (Priority): {average_delay_priority:.2f} seconds")

# Visualization of metrics
plt.figure(figsize=(12, 12))

# Plot Data Loss by Queue Type
plt.subplot(4, 2, 1)
plt.bar(data_loss.keys(), np.array(list(data_loss.values())), color='lightblue')
plt.title('Data Loss by Queue Type')
plt.ylabel('Number of Lost Packets')
plt.grid()

# Plot Overall Latencies Histogram
plt.subplot(4, 2, 2)
plt.hist(overall_latencies, bins=20, color='lightgreen', alpha=0.7)
plt.title('Overall Latency Histogram')
plt.xlabel('Latency (seconds)')
plt.ylabel('Frequency')
plt.grid()

# Plot Overall Delays Histogram
plt.subplot(4, 2, 3)
plt.hist(overall_delays, bins=20, color='lightcoral', alpha=0.7)
plt.title('Overall Delay Histogram')
plt.xlabel('Delay (seconds)')
plt.ylabel('Frequency')
plt.grid()

# Plot FIFO Delays Histogram
plt.subplot(4, 2, 4)
plt.hist(delays['FIFO'], bins=20, color='blue', alpha=0.7)
plt.title('FIFO Delay Histogram')
plt.xlabel('Delay (seconds)')
plt.ylabel('Frequency')
plt.grid()

# Plot FIFO Latency Histogram
plt.subplot(4, 2, 5)
plt.hist(latencies['FIFO'], bins=20, color='red', alpha=0.7)
plt.title('FIFO Latency Histogram')
plt.xlabel('Latency (seconds)')
plt.ylabel('Frequency')
plt.grid()

# Plot Priority Latency Histogram
plt.subplot(4, 2, 6)
plt.hist(latencies['Priority'], bins=20, color='orange', alpha=0.7)
plt.title('Priority Latency Histogram')
plt.xlabel('Latency (seconds)')
plt.ylabel('Frequency')
plt.grid()

plt.tight_layout()
plt.show()

# Function to draw network topology
def draw_topology(pcs, switches, http_servers):
    G = nx.DiGraph()  # Create a directed graph

    # Add PCs
    for pc in pcs:
        G.add_node(pc.name, layer='PC')

    # Add switches
    for switch in switches:
        G.add_node(switch.name, layer='Switch')

    # Add servers
    for server in http_servers:
        G.add_node(server.name, layer='Server')

    # Connect PCs to switches
    for pc in pcs:
        for switch in switches:
            G.add_edge(pc.name, switch.name)

    # Connect switches to servers
    for switch in switches:
        for server in http_servers:
            G.add_edge(switch.name, server.name)

    # Draw the graph
    plt.figure(figsize=(12, 8))  # Increased figure size for better visibility
    pos = nx.spring_layout(G, k=1.0, iterations=50)  # Adjusted parameters for better layout
    node_colors = []
    for n in G.nodes():
        if G.nodes[n]['layer'] == 'PC':
            node_colors.append('lightblue')
        elif G.nodes[n]['layer'] == 'Switch':
            node_colors.append('lightgreen' if 'FIFO' in n else 'salmon')
        else:
            node_colors.append('lightcoral')

    # Use a circular layout to improve aesthetics
    nx.draw(G, pos, with_labels=True, node_color=node_colors, node_size=2000, font_size=10, font_weight='bold', arrows=True)
    plt.title('Enhanced Network Topology Visualization')
    plt.axis('off')  # Hide axes for cleaner look
    plt.show()

# Call the draw topology function
draw_topology(pcs, switches, http_servers)
