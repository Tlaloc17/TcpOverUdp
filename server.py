import socket, time, os, select
from io import BytesIO

IP = "127.0.0.2"
PORT_A = 7007
PORT_B = 6006

SYN_ACK = "SYN-ACK6006"
END = "FIN"
MAXLINE = 1024
buffer_fichier = []
buffer_segment=[]
buffer_ack = bytearray()
nb_segment = 0
timeout = 0.5
seg_manquant=""


#creer le numero du segment sur 6 octets

def init_segment(n):
    u= str(n)
    v= u.zfill(6)
    return v

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
print(addr)

socket_connect.sendto(SYN_ACK.encode("ascii"), addr)
print("Me: " + SYN_ACK)

data, addr = socket_connect.recvfrom(1024)
data=data.decode("Utf8")
print("Client: %s" % data)

data, addr = socket_transfer.recvfrom(1024)
data=data.decode("ascii")

#if(data == "image") :
print("Client request: %s" % data)
    #open file and put it in a buffer
my_file = open("image.jpg", "rb")
size = 0
while size < os.path.getsize("image.jpg"):
    bytes = my_file.read(1024)
    buffer_fichier.append(bytes)
    size = len(buffer_fichier)*1024
my_file.close()
print("la taille de buffer fichier est %d", size)

#file sending
for i in range(int(size/1024)):
    buffer_segment = init_segment(nb_segment).encode("Utf8")

    socket_transfer.sendto((buffer_segment+buffer_fichier[i]), (addr))
    nb_segment += 1
    ready = select.select([socket_transfer], [], [], timeout)
    if ready[0]:
        print("ready")
        data, addr = socket_transfer.recvfrom(1024)
        data=data.decode("Utf8")
        lol = int(float(data[-3:]))
        print(lol)

    else:
        print("pas de ack recu, probleme")
        #buffer_segment = init_segment(seg_manquant).encode("Utf8")
        #socket_transfer.sendto((buffer_segment+buffer_fichier[seg_manquant]), (addr))
    #buffer_ack.append(data)

socket_transfer.sendto(END.encode("Utf8"), (IP, PORT_B))
print("File of %d bytes send" %  os.path.getsize("image.jpg"))
print("nb of ack received %d" % len(buffer_ack))
