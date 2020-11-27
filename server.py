import socket, time, os, select
from io import BytesIO

IP = "192.168.43.93"
PORT_A = 7007
PORT_B = 6006

SYN_ACK = "SYN-ACK6006"
END = "FIN"
MAXLINE = 1024
buffer_fichier = bytearray()
buffer_ack = bytearray()
nb_segment = 0
timeout = 0.2

#socket creation
try:
    socket_connect = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
except socket.error:
    print("socket creation failed")
    exit()

try:
    socket_transfer = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
except socket.error:
    print("socket creation failed")
    exit()

#socket bind
try:
    socket_connect.bind((IP, PORT_A))
except socket.error:
    print("socket bind failed")
    exit()

try:
    socket_transfer.bind((IP, PORT_B))
except socket.error:
    print("socket transfer bind failed")
    exit()


print("Server waiting for a client")

#tree handshake connection
data, addr = socket_connect.recvfrom(1024)
data=data.decode("Utf8")
print("Client: %s" % data)

socket_connect.sendto(SYN_ACK.encode("ascii"), addr)
print("ME: ", SYN_ACK)

data, addr = socket_connect.recvfrom(1024)
data=data.decode("Utf8")
print("Client: %s" % data)

data, addr = socket_transfer.recvfrom(1024)
data=data.decode("ascii")
print(data)

#if(data == "image") :
print("Client request: %s" % data)
    #open file and put it in a buffer
my_file = open("image.jpg", "rb")
bytes = my_file.read()
my_file.close()
for elem in bytes:
    buffer_fichier.append(elem)
size = len(buffer_fichier)

    #file sending
for i in range(0,size,MAXLINE):
    buffer_segment = bytearray()
    buffer_segment.append(nb_segment)
    for j in range(i, i + MAXLINE):
        if j < size:
            buffer_segment.append(buffer_fichier[j])
        else:
            break
    socket_transfer.sendto(buffer_segment, (IP, PORT_B))
    nb_segment += 1
    ready = select.select([socket_transfer], [], [], timeout)
    if ready[0]:
        data, addr = socket_transfer.recvfrom(1)
        data.decode("Utf8")
    else:
        print("pas de ack recu, probleme")
    #buffer_ack.append(data)

socket_transfer.sendto(END.encode("Utf8"), (IP, PORT_B))
print("File of %d bytes received" %  os.path.getsize("image.jpg"))
print("nb of ack received %d" % len(buffer_ack))

#else :
print("No file requested")
