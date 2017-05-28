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
        self.ttl = 5
        self.interval1 = None

    def init_start(self):
        self.interval1 = interval(self.host, 1, self.proxy, 'check_members')

    def join(self, member_ref):
        if member_ref not in self.members_dic:
            for member in self.members_dic:
                member.add_member(member_ref)
            self.members_dic[member_ref] = self.ttl
            print self.id + ': ' + str(member_ref) + ' joined'
            return 'accepted'

    def get_members(self):
        return self.members_dic.keys()

    def leave(self, member_ref):
        if member_ref in self.members_dic:
            del self.members_dic[member_ref]

    def keep_alive_receiver(self, member_ref):
        if member_ref in self.members_dic:
            self.members_dic[member_ref] = self.ttl

    def check_members(self):
        for member in self.members_dic:
            self.members_dic[member] -= 1
            if self.members_dic[member] == 0:
                del self.members_dic[member]
                print self.id + ': longitud members_dic -> ' + str(len(self.members_dic))


'''

    Clase abstracta que define al miembro del grupo.

'''


class MemberGroup:
    _ask = ['init_start']
    _tell = ['add_member', 'process_msg']
    _ref = ['add_member']

    # Metodo de inicializacion de la instancia de la clase
    def __init__(self):
        self.members_list = list()
        self.manager = None
        self.monitor = None
        self.id = None
        self.latency = None
        self.messages = {}

    # Metodo abstracto que procesara el mensaje que esta la cabeza de la cola
    def process_msg(self):
        pass

    # Metodo para agregar un miembro notificado por el gestor
    def add_member(self, member_ref):
        if member_ref not in self.members_list:
            self.members_list.append(member_ref)

    # Metodo abstracto de la aplicacion que ejecutara el miembro
    def application(self):
        pass


'''

    Clase que define al miembro del modelo TOM con secuenciador.

'''


