from pyactor.context import set_context, create_host, sleep, serve_forever, interval
from pyactor.exceptions import TimeoutError
from sys import stdout
import random


class Monitor:
    _tell = ['init_start', 'add_member', 'print_data',
             'add_member_msg']

    # Inicializador de la instancia del Monitor
    def __init__(self):
        # Dic formado por tuplas {member_id:{counter:mensaje}}
        self.members_dic = {}
        self.interval = None

    # Metodo 'init_start'
    def init_start(self):
        self.interval = interval(self.host, 1, self.proxy, 'print_data')

    def add_member(self, member_id):
        self.members_dic[member_id] = {}

    def add_member_msg(self, member_id, counter, msg):
        print 'add_member_msg'
        self.members_dic[member_id][counter] = msg

    def print_data(self):
        file_name = 'volcado.txt'

        f = open(file_name, 'w')
        for member in self.members_dic:
            f.write(member + ':\n')
            for counter in self.members_dic[member]:
                f.writelines('\t' + str(counter) + ':' + self.members_dic[member][counter] + '\n')
        f.close()

if __name__ == "__main__":
    set_context()

    # Creacion del host que engendra el monitor
    host = create_host('http://127.0.0.1:2178/')

    # Generacion del 'monitor'
    monitor = host.spawn('monitor', Monitor)

    monitor.init_start()

    # El monitor se mantiene vivo de forma indefinida
    serve_forever()