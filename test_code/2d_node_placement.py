# IMPORTS ============================================================================================================
import sys
import json
import ipaddress
import math
import pygame
import os

# CONSTANTS ============================================================================================================
SCREEN_SIZE = 650
RADIUS = 200
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)

os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (650,20)


# CLASSES ============================================================================================================
class Node:
    def __init__(self, start_ip, end_ip, start_index, end_index, x_coord, y_coord, size, hostlist):
        self.start_ip = start_ip # Start of ip range
        self.end_ip = end_ip # end of ip range
        self.start_index = start_index # index of the first ip in sorted hostlist that falls in the range
        self.end_index = end_index # index of the last ip in sorted hostlist that falls in range
        self.x_coord = x_coord # x coord
        self.y_coord = y_coord # y coord
        self.size = size # size based on percent of network
        self.hostlist = hostlist # list of hosts that fall in range

# FUNCTIONS ============================================================================================================

# Description: convert ip string to decimal number 
# Inputs: ip string
# Outputs: int
def ip_to_num(addr):
    return int(ipaddress.ip_address(addr))

# Description: convert decimal number to ip string
# Inputs: int
# Outputs: ip string
def num_to_ip(num):
    return str(ipaddress.ip_address(num))

# Description: load json file
# Inputs: none, command line argument
# Outputs: python object named data
def load_json():
    arg_count = len(sys.argv)
    if arg_count < 2:
        print("Usage: backend.py pcap.json")
        exit()
    else:
        json_data = sys.argv[1]
    f = open(json_data)
    data = json.load(f)
    f.close()
    return data

# Description: get all hosts
# Inputs: data object
# Outputs: list of hosts
def get_hosts(data):
    hosts = []
    for host in data["Hosts"]:
        hosts.append(host["HostIP"])
    return hosts

# Description: determine which hosts fall under a node
# Inputs: node object and list of hosts
# Outputs: none, hosts are appended directly to the node's hostlist
def add_hosts_to_node(node: Node, hostlist):
    start = ip_to_num(node.start_ip)
    end = ip_to_num(node.end_ip)
    for i in hostlist:
        if (start <= ip_to_num(i)) & (end >= ip_to_num(i)):
            node.hostlist.append(i)

# Description: determine if two nodes are connected
# Inputs: data object, node1, node2
# Outputs: true/false
def node_connections(data, node1: Node, node2: Node, hostlist):
    connected = False
    for host1 in node1.hostlist:
        for host2 in node2.hostlist:
            # if a host in node1 is connected to a host in node 2, the nodes are connected
            if host_connection(data, host1, host2, hostlist=hostlist):
                connected = True
                break
    return connected

# Description: determine if two hosts are connected
# Inputs: data object, host1, host2
# Outputs: true/false
def host_connection(data, host1, host2, hostlist):
    connections = data["Connections"]
    if connections[hostlist.index(host1)][hostlist.index(host2)] == 1:
        return True
    else:
        return False

# Description: convert coordinates to pygame axis
# Inputs: x coord, y coord
# Outputs: (x, y)
def convert_coords(x, y):
    return (x + (SCREEN_SIZE/2)), (y + (SCREEN_SIZE/2))

# Description: print commands
# Inputs: NA 
# Outputs: NA
def commands():
    print("\nCommands:")
    print("'# range' - expand node")
    print("'e #' - fully expand node")
    # print("'h' node # - hide node")
    print("'p #' - print connections")
    print("'c' - show commands")
    print("'r' - refresh visualization")
    print("'q' - quit")

# Description: sort list of hosts
# Inputs: hostlist 
# Outputs: sorted hostlist
def sort_hostlist(hostlist):
    for count, i in enumerate(hostlist):
        hostlist[count] = ip_to_num(i)

    hostlist.sort()

    for count, i in enumerate(hostlist):
        hostlist[count] = num_to_ip(i)

    return hostlist


def parse_ranges(parent: Node, ranges, nodelist, sorted_hostlist):
    # get ips from ranges
    ranges = ranges.split(',')
    for count, i in enumerate(ranges):
        ranges[count] = i.split('-')
    
    for i in ranges:
        child = Node(start_ip=i[0], end_ip=i[1], start_index=None, end_index=None, x_coord=None, y_coord=None, size=None, hostlist=[])
        add_hosts_to_node(node=child, hostlist=parent.hostlist)
        add_index_to_node(node=child, sorted_hostlist=sorted_hostlist)
        nodelist.append(child)
    
    nodelist.remove(parent)


def add_index_to_node(node: Node, sorted_hostlist):
    start = ip_to_num(node.start_ip)
    end = ip_to_num(node.end_ip)
    for count, i in enumerate(sorted_hostlist):
        if ip_to_num(i) >= start:
            node.start_index = count
            node.start_ip = i
            break
    for count, i in enumerate(reversed(sorted_hostlist)):
        if ip_to_num(i) <= end:
            node.end_index = len(sorted_hostlist) - count - 1
            node.end_ip = i
            break

  
