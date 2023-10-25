import os
import sys
import time
import traceback
from code import CommandCompiler
import zmq

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from mod.session import Session
from mod.stream import StreamType, Stream
from mod.completer import KernelCompleter
from pkg.message import Message
from pkg.utils import *

class Kernel(object):
    def __init__(self, session, reply_socket, pub_socket):
        self.session = session
        self.reply_socket = reply_socket
        self.pub_socket = pub_socket
        self.user_ns = {}
        self.compiler = CommandCompiler()
        self.completer = KernelCompleter(self.user_ns)
        
        # Build dict of handlers for message types
        self.handlers = {}
        for msg_type in ['execute_request', 'complete_request']:
            self.handlers[msg_type] = getattr(self, msg_type)

    def execute_request(self, ident, parent):
        try:
            code = parent.content.code
        except:
            printe("Got bad msg: {}".format(parent))
            return
        try:
            comp_code = self.compiler(code, '<zmq-kernel>')
            sys.stdout.set_parent_header(dict(parent.header))
            sys.stderr.set_parent_header(dict(parent.header))
            exec(comp_code, self.user_ns)
        except:
            etype, evalue, tb = sys.exc_info()
            tb = traceback.format_exception(etype, evalue, tb)
            reply_content = {
                'status' : 'error',
                'traceback' : tb,
                'etype' : str(etype),
                'evalue' : str(evalue)
            }
        else:
            reply_content = {'status' : 'ok'}
        printi(self.session.send(self.reply_socket, 'execute_reply', reply_content, dict(parent.header), ident))

    def complete_request(self, ident, parent):
        matches = {'matches' : self.complete(parent), 'status' : 'ok'}
        printi(self.session.send(self.reply_socket, 'complete_reply', matches, dict(parent.header), ident))

    def complete(self, msg):
        return self.completer.complete(msg.content.line, msg.content.text)

    def start(self):
        while True:
            ident = self.reply_socket.recv()
            assert self.reply_socket.rcvmore, "Unexpected missing message part."
            msg = self.reply_socket.recv_json()
            omsg = Message(msg)
            printi(omsg)
            handler = self.handlers.get(omsg.msg_type, None)
            if handler is None:
                printe("UNKNOWN MESSAGE TYPE:{}".format(omsg))
            else:
                handler(ident, omsg)

def main():
    c = zmq.Context()

    ip = '127.0.0.1'
    port_base = 5555
    connection = ('tcp://%s' % ip) + ':%i'
    rep_conn = connection % port_base
    pub_conn = connection % (port_base+1)

    printi("Starting the kernel...")
    printi("On:{} {}".format(rep_conn, pub_conn))

    reply_socket = c.socket(zmq.ROUTER)
    reply_socket.bind(rep_conn)
    pub_socket = c.socket(zmq.PUB)
    pub_socket.bind(pub_conn)

    session = Session(username='kernel')
    sys.stdout = Stream(session, pub_socket, StreamType.stdout)
    sys.stderr = Stream(session, pub_socket, StreamType.stderr)

    kernel = Kernel(session, reply_socket, pub_socket)
    printi("Use Ctrl-\\ (NOT Ctrl-C!) to terminate.")
    kernel.start()

if __name__ == '__main__':
    main()
