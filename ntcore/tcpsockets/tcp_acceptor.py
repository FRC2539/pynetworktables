
import socket

from .tcp_stream import TCPStream

import logging
logger = logging.getLogger('nt')

class TcpAcceptor(object):
    
    def __init__(self, port, address):
        self.m_lsd = None
        self.m_port = port
        self.m_address = address
        self.m_listening = False
        self.m_shutdown = False
    
    def __del__(self):
        self.close()
            
    def close(self):
        if self.m_lsd:
            self.shutdown()
            self.m_lsd.close()
        self.m_lsd = None
    
    def start(self):
        if self.m_listening:
            return False
    
        self.m_lsd = socket.socket()
        
        self.m_lsd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.m_lsd.bind((self.m_address, self.m_port))
        self.m_lsd.listen(5)
        
        self.m_listening = True
        return True
    
    def shutdown(self):
        self.m_shutdown = True
        self.m_lsd.shutdown(socket.SHUT_RDWR)
    
    def accept(self):
        if not self.m_listening or self.m_shutdown:
            return
        
        sd, address = self.m_lsd.accept()
        
        if self.m_shutdown:
            sd.close()
            return
        
        return TCPStream(sd, address)