def calc_coords(nodelist, total_num_hosts):
    ranges = []
    for i in nodelist:
        ranges.append([i.start_index , i.end_index])

    degrees = []
    for i, j in enumerate(ranges):
        if len(j) == 1:
            degrees.append(360 * (1 / total_num_hosts))
        else:
            degrees.append(360 * ((int(j[1]) - int(j[0]) + 1) / total_num_hosts))

    # add all degrees
    for i in range(1, len(degrees)):
        degrees[i] = degrees[i] + degrees[i-1]

    degrees_old = degrees.copy()

    # line should actually go in the center of the degree ranges
    degrees[0] = (0 + degrees_old[0]) / 2
    for i in range(1, len(degrees)):
        degrees[i] = (degrees_old[i] + degrees_old[i-1]) / 2

    percents = []
    for i, j in enumerate(ranges):
        if len(j) == 1:
            percents.append((1 / total_num_hosts) * 100)
        else:
            percents.append(((int(j[1]) - int(j[0]) + 1) / total_num_hosts) * 100)

    coords_old = []
    for i in degrees_old:
        coords_old.append([(RADIUS * math.cos(math.radians(i))), (RADIUS * math.sin(math.radians(i)))])

    coords = []
    for i in degrees:
        coords.append([(RADIUS * math.cos(math.radians(i))), (RADIUS * math.sin(math.radians(i)))])

    if len(coords) == 1:
        coords[0] = [0,0]

    for count, i in enumerate(coords):
        nodelist[count].x_coord = i[0]
        nodelist[count].y_coord = i[1]
        nodelist[count].size = percents[count]

def expand_node(parent: Node, nodelist, sorted_hostlist):
    print(parent.hostlist)
    for i in parent.hostlist:
        child = Node(start_ip=i, end_ip=i, start_index=None, end_index=None, x_coord=None, y_coord=None, size=None, hostlist=[])
        add_hosts_to_node(node=child, hostlist=parent.hostlist)
        add_index_to_node(node=child, sorted_hostlist=sorted_hostlist)
        nodelist.append(child)
    
    nodelist.remove(parent)

def print_connections(node: Node, data, hostlist):
    # only works for nodes with a single IP
    connections = data["Connections"]
    host1 = node.start_ip
    print(f'{node.start_ip} is connected to:')
    for i in hostlist:
        if connections[hostlist.index(host1)][hostlist.index(i)] == 1:
            print(i)

# MAIN FUNCTION ============================================================================================================
def main():

    pygame.font.init() 
    font = pygame.font.SysFont('Times New Roman', 15)

    # initialize data
    user_input = ''
    data = load_json()
    nodelist = []
    hostlist = get_hosts(data)
    total_num_hosts = len(hostlist)
    sorted_hostlist = hostlist.copy() # create a sorted copy of the hostlist, IMPROVEMENT - have this already sorted in JSON
    sorted_hostlist = sort_hostlist(sorted_hostlist)


    # create first node
    parent = Node(start_ip='0.0.0.0', end_ip='255.255.255.255', start_index=None, end_index=None, x_coord=None, y_coord=None, size=None, hostlist=[])
    add_hosts_to_node(node=parent, hostlist=hostlist)
    add_index_to_node(node=parent, sorted_hostlist=sorted_hostlist)
    nodelist.append(parent)


    # Initialize pygame and print banner
    pygame.init()
    screen = pygame.display.set_mode([SCREEN_SIZE, SCREEN_SIZE])
    print("============================")
    print("2D Network Visualization POC")
    print("============================")
    commands()


    # Main while loop -----------------------------------------------------------------------------------------------------------
    while user_input != 'q':


        # after each command refresh screen
        screen.fill(WHITE)

        # recalculate coordinates for all the nodes
        calc_coords(nodelist=nodelist, total_num_hosts=total_num_hosts)

        # Draw nodes
        print("\nVisible Nodes:")
        for i, node in enumerate(nodelist):
            num_hosts = len(node.hostlist)
            size_node = math.floor((len(node.hostlist)/len(hostlist))*100)
            if node.start_ip == node.end_ip:
                print(f"Node {i+1}: {node.start_ip},  contains {num_hosts} host,  {size_node}% of network")
            else:
                print(f"Node {i+1}: {node.start_ip} - {node.end_ip},  contains {num_hosts} hosts,  {size_node}% of network")
            pygame.draw.circle(screen, BLUE, convert_coords(node.x_coord, node.y_coord), node.size*2)


        # Draw connections
        print("Node Connections:")
        for count1, i in enumerate(nodelist):
            for count2, j in enumerate(nodelist):
                if count1 < count2:
                    if node_connections(data, i, j, hostlist):
                        print(f"Node {count1+1} - Node {count2+1}: Yes")
                        pygame.draw.line(screen, RED, convert_coords(i.x_coord, i.y_coord), convert_coords(j.x_coord, j.y_coord))
                    else:
                        print(f"Node {count1+1} - Node {count2+1}: No")

        
        # Add labels
        for i, node in enumerate(nodelist):
            # write node label
            if node.start_ip == node.end_ip:
                text = font.render(f'{node.start_ip}', False, (0, 0, 0))
                screen.blit(text, convert_coords(node.x_coord - 90, node.y_coord - 10))
            else:
                text = font.render(f'{node.start_ip} - {node.end_ip}', False, (0, 0, 0))
                screen.blit(text, convert_coords(node.x_coord - 90, node.y_coord - 10))


        # Get user input
        user_input = input("Input command: ")
        
        # expand node into ranges
        if user_input[0].isdigit():
            parse_ranges(nodelist[int(user_input[0]) - 1], user_input[2:], nodelist, sorted_hostlist)
        
        # fully expand node
        elif user_input[0] == 'e':
            expand_node(nodelist[int(user_input[2]) - 1], nodelist, sorted_hostlist)
        
        # print connections for specific node
        elif user_input[0] == 'p':
            print_connections(nodelist[int(user_input[2]) - 1], data, hostlist)
        
        # print commands
        elif user_input == 'c':
            commands()
        
        elif user_input == 'r':
            print("Refresh visualization")


        # exit main loop
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                user_input = 'q'
        pygame.display.flip()
    
    # End main while loop ------------------------------------------------------------------------------------------------------------
    

    # On quit, close pygame
    pygame.quit()

main()