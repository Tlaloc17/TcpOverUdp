import socket, time, re, os

IP = "127.0.0.1"
PORT_A = 7007

SYN = "SYN"
ACK = "ACK"
IMG = "image"

buffer_ack = bytearray()

#function to slip text and integer in a string
def text_num_split(item):
    for index, letter in enumerate(item, 0):
        if letter.isdigit():
            return [item[:index],item[index:]]

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

#tree handshake connexion
socket_connect.sendto(SYN.encode("Utf8"), (IP, PORT_A))
print("Me: SYN")

data, addr = socket_connect.recvfrom(1024)
data=data.decode("Utf8")
msg = text_num_split(data)
PORT_B= int(msg[1])
print("Server: %s" % data)

try:
    socket_transfer.bind((IP, PORT_B)) #on bind  la socket pour qu'elle ecoute
except socket.error:                   #sur le port ou le serveur envoie le fichier
    print("socket bind failed")
    exit()

socket_connect.sendto(ACK.encode("Utf8"), addr)
print("Me: ACK")

socket_connect.sendto(IMG.encode("Utf8"),addr)
#Receive file
my_file = open('my_file', 'w+b')
while True:

    data, addr = socket_transfer.recvfrom(1025)
    if (data == "END".encode("Utf8")):
        break
    else:
        data = bytearray(data)
        buffer_ack.append(data[0])
        ack = str(data[0])
        socket_transfer.sendto(ack.encode("Utf8"), addr)
        data.pop(0)
        my_file.write(data)

my_file.close()
print("File of %d bytes sent" %  os.path.getsize('my_file'))
print("nb of ack sent %d" % len(buffer_ack))
