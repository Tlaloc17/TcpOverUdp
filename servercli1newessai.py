import sys,socket, time, os, select
from numpy import zeros,array
from threading import Thread
import logging
import numpy as np

#from matplotlib import pyplot as plt

IP = "127.0.0.2"
PORT_A = 7007
PORT_B = 6006
END = "FIN"
MAXLINE = 1024
"""
global swnd
global perc_timeout
global difference
"""
swnd = int(sys.argv[1])
perc_timeout = float(sys.argv[2])
difference = int(sys.argv[3])


# logging configuration
logging.basicConfig(level=logging.ERROR, format='%(process)d-%(threadName)s %(funcName)s()_%(lineno)d:  %(message)s')
logger = logging.getLogger(__name__)


class RTT:
    def __init__ (self,time):
        self.time=time
rtt_begin=RTT(0)

def slow_start_imp(swnd,sstresh):
    if swnd<sstresh :
        return True
    else :
        return False

#def congestion_avoidance()






def init_segment(n):
    """
    Crée le numero du segment sur 6 octets
    """
    u= str(n)
    v= u.zfill(6)
    return v


def send_packet(nb_segment, socket_transfer, buffer_fichier, addr):
    """
    Envoie le paquet avec le numéro de séquence NB_SEGMENT.
    Dans l'en-tête on met NB_SEGMENT
    Dans les data, on met le morceau de fichier à l'index NB_SEGMENT-1 (l'index commence à 0).
    """
    buffer_segment = init_segment(nb_segment).encode("Utf8")
    logger.debug(f"sending buffer_fichier[{nb_segment-1}]")
    logger.debug(f" buffer_segment {buffer_segment}")
    socket_transfer.sendto((buffer_segment+buffer_fichier[nb_segment-1]), (addr))



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

        socket_connect.sendto(syn_ack.encode("Utf8"), addr)
        logger.debug("Me: " + syn_ack)

        # on recoit un ACK
        data, addr = socket_connect.recvfrom(1024)
        time_ack=time.time()

        rtt_begin.time=time_ack-time_synack
        data=data.decode("Utf8")
        logger.debug("Client: %s" % data)
        logger.debug("RTT %f" % rtt_begin.time)

        # on initialise un nouveau thread worker
        logger.info("Launching new thread on port %d" % new_worker_port)



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
    nb_segment = 0
    j=1
    last_ack=0


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

    # recoit le nom du fichier
    data, addr = socket_transfer.recvfrom(1024)
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
    print(seg_tot)

    # file sending
    # fenetre 2 et srtt

    rtt_count = 0
    timeout = (rtt_begin.time)*perc_timeout
    buff_time=[]
    buff_time.append(timeout)
    packet_has_been_sent = False
    no_response_count=0
    buff_nb_segment=[]
    #swnd=45
    i=0
    sstresh=0
    msg_receive=0
    socket_transfer.setblocking(False)
    while last_ack != seg_tot:
        #time.sleep(3)

        logger.info("-------------------------------------------------")
        #socket_transfer.settimeout(None)
        # (1) On envoie un segment et on lance le chrono pour le RTT
        logger.debug(f"nb_segment {nb_segment} last_ack {last_ack} ")
        #if  nb_segment < seg_tot+1 and nb_segment <= last_ack:
        if  nb_segment < seg_tot+1:
            logger.debug("nb segment en début de boucle {nb_segment}")


            while i<swnd and nb_segment+1<=seg_tot:
                nb_segment += 1

                send_packet(nb_segment, socket_transfer, buffer_fichier, addr)
                logger.debug(f"nb_segment set to {nb_segment}")

                i+=1

            packet_has_been_sent = True
            i=0
            while i<swnd:
                ready = select.select([socket_transfer], [], [], timeout)
                if ready[0]:
                    msg_receive, addr = socket_transfer.recvfrom(1024)
                    msg_receive=msg_receive.decode("Utf8")
                    logger.debug(f"msg_receive begin = {msg_receive}")
                    msg_receive =msg_receive[-7:]
                    logger.debug(f"msg_receive mid = {msg_receive}")
                    msg_receive =int(msg_receive[:-1])
                    logger.debug(f"msg_receive = {msg_receive}")
                    #fast_retransmit
                    if last_ack < msg_receive:
                        last_ack=msg_receive
                        f_ret_counter=0
                    if last_ack==nb_segment:

                        continue
                    if last_ack==msg_receive:
                        f_ret_counter+=1
                        if f_ret_counter==3 and last_ack+1<seg_tot:
                            #nb_segment=last_ack+1
                            logger.debug(f"fast retransmit {last_ack+1}")
                            send_packet(last_ack+1, socket_transfer, buffer_fichier, addr)
                            f_ret_counter=0
                            continue



                        logger.debug(f"last_ack = {last_ack}")
                logger.debug(f"nombre de tour pour recv ={i}" )
                i+=1
            i=0



        # (2) On attend un ACK du dernier paquet envoyé
        #ready = select.select([socket_transfer], [], [], timeout)

        # On reçoit un message
        #if ready[0]:
            # Dans tous les cas on récupère le numéro d'ACK




            # Dans tous les cas on calcule le RTT

                #  (2.1) Tout se déroule comme prévu: on reçoit l'ACK du dernier paquet envoyé
            if last_ack == nb_segment :
                #timeout=0.3*timeout+0.7*((rtt_recv_time-rtt_send_time)/(swnd))
                #print("tiemout=",timeout)

                f_ret_counter = 0
                logger.info("Cas 2.1)  tout se déroule comme prévu")
                """
                if slow_start_imp(swnd, sstresh):
                    swnd+=1
                """
                continue


        #Problème : Dernier ack reçu différent du numéro de segment envoyé






            #  (2.2) Problème: on reçoit un ACK supérieur au num de la séquence, donc on met à jour notre nb_segment




            elif last_ack < nb_segment:
                logger.info(f"Cas 2.3)  last_ack = {last_ack}       <     nb_segment = {nb_segment}")
                # on incrémente le compteur de fast_retransmit
                if  nb_segment-last_ack>=difference:
                    logger.debug(f"Reset à la différence {last_ack+1}")
                    nb_segment=last_ack+1
                    continue
                f_ret_counter +=1
                if f_ret_counter==3 and last_ack+1<=seg_tot:
                    #nb_segment=last_ack+1
                    logger.debug(f"fast retransmit {last_ack+1}")
                    send_packet(last_ack+1, socket_transfer, buffer_fichier, addr)
                    f_ret_counter=0
                    continue

            elif nb_segment-last_ack>=difference:
                nb_segment=last_ack+1
                continue

            # (2.3) Problème: on reçoit un ack inférieur au num de la séquence, ça veut dire qu'il manque un paquet au client










    socket_transfer.sendto(END.encode("Utf8"), addr)
    temps_apres=time.time()
    debit = (size/ (temps_apres-temps_avant))/1000
    print(debit)




    #print("File of %d bytes send" %  os.path.getsize(file))
    #print("nb of ack received :" , last_ack)




# lance le programme principal
if __name__ == "__main__":
    (Thread(target=main_server, args=(PORT_A, ))).start()
