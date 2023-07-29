# pip install scapy
from scapy.all import wrpcap, Ether, IP, TCP
import time
import random

ipList = ["192.168.1.1", "192.168.1.2", "192.168.1.3", "192.168.1.4", "192.168.1.5", "192.168.1.6"]
macList = ["00:00:00:00:00:01", "00:00:00:00:00:02", "00:00:00:00:00:03", "00:00:00:00:00:04", "00:00:00:00:00:05", "00:00:00:00:00:06"]
packetList = []

def createPacket(src, dst, size):
    payload = 'a'*size
    pkt = Ether()/IP()/TCP()/payload
    pkt[Ether].time = time.time()
    pkt[Ether].src= macList[src-1]
    pkt[Ether].dst= macList[dst-1]
    pkt[IP].src= ipList[src-1]
    pkt[IP].dst= ipList[dst-1]
    pkt[TCP].sport = random.randint(1, 500)
    pkt[TCP].dport = random.randint(1, 500)
    packetList.append(pkt)

createPacket(1, 2, 1)
createPacket(1, 5, 6)
createPacket(2, 1, 9)
createPacket(2, 5, 8)
createPacket(3, 6, 4)
createPacket(5, 1, 3)
createPacket(5, 2, 3)
createPacket(6, 3, 7)

wrpcap('fake.pcap', packetList)

# RESULT
# 0 1 2 3 4 5 6
# 1 0 1 0 0 6 0
# 2 9 0 0 0 8 0
# 3 0 0 0 0 0 4
# 4 0 0 0 0 0 0
# 5 3 3 0 0 0 0
# 6 0 0 7 0 0 0