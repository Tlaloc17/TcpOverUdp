import sys,socket, time, os, select
from numpy import zeros,array
from threading import Thread
import logging

IP = "127.0.0.2"
PORT_A = 7007
PORT_B = 6006
END = "FIN"
MAXLINE = 1024

# logging configuration
logging.basicConfig(format='%(process)d-%(threadName)s %(funcName)s():  %(message)s', level = logging.DEBUG)
logger = logging.getLogger(__name__)

# creer le numero du segment sur 6 octets
def init_segment(n):
    u= str(n)
    v= u.zfill(6)
    return v

def rtt_calc(nseg, nack, timeseg, timeack, bufrtt, count):

    rtt=0
    if nseg==nack:
        rtt=timeack-timeseg
        bufrtt.append(rtt)
        count+=1
    return count-1



def main_server(PORT_A):
    """
    Le main_server est le serveur "père" qui tourne en tache de fond sur le PORT_A passé en paramètre.
    Il fait le three-way handshake et lance les workers
    """
    #socket creation
    try:
        socket_connect = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    except socket.error:
        print("socket creation failed")
        exit()
    #bind process
    try:
        socket_connect.bind((IP, PORT_A))
    except socket.error:
        print("socket bind failed")
        exit()

    # main_server boucle en attendant une requete d'un client
    # dès qu'il recoit une requete il fait un three-way handshake et initialise un worker
    new_worker_port = 6006
    while True:
        # three way handshake

        data, addr = socket_connect.recvfrom(1024)
        data=data.decode("Utf8")
        logger.debug("Client: %s" % data)
        logger.debug(addr)

        # attribution d'un nouveau port
        new_worker_port += 1
        syn_ack = "SYN-ACK"+str(new_worker_port)
        (Thread(target=worker, args=(new_worker_port, ))).start()

        #envoie syn ack et nouveau port + début rtt time
        time_synack=time.time()
        print(time_synack)
        socket_connect.sendto(syn_ack.encode("Utf8"), addr)
        logger.debug("Me: " + syn_ack)

        # on recoit un ACK
        data, addr = socket_connect.recvfrom(1024)
        time_ack=time.time()
        print(time_ack)
        rtt_begin=float(time_ack-time_synack)
        data=data.decode("Utf8")
        logger.debug("Client: %s" % data)
        logger.debug("RTT %f" % rtt_begin)

        # on initialise un nouveau thread worker
        logger.debug("Launching new thread on port %d" % new_worker_port)


def worker(port_b):
    """
    Le worker est un serveur "fils" qui peut être lancé indépendemment d'autres workers
    Il fait :
    - initialisation de la socket sur le port attribué par le main_server
    - envoi du fichier
    """
    buffer_fichier = []
    buffer_segment = []
    f_ret_counter =0
    nb_segment = 1
    timeout = 0.0009
    j=1
    last_last_ack=0
    buffer_rtt=[]
    ClientCount=0
    moy_rtt=0
    count=0
    index=0
    cwnd=0


    logger.debug("Hello from worker on %d " % port_b)

    #socket creation
    socket_transfer = None
    try:
        socket_transfer = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    except socket.error:
        print("socket creation failed")
        exit()
    except Exception:
        print("unexpected error")
        exit()

    #socket bind
    try:
        socket_transfer.bind((IP, port_b))
    except socket.error:
        print("socket transfer bind failed")
        exit()
    except Exception:
        print("unexpected error")
        exit()

    logger.debug("before recvfrom")
    # recoit le nom du fichier
    data, addr = socket_transfer.recvfrom(1024)
    logger.debug("after recvfrom")
    data=data.decode("ascii")
    data=data[:-1]
    file=data

    logger.debug("Client request: %s" % file)
    temps_avant= time.time()
    my_file = open(file, "rb")
    size = 0

    while size < os.path.getsize(file):
        bytes = my_file.read(1024)
        buffer_fichier.append(bytes)
        size = len(buffer_fichier)*1024

    my_file.close()
    logger.debug("la taille de buffer fichier est %d", size)
    last_ack=0
    seg_tot=int(size/1024)

    # file sending
    # fenetre 2 et srtt
    while last_ack != seg_tot:

        if  nb_segment<seg_tot+1:
            buffer_segment = init_segment(nb_segment).encode("Utf8")
            #buffer_segment_next = init_segment(nb_segment+1).encode("Utf8")
            temps_seg=time.time()
            socket_transfer.sendto((buffer_segment+buffer_fichier[nb_segment-1+cwnd]), (addr))
            #socket_transfer.sendto((buffer_segment_next+buffer_fichier[nb_segment+cwnd]), (addr))
            #nb_segment += 2
            nb_segment+=1




        ready = select.select([socket_transfer], [], [], timeout)

        if ready[0]:
            last_ack, addr = socket_transfer.recvfrom(1024)
            temps_ack=time.time()
            last_ack=last_ack.decode("Utf8")
            last_ack =int(last_ack[-6:].replace('\x00',''))
            print(last_ack)
            """
            index = rtt_calc(nb_segment-1, last_ack, temps_seg,temps_ack, buffer_rtt, count)
            if buffer_rtt:
                timeout=buffer_rtt[index]

            """






        if last_last_ack==last_ack :
            f_ret_counter +=1

            if f_ret_counter==3:
                #nb_segment=last_ack+1
                buffer_segment = init_segment(last_ack+1).encode("Utf8")
                #temps_send_fast=time.time()
                socket_transfer.sendto((buffer_segment+buffer_fichier[last_ack]), (addr))
                ready = select.select([socket_transfer], [], [], timeout)
                if ready[0]:
                    last_ack, addr = socket_transfer.recvfrom(1024)
                    #temps_rec_fast=time.time()
                    last_ack=last_ack.decode("Utf8")
                    last_ack =int(last_ack[-6:].replace('\x00',''))
                    #print(last_ack)
                    """
                    index = rtt_calc(last_ack, last_last_ack, temps_send_fast,temps_rec_fast, buffer_rtt, count)
                    if buffer_rtt:
                        timeout=buffer_rtt[index]
                    """




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

    for i in range(len(buffer_rtt)):

        moy_rtt+=buffer_rtt[i]
    moy_rtt=moy_rtt/seg_tot

    print("RTT moyen =", moy_rtt)
    print("File of %d bytes send" %  os.path.getsize(file))
    print("nb of ack received :" , last_ack)


# lance le programme principal
if __name__ == "__main__":
    (Thread(target=main_server, args=(PORT_A, ))).start()
