
import select
import socket

class StreamEOF(IOError):
    pass

# From original pynet
class ReadStream:
    def __init__(self, f):
        self.f = f

    def read(self, size=-1):
        data = self.f.read(size)
        if size is not None and size > 0 and len(data) != size:
            raise StreamEOF("end of file")
        return data

    def readStruct(self, s):
        data = self.f.read(s.size)
        if len(data) != s.size:
            raise StreamEOF("end of file")
        return s.unpack(data)



class TCPStream(object):

    def __init__(self, sd, peer_ip, peer_port):
        
        self.m_sd = sd
        self.m_peerIP = peer_ip
        self.m_peerPort = peer_port
    
    def __del__(self):
        self.close()    
    
    def send(self, buffer, len, err):
        # TODO: change to return True/False (unless this gets changed to a stream
        if self.m_sd < 0:
            *err = kConnectionClosed
            return False
    
    #ifdef _WIN32
        WSABUF wsaBuf
        wsaBuf.buf = const_cast<char*>(buffer)
        wsaBuf.len = (ULONG)len
        DWORD rv
        result = True
        while (WSASend(m_sd, &wsaBuf, 1, &rv, 0, nullptr, nullptr) == SOCKET_ERROR)
            if WSAGetLastError() != WSAEWOULDBLOCK:
                result = False
                break
    
            Sleep(1)
    
        if not result:
            char Buffer[128]
    #ifdef _MSC_VER
            sprintf_s(Buffer, "Send() failed: WSA error=%d\n", WSAGetLastError())
    #else:
            std.snprintf(Buffer, 128, "Send() failed: WSA error=%d\n", WSAGetLastError())
    #endif
            OutputDebugStringA(Buffer)
            *err = kConnectionReset
            return 0
    
    #else:
        rv = write(m_sd, buffer, len)
        if rv < 0:
            *err = kConnectionReset
            return 0
    
    #endif
        return static_cast<std.size_t>(rv)
    
    
    std.size_t TCPStream.receive(char* buffer, len, err,
                                   int timeout)
        if self.m_sd < 0:
            *err = kConnectionClosed
            return 0
    
    #ifdef _WIN32
        int rv
    #else:
        ssize_t rv
    #endif
        if timeout <= 0:
    #ifdef _WIN32
            rv = recv(m_sd, buffer, len, 0)
    #else:
            rv = read(m_sd, buffer, len)
    #endif
    
        elif _waitForReadEvent(timeout):
    #ifdef _WIN32
            rv = recv(m_sd, buffer, len, 0)
    #else:
            rv = read(m_sd, buffer, len)
    #endif
    
        else:
            *err = kConnectionTimedOut
            return 0
    
        if rv < 0:
            *err = kConnectionReset
            return 0
    
        return static_cast<std.size_t>(rv)
    
    
    def close(self):
        if self.m_sd:
            self.m_sd.shutdown(socket.SHUT_RDWR)
            self.m_sd.close()
        
        self.m_sd = None
    
    
    def getPeerIP(self):
        return self.m_peerIP
    
    def getPeerPort(self):
        return self.m_peerPort
    
    def setNoDelay(self):
        self.m_sd.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    
    def _waitForReadEvent(self, timeout):
        r, _, _ = select.select((self.m_sd,),(),(), timeout)
        return len(r) > 0
