from pyactor.context import interval

'''

    Clase que define el gestor de la membresia del grupo. 
    API:
        - join()
        - get_members()
        - leave()

'''


class GroupMembershipManager:
    _ask = ['join', 'get_members']
    _tell = ['init_start', 'check_members', 'keep_alive_receiver']
    _ref = ['join', 'keep_alive_receiver', 'get_members']

    def __init__(self):
        self.members_dic = dict()
        self.ttl = 10
        self.interval1 = None

    def init_start(self):
        self.interval1 = interval(self.host, 1, self.proxy, 'check_members')

    def join(self, member_ref):
        if member_ref not in self.members_dic:
            i = 0
            for member in self.members_dic:
                member.add_member(member_ref)
                print i
                i += 1
            self.members_dic[member_ref] = self.ttl
            print str(member_ref) + ': joined'
            return 'accepted'

    def get_members(self):
        return self.members_dic.keys()

    def leave(self, member_ref):
        if member_ref in self.members_dic:
            del self.members_dic[member_ref]
            for member in self.members_dic:
                member.remove_member(member_ref)

    def keep_alive_receiver(self, member_ref):
        if member_ref in self.members_dic:
            self.members_dic[member_ref] = self.ttl

    def check_members(self):
        for member in self.members_dic:
            self.members_dic[member] -= 1
            if self.members_dic[member] == 0:
                del self.members_dic[member]
                for member_r in self.members_dic:
                    member_r.remove_member(member)


'''

    Clase abstracta que define al miembro del grupo.

'''


class MemberGroup:
    _ask = ['remove_member', 'init_start']
    _tell = ['add_member']
    _ref = ['add_member', 'remove_member']

    # Metodo de inicializacion de la instancia de la clase
    def __init__(self):
        self.members_list = list()
        self.manager = None
        self.id = None
        self.latency = None

    # Metodo abstracto que procesara el mensaje que esta la cabeza de la cola
    def process_msg(self):
        pass

    # Metodo para agregar un miembro notificado por el gestor
    def add_member(self, member_ref):
        if member_ref not in self.members_list:
            self.members_list.append(member_ref)

    # Metodo para eliminar un miembro notificado por el gestor
    def remove_member(self, member_ref):
        if member_ref in self.members_list:
            self.members_list.remove(member_ref)

    # Metodo abstracto de la aplicacion que ejecutara el miembro
    def application(self):
        pass


'''

    Clase que define al miembro del modelo TOM con secuenciador.

'''


