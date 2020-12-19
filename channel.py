import socket

MESSAGE_PREFIX = '>I'
BUFFER = 4096


class chanMessageInterface:
    def __init__(self, chan):
        self.message_buffer = []
        self.chan = chan
        self.chan.setblocking(0)

    def send(self, msg):
        self.chan.send(MESSAGE_PREFIX + msg)

    def sendall_bytes(self, msg):
        self.chan.sendall(bytes(MESSAGE_PREFIX, 'utf-8') + msg)

    def recv(self):
        if not self.message_buffer:
            self.fill_buffer()
        if self.message_buffer:
            ret = self.message_buffer[0]
            self.message_buffer = self.message_buffer[1:] if len(self.message_buffer) > 1 else []
            return ret
        else:
            return None

    def fill_buffer(self):
        try:
            msgs = self.chan.recv(BUFFER).split(bytes(MESSAGE_PREFIX, 'utf-8'))
        except socket.timeout:
            # nothing on buffer
            msgs = []
        if msgs and msgs[0] != b'':
            self.message_buffer += msgs
        elif msgs and msgs[0] == b'':
            self.message_buffer += msgs[1:]

    def blocking_recv(self):
        msg = None
        while not msg:
            msg = self.recv()
        return msg