class MemberSeq(MemberGroup):
    MemberGroup._ask += ['receive_candidate', 'send_counter']
    MemberGroup._tell += ['keep_alive', 'check_candidates', 'receive_candidate', 'application', 'ack_election_done',
                          'check_electors', 'multicast', 'receive']
    MemberGroup._ref += ['init_start', 'keep_alive', 'receive_candidate','application',
                         'ack_election_done', 'check_electors', 'multicast']

    # Inicializador de la clase 'MemberSeq'
    def __init__(self):
        MemberGroup.__init__(self)
        self.sequencer = None
        # Variable contador utilizada por el secuenciador
        self.counter = 0
        # Variable contador utilizado por los miembros
        self.next_counter = 0
        self.candidate = None
        self.candidates = {}
        self.electors = {}
        self.interval_kalive = None
        self.interval_app = None
        self.interval_ccandidate = None
        self.interval_celectors = None
        self.interval_pmsg = None

    def init_start(self, manager, monitor, latency):
        self.manager = manager
        self.monitor = monitor
        self.latency = latency
        response = manager.join(self.proxy)
        self.monitor.add_member(self.id)
        if response == 'accepted':
            # Inicializacion del intervalo del keep_alive
            self.interval_kalive = interval(self.host, 1, self.proxy, 'keep_alive')
            # Inicializacion del intervalo de la aplicacion
            self.interval_app = interval(self.host, latency, self.proxy, 'application')
            # Inicializacion del intervale del process_msg
            self.interval_pmsg = interval(self.host, 2, self.proxy, 'process_msg')
            print self.id + ': joined'

    def multicast(self, msg, counter):
        self.members_list = self.manager.get_members()
        self.members_list.remove(self.proxy)
        # print self.id + ': doing multicast'
        for member in self.members_list:
            # print self.id + ': sending msg to ' + str(member)
            member.receive(msg, counter)
            # print self.id + ': msg sended to ' + str(member)
        # print self.id + ': multicast done'
        self.messages[counter] = msg

    # Metodo que simula la aplicacion
    def application(self):
        msg = 'msg from: ' + str(self.id)

        try:
            print self.id + ': Asking counter to sequencer.'
            # Ojo! Mientras esta esperando, el actor se bloquea y no hace keep_alive. No execeder el tiempo del ttl
            # que proporciona el manager ni poner un tiempo mayor al periodo de ejecucion de la aplicacion
            counter = self.sequencer.send_counter(timeout = 1)
            if counter is not None:
                print self.id + ': value of the obtained counter -> ' + str(counter)
                self.multicast(msg, counter)
        except Exception:
            print self.id + ': Sequencer not found. Starting election.'
            # Si falla el secuenciador, iniciar el proceso de eleccion
            # Se detiene el intervalo de la aplicacion
            self.interval_app.set()
            # Se reinicia el dic de las tuplas 'proxy':'id' de los candidatos
            self.candidates = {}
            self.electors = {}
            self.sequencer = None
            # Se inicia el intervalo de la comprobacion de candidatos
            self.interval_ccandidate = interval(self.host, 1, self.proxy, 'check_candidates')
            # print self.id + ': exception catched ->' + str(Exception)

    # Metodo que comprueba la obtencion de las candidaturas de forma periodica y inicializa
    # la eleccion del secuenciador una vez se obtienen todas.
    def check_candidates(self):
        # Mandamos a todos los miembros nuestra candidatura para ser el secuenciador
        member_list = self.manager.get_members()
        for member in member_list:
            member.receive_candidate(self.proxy, self.id)

        # Comprobamos si ya hemos obtenido todas las candidaturas
        if len(self.candidates) == len(member_list):
            # Seleccionamos como candidato el que tenga el mayor id
            self.candidate = member_list[0]
            for member in member_list:
                if self.candidates[member] > self.candidates[self.candidate]:
                    self.candidate = member
            # Avisamos a cada miembro que hemos acabado nuestra eleccion y el resultado de esta
            for member in member_list:
                member.ack_election_done(self.proxy, self.candidate)
            # Detenemos el intervalo del 'check_candidates'
            self.interval_ccandidate.set()
            print self.id + ': check_candidates done'
            # Iniciamos la ejecucion del intervalo del check_electors
            self.interval_celectors = interval(self.host, 1, self.proxy, 'check_electors')

    # Metodo que recibe la candidatura de cada miembro para la eleccion del secuenciador
    def receive_candidate(self, member_ref, member_id):
        # print self.id + ': candidature received from -> "' + member_id + '"'
        self.candidates[member_ref] = int(member_id.replace('member', ''))

    # Metodo que recibe el candidato a secuenciador elegido por los que han terminado el proceso de eleccion
    def ack_election_done(self, member_ref, candidate):
        # print self.id + ': ack_election_done -> ' + str(member_ref)
        self.electors[member_ref] = candidate
        # print self.id + ': list electors length -> ' + str(len(self.electors))

    # Metodo que comprueba que todos los miembros han terminado la eleccion del candidato
    # al secuenciador y que una vez terminada comprueba si se ha llegado al mismo resultado
    def check_electors(self):
        member_list = self.manager.get_members()
        # print self.id + ': list members length -> ' + str(len(member_list)) + '; from check_electors'
        # print self.id + ': list electors length -> ' + str(len(self.electors)) + '; from check_electors'
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
            # Si no ha habido acuerdo reiniciamos la applicacion para que se reinicie el proceso de eleccion
            # y si lo hay, todos menos el secuenciador reiniciaran la ejecucion de la aplicacion
            if self.sequencer is None or self.proxy != self.sequencer:
                self.interval_app = interval(self.host, self.latency, self.proxy, 'application')
        else:
            # Volvermos a mandar nuestra candidatura en el caso de que no todos los miembros la hayan recibido
            member_list = self.manager.get_members()
            # print self.id + ': list members length -> ' + str(len(member_list))
            # print self.id + ': list candidates length -> ' + str(len(self.candidates))
            for member in member_list:
                member.receive_candidate(self.proxy, self.id)

    # Metodo ejecutado por el miembro que realiza el papel de secuenciador
    def send_counter(self):
        # Condicion para forzar a que no se devuelva contador a los miembros adelantados en la eleccion del lider
        # antes de que este mismo sepa que es el lider.
        if self.proxy == self.sequencer:
            if self.counter < 10:
                print self.id + ': SENDING COUNTER'
                current_counter = self.counter
                self.counter += 1
                return current_counter
            else:
                # Paramos lo ejecucion del host del actor
                self.proxy.stop()
        else:
            return None

    # Metodo que realiza el keep_alive en contra del gestor
    def keep_alive(self):
        self.manager.keep_alive_receiver(self.proxy)
        # print self.id + ' keep_alive warning --------------'

    # Metodo que recibe un mensaje y lo agregara a la cola
    def receive(self, message, counter):
        self.messages[counter] = message

    # Metodo que procesara los mensajes en la cola por orden de los contadores
    def process_msg(self):
        while self.next_counter in self.messages:
            self.monitor.add_member_msg(self.id, self.next_counter, self.messages[self.next_counter])
            del self.messages[self.next_counter]
            self.next_counter += 1

'''

    Clase que define al miembro del modelo TOM con Lamport.

'''


class MemberLamp(MemberGroup):
    def __init__(self):
        MemberGroup.__init__(self)
