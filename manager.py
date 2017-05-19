from pyactor.context import set_context, create_host, sleep, serve_forever, interval
from group_communication import GroupMembershipManager
import sys


if __name__ == "__main__":
    print
    if len(sys.argv) > 1:
        manager_url = sys.argv[1]

        # Inicializacion del contexto de la ejecucion del host
        set_context()

        # Creacion del host que engendra el manager
        host = create_host(manager_url)

        # Generacion del 'manager'
        manager = host.spawn('manager', GroupMembershipManager)

        # Inicializacion del manager
        manager.init_start()

        # El manager se mantiene vivo de forma indefinida
        serve_forever()
    else:
        print 'Missing argument\'s to execute the manager'