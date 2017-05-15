import group_communication as gc
import threading
import os


# Funcion que inicia el proceso que ejecutara al manager del grupo.
def manager_runner(file_src, host_port):
    command = 'python ' + file_src + ' ' + host_port
    os.system(command)


# Funcion que inicia el proceso que ejecutara uno de los miembros del grupo.
def members_runner(file_src, host_port, actor_id, manager_url):
    command = 'python ' + file_src + ' ' + host_port + ' ' + actor_id + ' ' + manager_url
    os.system(command)


if __name__ == "__main__":
    manager_src = 'manager.py'
    member_src = 'member.py'
    manager_url = 'http://127.0.0.1:1277/'
    threads = list()

    num_thread = 0
    for port in range(1650, 1651):
        if num_thread == 0:
            # Ejecucion del gestor del grupo
            t = threading.Thread(target=manager_runner, args=(manager_src, manager_url))
        else:
            # Ejecucion de los miembros del grupo
            actor = 'member' + str(num_member)
            t = threading.Thread(target=members_runner, args=(member_src, str(port), str(actor),
                                                              manager_url))
        threads.append(t)
        t.start()
        num_thread += 1


