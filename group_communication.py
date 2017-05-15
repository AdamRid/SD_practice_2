import pyactor

'''

    Clase que define el gestor de la membresia del grupo. 
    API:
        - join()
        - get_members()
        - leave()

'''
class GroupMembershipManager:
    _ask = ['join']
    _tell = ['init_start']
    _ref = ['join']

    def __init__(self):
        self.members_dic = {}
        self.ttl = 10
        self.sequencer = None

    def init_start(self):
        pass

    def join(self, member_ref):
        if member_ref not in self.members_dic:
            for member in self.members_dic:
                member.add_member(member)
            self.members_dic[member_ref] = self.ttl

    def get_members(self):
        return self.members_dic.keys()

    def leave(self):
        pass

    def keep_alive_receiver(self, member_ref):
        if member_ref in self.members_dic:
            self.members_dic[member_ref] = self.ttl

    def check_members(self):
        updated = False

        for member in self.members_dic:
            self.members_dic[member] -= 1
            if self.members_dic[member] == 0:
                del self.members_dic[member]
                updated = True

        if updated:
            for member in self.members_dic:
                member.update_members(self.members_dic.keys())

'''

    Clase abstracta que define el miembros del grupo.
    
'''
class MemberGroup:
    _ask = []
    _tell = []
    _ref = ['update_members']

    def __init__(self):
        self.manager = None
        self.id = None
        self.delay = None

    def init_start(self):
        pass

    def multicast(self):
        pass

    def receive(self):
        pass

    def process_msg(self):
        pass

    def keep_alive(self):
        pass

    def add_member(self, member):
        pass

    def remove_member(self, member):
        pass


'''

    Clase que define el miembro del modelo TOM con sequenciador.
    
'''
class MemberSeq(MemberGroup):
    MemberGroup._ref += []

    def __init__(self, manager):
        MemberGroup.__init__(self, manager)
        self.sequencer = None
        self.counter = 0

    def multicast(self):
        pass

    def give_counter(self):
        current_counter  = self.counter
        self.counter += 1
        return current_counter

'''

    Clase que define al miembro del modelo TOM con Lamport.
    
'''
class MemberLamp(MemberGroup):
    def __init__(self):
        MemberGroup.__init__(self)