class MemberSeq(MemberGroup):
    MemberGroup._ask += ['receive_candidate', 'send_counter', ]
    MemberGroup._tell += ['keep_alive', 'check_candidate',
                          'receive_candidate', 'application', 'check_candidate',
                          'ack_election_done', 'check_electors', 'multicast',
                          'receive','ack_candidate']
    MemberGroup._ref += ['init_start', 'keep_alive', 'receive_candidate',
                         'application', 'ack_candidate', 'ack_election_done',
                         'check_electors', 'multicast']

    # Inicializador de la clase 'MemberSeq'
    def __init__(self):
        MemberGroup.__init__(self)
        self.sequencer = None
        self.counter = 0
        self.candidate = None
        self.candidates = {}
        self.electors = {}
        self.interval_kalive = None
        self.interval_app = None
        self.interval_ccandidate = None
        self.interval_celectors = None

    def init_start(self, manager, latency):
        self.manager = manager
        self.latency = latency
        response = manager.join(self.proxy)
        if response == 'accepted':
            # Inicializacion del intervalo del keep_alive
            self.interval_kalive = interval(self.host, 1, self.proxy, 'keep_alive')
            # Inicializacion del intervalo de la aplicacion
            self.interval_app = interval(self.host, latency, self.proxy, 'application')
            # DEBUG LINE
            print self.id + ': joined'

    def multicast(self, msg, counter):

        self.members_list = self.manager.get_members()
        self.members_list.remove(self.proxy)
        print self.id + ': doing multicast'
        for member in self.members_list:
            print self.id + ': sending msg to ' + str(member)
            member.receive(msg, counter)
            print self.id + ': msg sended to ' + str(member)
        print self.id + ': multicast done'

    # Metodo abstracto que procesara el mensaje y lo agregara a la cola
    def receive(self, message, counter):
        pass

    # Metodo que simula la aplicacion
    def application(self):
        msg = 'msg from: ' + str(self.id)
        try:
            counter = self.sequencer.send_counter()
            print self.id + ': counter value -> ' + str(counter)
            self.multicast(msg, counter)
        except Exception:
            # Si falla el secuenciador, iniciar el proceso de eleccion
            # Se detiene el intervalo de la aplicacion
            self.interval_app.set()
            # Se reinicia el dic de 'proxy':'id' de los candidatos
            self.candidates = {}
            # Se inicia el intervalo de la comprobacion de candidatos
            self.interval_ccandidate = interval(self.host, 2, self.proxy, 'check_candidate')
            # Mandamos a todos los miembros nuestra candidatura para ser el secuenciador
            member_list = self.manager.get_members()
            print self.id + ': list members length -> ' + str(len(member_list))
            for member in member_list:
                member.receive_candidate(self.proxy, self.id)
            # print str(Exception) + ' from ' + self.id

    # Metodo ejecutado por el miembro que realiza el papel de secuenciador
    def send_counter(self):
        print self.id + ': echo from send_counter'
        current_counter = self.counter
        self.counter += 1
        return current_counter

    # Metodo que recibe la candidatura de cada miembro para la eleccion del secuenciador
    def receive_candidate(self, member_ref, member_id):
        #print self.id + ': receive_candidate "' + member_id + '"'
        self.candidates[member_ref] = member_id

    def ack_candidate(self, member_ref,  candidate):
        self.members_acks[member_ref] = candidate

    # Metodo que comprueba la obtencion de las candidaturas de forma periodica y inicializa
    # la eleccion del secuenciador una vez se obtienen todas.
    def check_candidate(self):
        member_list = self.manager.get_members()
        # Comprobamos si hemos obtenido todas las candidaturas
        if len(self.candidates) == len(member_list):
            # Seleccionamos como candidato el que tenga el mayor id
            self.candidate = member_list[1]
            for member in member_list:
                if self.candidates[member] > self.candidates[self.candidate]:
                    self.candidate = member
            # Avisamos a cada miembro que hemos acabado nuestra eleccion y el resultadp
            # de esta
            for member in member_list:
                member.ack_election_done(self.proxy, self.candidate)
            # Detenemos el intervalo del 'check_candidate'
            self.interval_ccandidate.set()
            # Iniciamos la ejecucion del intervalo del check_electors
            self.interval_celectors = interval(self.host, 1, self.proxy, 'check_electors')
            print self.id + ': check_candidate done'
        else:
            # En caso contrario volvemos a mandar nuestra candidatura
            member_list = self.manager.get_members()
            print self.id + ': list members length -> ' + str(len(member_list))
            print self.id + ': list candidates length -> ' + str(len(self.candidates))
            for member in member_list:
                member.receive_candidate(self.proxy, self.id)

    # Metodo que comprueba que todos los miembros han terminado la eleccion del candidato
    # al secuenciador y que una vez terminada realiza los ack's del candidato con los demas
    # miembros para comprobar si se ha llegado al mismo resultado
    def check_electors(self):
        member_list = self.manager.get_members()
        if len(self.electors) == len(member_list):
            accordance = True
            for elector in self.electors:
                if self.electors[elector] != self.candidate:
                    accordance = False
                    break
            # Detenemos el intervalo del 'check_electors'
            self.interval_celectors.set()
            if accordance:
                self.sequencer = self.candidate
                print self.id + ': sequencer elected -> ' + str(self.sequencer)

                if self.proxy == self.sequencer:
                    self.counter = 0
                else:
                    # Todos los miembtos a excepcion del secuenciador reiniciaran la ejecucion de
                    # la aplicacion
                    self.interval_app = interval(self.host, self.latency, self.proxy, 'application')

            else:
                # En caso de na haber acuerdo rReiniciamos la ejecucion de la applicacion
                # para que se reinicie el proceso de eleccion
                self.interval_app = interval(self.host, self.latency, self.proxy, 'application')
            print self.id + ': check_electors done'
        else:
            # En caso contrario volvemos a mandar nuestra candidatura
            member_list = self.manager.get_members()
            print self.id + ': list members length -> ' + str(len(member_list))
            print self.id + ': list candidates length -> ' + str(len(self.candidates))
            for member in member_list:
                member.receive_candidate(self.proxy, self.id)

    # Metodo que recibe a los miembros que han terminado la eleccion del candidato
    # al secuenciador
    def ack_election_done(self, member_ref, candidate):
        self.electors[member_ref] = candidate

    # Metodo que realiza el keep_alive en contra del gestor
    def keep_alive(self):
        self.manager.keep_alive_receiver(self.proxy)




'''

    Clase que define al miembro del modelo TOM con Lamport.

'''


class MemberLamp(MemberGroup):
    def __init__(self):
        MemberGroup.__init__(self)
