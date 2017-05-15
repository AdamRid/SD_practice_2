import os
import time
import threading


def run_peer(file, peer_port, actor_id, hash):
    print file
    command = 'python ' + file + ' ' + peer_port + ' ' + actor_id + ' ' + hash
    os.system(command)


if __name__ == "__main__":
    peer_script = 'peer.py'
    hash = 'hash0'
    threads = list()
    num_peer = 0
    for port in range(1650, 1655):
        actor = 'peer' + str(num_peer)

        t = threading.Thread(target=run_peer, args=(peer_script, str(port), str(actor),
                                                    hash))
        threads.append(t)
        t.start()
        num_peer += 1
        #time.sleep(1)
