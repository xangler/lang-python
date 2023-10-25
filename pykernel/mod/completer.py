
import itertools
import readline
import rlcompleter
import time

class KernelCompleter(object):
    """Kernel-side completion machinery."""
    def __init__(self, namespace):
        self.namespace = namespace
        self.completer = rlcompleter.Completer(namespace)

    def complete(self, line, text):
        matches = []
        for state in itertools.count():
            comp = self.completer.complete(text, state)
            if comp is None:
                break
            matches.append(comp)
        return matches

class ClientCompleter(object):    
    def __init__(self, session, socket):
        self.session = session
        self.socket = socket
        self.matches = []

    def request_completion(self, text):
        line = readline.get_line_buffer()
        self.session.send(self.socket, 'complete_request', dict(text=text, line=line))

        for _ in range(5):
            rep = self.session.recv(self.socket)
            if rep is not None and rep.msg_type == 'complete_reply':
                matches = rep.content.matches
                break
            time.sleep(0.1)
        else:
            matches = None
        return matches
    
    def complete(self, text, state):
        if state==0:
            matches = self.request_completion(text)
            if matches is None:
                self.matches = []
            else:
                self.matches = matches
        try:
            return self.matches[state]
        except IndexError:
            return None
