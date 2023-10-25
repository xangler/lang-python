from enum import Enum
from pkg.message import Message
from pkg.utils import *

StreamType = Enum('StreamType', ("stdout", "stderr"))

class Stream(object):
    def __init__(self, session, pub_socket, type, max_buffer=200):
        self.session = session
        self.pub_socket = pub_socket
        self.type = type
        self._buffer = []
        self._buffer_len = 0
        self.max_buffer = max_buffer
        self.parent_header = {}

    def set_parent_header(self, parent_header):
        self.parent_header = parent_header

    def close(self):
        self.pub_socket = None

    def flush(self):
        if self.pub_socket is None:
            raise ValueError('I/O operation on closed file')
        else:
            if self._buffer:
                data = ''.join(self._buffer)
                content = {'name':self.type.name, 'data':data}
                msg = self.session.msg('stream', content=content,
                                       parent_header=self.parent_header)
                if self.type == StreamType.stdout:
                    printi(Message(msg))
                else:
                    printe(Message(msg))
                self.pub_socket.send_json(msg)
                self._buffer_len = 0
                self._buffer = []

    def isattr(self):
        return False

    def next(self):
        raise IOError('Read not supported on a write only stream.')

    def read(self, size=None):
        raise IOError('Read not supported on a write only stream.')

    readline=read

    def write(self, s):
        if self.pub_socket is None:
            raise ValueError('I/O operation on closed file')
        else:
            self._buffer.append(s)
            self._buffer_len += len(s)
            self._maybe_send()

    def _maybe_send(self):
        if '\n' in self._buffer[-1]:
            self.flush()
        if self._buffer_len > self.max_buffer:
            self.flush()

    def writelines(self, sequence):
        if self.pub_socket is None:
            raise ValueError('I/O operation on closed file')
        else:
            for s in sequence:
                self.write(s)