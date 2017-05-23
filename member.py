from pyactor.context import set_context, create_host, sleep, serve_forever, interval
from group_communication import MemberSeq
import sys
import time


if __name__ == "__main__":
    if len(sys.argv) > 3:
        host_port = sys.argv[1]
        member_id = sys.argv[2]
        manager_url = sys.argv[3]

        set_context()

        h = create_host('http://127.0.0.1:' + host_port + '/')

        manager_url += 'manager'

        manager = h.lookup_url(manager_url, 'GroupMembershipManager', 'manager')

        monitor = h.lookup_url('http://127.0.0.1:2178/monitor', 'Monitor', 'monitor')

        member = h.spawn(member_id, MemberSeq)

        print member_id + " spawned"

        member.init_start(manager, monitor, 2)

        serve_forever()

    else:
        print 'Missing argument\'s to execute the member'