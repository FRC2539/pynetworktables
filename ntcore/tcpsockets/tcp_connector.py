
import socket

from .tcp_stream import TCPStream

def TcpConnector(server, port, timeout):
    def _connect():
        
        if timeout == 0:
            sd = socket.create_connection((server, port))
        else:
            sd = socket.create_connection((server, port), timeout)
        
        return TCPStream(sd, server, port)
