import os
import uuid
import zmq
from pkg.message import Message

class Session(object):
    def __init__(self, username=os.environ.get('USER','username')):
        self.username = username
        self.session = str(uuid.uuid4())
        self.msg_id = 0

    def msg_header(self):
        h = {
            'msg_id' : self.msg_id,
            'username' : self.username,
            'session' : self.session
        }
        self.msg_id += 1
        return h

    def msg(self, msg_type, content={}, parent_header={}):
        msg = {}
        msg['header'] = self.msg_header()
        msg['parent_header'] = parent_header or {}
        msg['msg_type'] = msg_type
        msg['content'] = content or {}
        return msg

    def send(self, socket, msg_type, content={}, parent_header={}, ident=None):
        msg = self.msg(msg_type, content, parent_header)
        if ident is not None:
            socket.send(ident, zmq.SNDMORE)
        socket.send_json(msg)
        return Message(msg)

    def recv(self, socket, mode=zmq.NOBLOCK):
        try:
            msg = socket.recv_json(mode)
        except zmq.ZMQError as e:
            if e.errno == zmq.EAGAIN:
                return None
            else:
                raise
        return Message(msg)

