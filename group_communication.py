from pyactor.context import interval

'''

    Clase que define el gestor de la membresia del grupo. 
    API:
        - join()
        - get_members()
        - leave()

'''


class GroupMembershipManager:
    _ask = ['join', 'get_members', 'check_members']
    _tell = ['init_start', 'join']
    _ref = ['join']

    def __init__(self):
        self.members_dic = dict()
        self.ttl = 10
        self.interval1 = None

    def init_start(self):
        self.interval1 = interval(self.host, 1, self.proxy, 'check_members')

    def join(self, member_ref):
        if member_ref not in self.members_dic:
            for member in self.members_dic:
                member.add_member(member)
            self.members_dic[member_ref] = self.ttl

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
    _ask = ['add_member', 'remove_member']
    _tell = ['keep_alive']
    _ref = ['add_member', 'remove_member']

    # Metodo de inicializacion de la instancia de la clase
    def __init__(self):
        self.members_list = list()
        self.manager = None
        self.id = None
        self.delay = None
        self.interval1 = None

    # Metodo abstracto de inicializacion del miembro
    def init_start(self):
        pass

    # Metodo abstracto que procesara el mensaje y lo agregara a la cola
    def receive(self):
        pass

    # Metodo abstracto que procesara el mensaje que esta la cabeza de la cola
    def process_msg(self):
        pass

    # Metodo que realiza el keep_alive en contra del gestor
    def keep_alive(self):
        self.manager.keep_alive_receiver(self.proxy)

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

    Clase que define al miembro del modelo TOM con sequenciador.

'''


class MemberSeq(MemberGroup):
    MemberGroup._ref += []

    def __init__(self):
        MemberGroup.__init__(self)
        self.sequencer = None
        self.counter = 0

    def init_start(self):
        pass

    def multicast(self, msg, timestamp):
        for member in self.members_list:
            member.receive(msg, timestamp)

    def application(self):
        msg = 'msg from: ' + str(self.id)
        timestamp = self.sequencer.give_counter()
        self.multicast(msg, timestamp)

    # Metodo ejecutado por el miembro que realiza el papel de secuenciador
    def give_counter(self):
        current_counter = self.counter
        self.counter += 1
        return current_counter




'''

    Clase que define al miembro del modelo TOM con Lamport.

'''


class MemberLamp(MemberGroup):
    def __init__(self):
        MemberGroup.__init__(self)
