# novalidate

import threading
import socket

from .tcp_stream import TCPStream

import logging
logger = logging.getLogger('nt')

class TcpAcceptor(object):
    
    def __init__(self, port, address):
        # Protects open/shutdown/close
        self.lock = threading.RLock()
        
        self.m_lsd = None
        self.m_port = port
        self.m_address = address
        self.m_listening = False
        self.m_shutdown = False
            
    def close(self):
        
        with self.lock:
            if self.m_lsd:
                self.shutdown()
                self.m_lsd.close()
            
            self.m_lsd = None
    
    def start(self):
        with self.lock:
            if self.m_listening:
                return False
            
            self.m_lsd = socket.socket()
            
            try:
                self.m_lsd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.m_lsd.bind((self.m_address, self.m_port))
                self.m_lsd.listen(10)
            except OSError:
                logger.exception("Error starting server")
                
                try:
                    self.m_lsd.close()
                except Exception:
                    pass
                
                self.m_lsd = None
                return False
            
            self.m_listening = True
            return True
    
    def shutdown(self):
        with self.lock:
            if not self.m_shutdown:
                self.m_shutdown = True
                self.m_lsd.shutdown(socket.SHUT_RDWR)
    
    def accept(self):
        if not self.m_listening or self.m_shutdown:
            return
        
        try:
            sd, (peer_ip, peer_port) = self.m_lsd.accept()
        except OSError:
            if not self.m_shutdown:
                logger.warning("Error accepting connection", exc_info=True)
            return
        
        if self.m_shutdown:
            try:
                sd.close()
            except Exception:
                pass
            return
        
        return TCPStream(sd, peer_ip, peer_port)
