"""
TCP Client implementation for Modbus TCP communication
Author: AI Assistant (based on original C implementation by Emir)
"""

import socket
import select
import time
from typing import Tuple, Optional

class TCPClient:
    def __init__(self):
        """Initialize TCP client instance"""
        self.socket: Optional[socket.socket] = None
        self.address_info = None
        self.connected = False

    def init(self, connection_address: str, port_number: int) -> int:
        """
        Initialize TCP client with connection parameters
        
        Args:
            connection_address: Server address (IP or hostname)
            port_number: Server port number
            
        Returns:
            0 on success, -1 on getaddrinfo error, -2 on socket creation error
        """
        try:
            # Get address info
            self.address_info = socket.getaddrinfo(connection_address, port_number, 
                                                 socket.AF_UNSPEC, socket.SOCK_STREAM)
            if not self.address_info:
                return -1
                
            # Create socket
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
        """Configure socket as non-blocking"""
        if self.socket:
            self.socket.setblocking(False)

    def connect_to_server(self) -> int:
        """
        Connect to the server with timeout
        
        Returns:
            0 on success, -1 on failure
        """
        if not self.socket or not self.address_info:
            return -1

        try:
            # Set socket timeout
            self.socket.settimeout(0.5)  # 500ms timeout
            
            # Try to connect
            _, _, _, _, addr = self.address_info[0]
            self.socket.connect(addr)
            self.connected = True
            return 0
            
        except (socket.timeout, socket.error):
            return -1

    def check_connection(self) -> int:
        """
        Check if connection is still alive
        
        Returns:
            0 if connected, -1 if connection lost
        """
        if not self.socket or not self.connected:
            return -1

        try:
            # Try to peek at the socket
            data = self.socket.recv(1, socket.MSG_PEEK | socket.MSG_DONTWAIT)
            if len(data) == 0:  # Connection closed by peer
                self.connected = False
                return -1
            return 0
        except socket.error:
            return -1

    def send_data_to_server(self, data: bytes) -> int:
        """
        Send data to server
        
        Args:
            data: Bytes to send
            
        Returns:
            0 on success, -1 on error
        """
        if not self.socket or not self.connected:
            return -1

        try:
            self.socket.sendall(data)
            return 0
        except socket.error:
            return -1

    def check_input_buffer(self) -> int:
        """
        Check if data is available to read
        
        Returns:
            Positive value if data available, 0 if no data, -1 on error
        """
        if not self.socket or not self.connected:
            return -1

        try:
            readable, _, _ = select.select([self.socket], [], [], 0)
            return 1 if readable else 0
        except select.error:
            return -1

    def receive_data_from_server(self) -> Tuple[int, bytes, int]:
        """
        Receive data from server
        
        Returns:
            Tuple of (status, data, size)
            status: 0 on success, -1 on error
            data: received bytes
            size: number of bytes received
        """
        if not self.socket or not self.connected:
            return -1, b'', 0

        try:
            # Maximum buffer size for Modbus TCP (260 bytes)
            data = self.socket.recv(260)
            if not data:  # Connection closed
                return -1, b'', 0
            return 0, data, len(data)
        except socket.error:
            return -1, b'', 0

    def close_connection(self):
        """Close connection and cleanup resources"""
        if self.socket:
            try:
                self.socket.close()
            except socket.error:
                pass
            finally:
                self.socket = None
                self.address_info = None
                self.connected = False
