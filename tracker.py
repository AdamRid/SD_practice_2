from pyactor.context import set_context, create_host, sleep, serve_forever, interval
from pyactor.exceptions import TimeoutError
import random


class Tracker(object):
    _tell = ['announce', 'init_start', 'check_peers']
    _ask = ['get_peers']
    _ref = ['announce', 'get_peers']

    # Inicializador de la instancia del Tracker
    def __init__(self):
        self.swarmDic = {}
        self.ttl = 10
        self.interval1 = None

    def init_start(self):
        # Programamos el intervalo que comprobara el ttl de los peer's cada segundo
        self.interval1 = interval(self.host, 1, self.proxy, 'check_peers')

    # Metodo 'announce' del Tracker
    # Guarda un diccionario 'swarmDic' de pares clave-valor -> {'torrent_hash': peers_dic{}}
    # A su vez 'peers_dic' es un diccionario de los pares clave-valor -> {'peer_ref': [peer_proxy, ttl]}
    def announce(self, torrent_hash, peer_ref):
        # Comprobamos si existe el swarm del torrent_hash
        if torrent_hash in self.swarmDic:
            # Comprobamos si el peer existe en el swarm
            if str(peer_ref) in self.swarmDic[torrent_hash]:
                # Si existe le restauramos el ttl
                self.swarmDic[torrent_hash][str(peer_ref)][1] = self.ttl
                #print 'Announce from: ' + str(peer_ref)  # -----DEBUGGING LINE-----
            else:
                # si no existe lo incorporamos en el swarm
                self.swarmDic[torrent_hash][str(peer_ref)] = [peer_ref, self.ttl]
        else:
            # Sino existe el swarm lo creamos y incorporamos el peer
            self.swarmDic[torrent_hash] = {str(peer_ref): [peer_ref, self.ttl]}

    # Metodo 'get_peers'
    # Devuelve una lista de proxys de 3 peers aleatorios.
    # En caso de tener un numero de proxys menor o igual a 3, retorna los 3 disponibles.
    def get_peers(self, torrent_hash):
        # n es el numero de peers a devolver
        n = 2
        # Variable que contendra los proxies de los peers a devolver
        peers_2_return = []
        # Comprobamos que el swarm del torrent_hash existe
        if torrent_hash in self.swarmDic:
            peers_key = self.swarmDic[torrent_hash].keys()
            # Guardamos el numero de peers del swarm del hash
            num_peers = len(self.swarmDic[torrent_hash])

            #  Caso en que haya mas de tres peers en el swarm
            if num_peers > n:
                random_nums = []
                for i in range(n):
                    # Escogemos un numero aleatorio entre 0 y num_peers
                    random_num = random.randrange(num_peers)
                    # Comprobamos que no lo tengamos seleccionado
                    while random_num in random_nums:
                        random_num = random.randrange(num_peers)
                    peers_2_return.append(self.swarmDic[torrent_hash][peers_key[random_num]][0])
                    random_nums.append(random_num)
            else:
                # Si disponemos menos de 3 devolvemos todos
                for i in range(num_peers):
                    peers_2_return.append(self.swarmDic[torrent_hash][peers_key[i]][0])

        return peers_2_return

    # Metodo que se encarga de comprobar el ttl de los peers
    # y eliminar de cada swarm aquellos que no estan activos
    def check_peers(self):
        for swarm in self.swarmDic:
            if bool(self.swarmDic[swarm]):
                temp_dic = {}
                for peer in self.swarmDic[swarm]:
                    # Restamos el ttl una unidad
                    self.swarmDic[swarm][peer][1] -= 1
                    if self.swarmDic[swarm][peer][1] != 0:
                        temp_dic[peer] = self.swarmDic[swarm][peer]
                    else:
                        print str(peer) + " removed form the swarm"
                self.swarmDic[swarm] = temp_dic
                #print self.swarmDic[swarm]
            else:
                # si el swarm no tiene peers lo eliminamos
                # print 'el swarm \'' + swarm + '\' esta vacio'
                del self.swarmDic[swarm]


if __name__ == "__main__":
    # Inicializacion del contexto de la ejecucion del host
    # Por defecto el tipo de threads son los threads clasicos de python
    set_context()

    # Creacion del host que engendra el tracker
    host = create_host('http://127.0.0.1:1277/')

    # Generacion del 'tracker'
    tracker = host.spawn('tracker', Tracker)

    # Inicializacion del tracker
    tracker.init_start()

    # El tracker se mantiene vivo de forma indefinida
    serve_forever()
