import group_communication as gc
import time
import threading
import os


# Funcion que inicia el proceso que ejecutara al manager del grupo.
def manager_runner(file_src, host_port):
    command = 'python ' + file_src + ' ' + host_port
    os.system(command)


# Funcion que inicia el proceso que ejecutara a uno de los miembros del grupo.
def members_runner(file_src, host_port, actor_id, manager_url):
    command = 'python ' + file_src + ' ' + host_port + ' ' + actor_id + ' ' + manager_url
    os.system(command)


'''
 
 Inicio del programa.
 
'''
if __name__ == "__main__":
    manager_src = 'manager.py'
    member_src = 'member.py'
    manager_url = 'http://127.0.0.1:1277/'
    threads = list()

    # Ejecucion del gestor del grupo
    t = threading.Thread(target=manager_runner, args=(manager_src, manager_url))
    threads.append(t)
    t.start()
    time.sleep(1)

    num_member = 0
    for port in range(1650, 1660):
        # Ejecucion de los miembros del grupo
        actor = 'member' + str(num_member)
        t = threading.Thread(target=members_runner, args=(member_src, str(port), str(actor),
                                                              manager_url))
        threads.append(t)
        t.start()
        num_member += 1
        time.sleep(0.5)


