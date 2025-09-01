import socket
import select
import time
from typing import Tuple, Optional

class TCPClient:
    
    def __init__(self):
        self.socket: Optional[socket.socket] = None
        self.address_info = None
        self.connected = False

    def init(self, connection_address: str, port_number: int) -> int:

        try:

            self.address_info = socket.getaddrinfo(connection_address, port_number, 
                                                 socket.AF_UNSPEC, socket.SOCK_STREAM)
            if not self.address_info:
                return -1
                
            family, socktype, proto, _, addr = self.address_info[0]
            self.socket = socket.socket(family, socktype, proto)
            if not self.socket:
                return -2
                
            return 0
            
        except socket.gaierror:
            return -1
        except socket.error:
            return -2

    def set_socket_nonblocking(self):

        if self.socket:
            self.socket.setblocking(False)

    def connect_to_server(self) -> int:

        if not self.socket or not self.address_info:
            return -1

        try:

            self.socket.settimeout(0.5) 
            _, _, _, _, addr = self.address_info[0]
            self.socket.connect(addr)
            self.connected = True
            return 0
            
        except (socket.timeout, socket.error):
            return -1

    def check_connection(self) -> int:

        if not self.socket or not self.connected:
            return -1

        try:
          
            data = self.socket.recv(1, socket.MSG_PEEK | socket.MSG_DONTWAIT)
            if len(data) == 0: 
                self.connected = False
                return -1
            return 0
        except socket.error:
            return -1

    def send_data_to_server(self, data: bytes) -> int:

        if not self.socket or not self.connected:
            return -1

        try:
            self.socket.sendall(data)
            return 0
        except socket.error:
            return -1

    def check_input_buffer(self) -> int:

        if not self.socket or not self.connected:
            return -1

        try:
            readable, _, _ = select.select([self.socket], [], [], 0)
            return 1 if readable else 0
        except select.error:
            return -1

    def receive_data_from_server(self) -> Tuple[int, bytes, int]:

        if not self.socket or not self.connected:
            return -1, b'', 0

        try:

            data = self.socket.recv(260)
            if not data: 
                return -1, b'', 0
            return 0, data, len(data)
        except socket.error:
            return -1, b'', 0

    def close_connection(self):

        if self.socket:
            try:
                self.socket.close()
            except socket.error:
                pass
            finally:
                self.socket = None
                self.address_info = None
                self.connected = False
