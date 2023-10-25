import os
import code
import readline
import sys
import time
import zmq

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from mod import session
from mod import completer
from mod.stream import StreamType
from pkg.utils import *

class Console(code.InteractiveConsole):
    def __init__(self, locals=None, filename="<console>",
                 session = session,
                 request_socket=None,
                 sub_socket=None):
        code.InteractiveConsole.__init__(self, locals, filename)
        self.session = session
        self.request_socket = request_socket
        self.sub_socket = sub_socket

        # Set tab completion
        self.completer = completer.ClientCompleter(session, request_socket)
        readline.parse_and_bind('tab: complete')
        readline.parse_and_bind('set show-all-if-ambiguous on')
        readline.set_completer(self.completer.complete)

        sys.ps1 = 'Py>>> '
        self.handlers = {}
        for msg_type in ['stream']:
            self.handlers[msg_type] = getattr(self, 'handle_%s' % msg_type)

    def handle_stream(self, omsg):
        if omsg.content.name == StreamType.stdout.name:
            print(omsg.content.data, file=sys.stdout, end="")
        else:
            print('*ERR*', file=sys.stderr)
            print(omsg.content.data, file=sys.stderr, end="")

    def recv_channel(self):
        while True:
            omsg = self.session.recv(self.sub_socket)
            if omsg is None:
                break
            handler = self.handlers.get(omsg.msg_type, None)
            if handler is not None:
                handler(omsg)

    def handle_reply(self, rep):
        if rep is None:
            return
        if rep.content.status == 'error':
            printe("{}:{}".format(rep.content.etype, rep.content.evalue))
            printe("{}".format("".join(rep.content.traceback)))
        elif rep.content.status == 'aborted':
            printe("ERROR: ABORTED")

    def recv_reply(self):
        rep = self.session.recv(self.request_socket)
        self.handle_reply(rep)
        return rep

    def runcode(self, code):
        self.recv_channel()
        src = '\n'.join(self.buffer)
        self.session.send(self.request_socket, 'execute_request', dict(code=src))
        while True:
            rep = self.recv_reply()
            time.sleep(0.05)
            self.recv_channel()
            if rep is not None:
                break

def main():
    ip = '127.0.0.1'
    port_base = 5555
    connection = ('tcp://%s' % ip) + ':%i'
    req_conn = connection % port_base
    sub_conn = connection % (port_base+1)
    
    # Create initial sockets
    c = zmq.Context()
    request_socket = c.socket(zmq.DEALER)
    request_socket.connect(req_conn)
    sub_socket = c.socket(zmq.SUB)
    sub_socket.connect(sub_conn)
    sub_socket.setsockopt_string(zmq.SUBSCRIBE, '')

    # Make session and user-facing client
    sess = session.Session()
    client = Console(None, '<zmq-console>', sess, request_socket, sub_socket)
    client.interact()

if __name__ == '__main__':
    main()
