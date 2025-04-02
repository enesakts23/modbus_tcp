/*
    file: tcp_client.h
    date: 12.03.2025
    author: Emir
    brief: Client Code for TCP Communication
    description: This module will handle tcp communication.
*/

#ifndef TCP_CLIENT_H
#define TCP_CLIENT_H

#define _GNU_SOURCE

#include <stdint.h>
#include <netdb.h>
#include <unistd.h>
#include <errno.h>

int get_addr_info(const char* connection_address, struct addrinfo **res);

int create_socket(struct addrinfo* res);

void set_socket_nonblocking(int sockfd);

int check_connection(int sockfd);

int connect_to_server(int sockfd, struct addrinfo* res);

int send_data_to_server(int sockfd, uint8_t* data_buffer, size_t data_size);

int check_input_buffer(int sockfd);

int receive_data_from_server(int sockfd, uint8_t* data_buffer, ssize_t* data_size);


#endif

