from pyactor.context import set_context, create_host, sleep, serve_forever, interval
from pyactor.exceptions import TimeoutError
from sys import stdout
import random


class Monitor(object):
    _tell = ['init_start', 'current_mod', 'notify', 'inbox', 'calculate_average']
    _ref = ['current_mod', 'notify', 'inbox']

    # Inicializador de la instancia del Monitor
    def __init__(self):
        self.peer_data_dic = {}
        self.mod = ''
        self.current_second = 0
        self.chunks_number = 0
        self.average_list = []
        self.interval1 = None

    # Metodo 'init_start'
    def init_start(self, mod, chunks_number):

        mods = ['unknown mod', 'push', 'pull', 'push & pull']
        if (mod >= 1) and (mod <= 3):
            self.mod = mods[mod]
        else:
            self.mod = mods[0]

        self.chunks_number = chunks_number

        self.interval1 = interval(self.host, 1, self.proxy, 'calculate_average')

    # Metodo 'notify'
    def notify(self, peer_id):
        self.peer_data_dic[peer_id] = 0

    # Metodo 'inbox'
    def inbox(self, peer_data):
        #print peer_data
        self.peer_data_dic[peer_data[0]] = round((peer_data[1] * 100) / float(self.chunks_number), 2)
        print self.peer_data_dic
       # stdout.write("\r%s" % self.data_dic)

    # Metodo 'calculate_average'
    def calculate_average(self):
        average = 0
        if len(self.peer_data_dic):
            total_chunks = 0
            for item in self.peer_data_dic:
                total_chunks += self.peer_data_dic[item]
            average = round(total_chunks / float(len(self.peer_data_dic)), 2)

        self.average_list.append([self.current_second, average])
        self.current_second += 1

        if average == 100:
            self.interval1.set()
            file = open("monitor.txt", 'w')

            file.write('Mod: ' + self.mod + '\n')

            for item in self.average_list:
                # data = 'second ' + str(item[0]) + ': ' + str(item[1]) + '\n'
                data = str(item[1]) + '\n'
                file.write(data)
            file.close()
            print "My job is done."


if __name__ == "__main__":
    set_context()

    # Creacion del host que engendra el monitor
    host = create_host('http://127.0.0.1:1278/')

    # Generacion del 'monitor'
    monitor = host.spawn('monitor', Monitor)

    # El monitor se mantiene vivo de forma indefinida
    serve_forever()
