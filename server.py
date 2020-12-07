import socket, time, os, select
from numpy import zeros,array

IP = "127.0.0.2"
PORT_A = 7007
PORT_B = 6006

SYN_ACK = "SYN-ACK6006"
END = "FIN"
MAXLINE = 1024
buffer_fichier = []
buffer_segment=[]
file= "image.jpg"
f_ret_counter =0
nb_segment = 1
timeout = 0.00040
j=1
last_last_ack=0

ClientCount=0

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

socket_connect.sendto(SYN_ACK.encode("Utf8"), addr)
print("Me: " + SYN_ACK)

data, addr = socket_connect.recvfrom(1024)
data=data.decode("Utf8")
print("Client: %s" % data)


data, addr = socket_transfer.recvfrom(1024)
data=data.decode("ascii")
data=data[:-1]



if(data==file) :

    print("Client request: %s" % data)
    temps_avant= time.time()
    my_file = open("image.jpg", "rb")
    size = 0

    while size < os.path.getsize("image.jpg"):
        bytes = my_file.read(1024)
        buffer_fichier.append(bytes)
        size = len(buffer_fichier)*1024

    my_file.close()
    print("la taille de buffer fichier est %d", size)
    last_ack=0
    seg_tot=int(size/1024)
    #file sending
    temps_avant= time.time()
    while last_ack != seg_tot:

        if  nb_segment<seg_tot+1:
            buffer_segment = init_segment(nb_segment).encode("Utf8")
            socket_transfer.sendto((buffer_segment+buffer_fichier[nb_segment-1]), (addr))
            nb_segment += 1

        ready = select.select([socket_transfer], [], [], timeout)
        if ready[0]:
            last_ack, addr = socket_transfer.recvfrom(1024)
            last_ack=last_ack.decode("Utf8")
            last_ack =int(last_ack[-3:].replace('\x00',''))






        if last_last_ack==last_ack :
            f_ret_counter +=1

            if f_ret_counter==3:
                #nb_segment=last_ack+1
                buffer_segment = init_segment(last_ack+1).encode("Utf8")
                socket_transfer.sendto((buffer_segment+buffer_fichier[last_ack]), (addr))
                ready = select.select([socket_transfer], [], [], timeout)
                if ready[0]:
                    last_ack, addr = socket_transfer.recvfrom(1024)
                    last_ack=last_ack.decode("Utf8")
                    last_ack =int(last_ack[-3:].replace('\x00',''))
                f_ret_counter=0



        #if j==5 :
            #if last_ack != nb_segment :
                #nb_segment=last_ack+1

            #j=0


        #j=j+1
        last_last_ack=last_ack

    socket_transfer.sendto(END.encode("Utf8"), addr)
    temps_apres=time.time()
    debit = (size/ (temps_apres-temps_avant))/1000
    print("Débit : ", debit , "ko/s")
    print("File of %d bytes send" %  os.path.getsize("image.jpg"))
    print("nb of ack received :" , last_ack)
