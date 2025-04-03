/*
    file: tcp_client.c
    date: 12.03.2025
    author: Emir
    brief: Client Code for TCP Communication
    description: This module will handle tcp communication.
*/

#include "tcp_client.h"

#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <unistd.h>
#include <netdb.h>
#include <fcntl.h>
#include <poll.h>
#include <string.h>

#define SERVER_PORT "502"


/*****************************************************************************/
int get_addr_info(const char* connection_address, struct addrinfo **res)
{
    struct addrinfo hints;
    int get_addr_err;

    memset(&hints, 0, sizeof(hints));
    hints.ai_family = AF_INET;
    hints.ai_socktype = SOCK_STREAM;        //tcp 
    hints.ai_flags = AI_NUMERICSERV;
    
    get_addr_err = getaddrinfo(connection_address, SERVER_PORT, &hints, res);
    
    return get_addr_err;
}

/*****************************************************************************/
int create_socket(struct addrinfo* res)
{
    int sockfd;
    
    if((sockfd = socket(res->ai_family, res->ai_socktype, res->ai_protocol)) == -1)
    {
        printf("Error occured\n");
    }
    else{
        printf("Socket created\n");
    }
    
    return sockfd;
}

/*****************************************************************************/
void set_socket_nonblocking(int sockfd) {
    // Socket'i non-blocking mode'a al
    int flags = fcntl(sockfd, F_GETFL, 0);
    if (flags == -1) {
        perror("fcntl F_GETFL");
        return;
    }
    
    if (fcntl(sockfd, F_SETFL, flags | O_NONBLOCK) == -1) {
        perror("fcntl F_SETFL");
    }
}

/*****************************************************************************/
int connect_to_server(int sockfd, struct addrinfo* res)
{   
    struct pollfd pfd;
    int ret;
    int so_error;
    socklen_t len = sizeof(int);

    if(connect(sockfd, res->ai_addr, res->ai_addrlen) == 0)
    {
        printf("Connection is successfull\n");
        return 0;
    }

    if(errno != EINPROGRESS)
    {
        printf("Value of errno: %d\n", errno);
        perror("Error message:");

        return -1;
    }

    pfd.fd = sockfd;
    pfd.events = POLLOUT;

    ret = poll(&pfd, 1, 500);
    if (ret == 0) {
        // Timeout
        printf("Connection timeout!\n");
        return -1;
    } else if (ret < 0) {
        perror("poll error");
        return -1;
    }

    getsockopt(sockfd, SOL_SOCKET, SO_ERROR, &so_error, &len);
    if (so_error != 0) {
        errno = so_error;
        perror("connect failed");
        return -1;
    }

    printf("Connection is successfull\n");
    
    return 0;  // Bağlantı başarılı
}

/*****************************************************************************/
int check_connection(int sockfd)
{
    char buffer[1];
    // checks if connection is lost or not
    if(recv(sockfd, buffer, 1, MSG_PEEK) == 0)
    {
        return -1;
    } 
    
    return 0;
}

/*****************************************************************************/
int send_data_to_server(int sockfd, uint8_t* data_buffer, size_t data_size)
{
    int packet_send;

    if((packet_send = send(sockfd, data_buffer, data_size, 0)) == -1)
    {
        printf("Value of errno: %d\n", errno);
        perror("Error message:");
        return -1;
    }

    return 0;
}

/*****************************************************************************/
int check_input_buffer(int sockfd)
{
    int ret;
    struct pollfd pfd;
    pfd.fd = sockfd;
    pfd.events = POLLIN;

    ret = poll(&pfd, 1, 1000);

    if (ret > 0) 
    {
        if(pfd.revents & POLLIN)
        {
            return ret;
        }
        else
        {
            return 0;
        }
    }

    return ret;
}

/*****************************************************************************/
int receive_data_from_server(int sockfd, uint8_t* data_buffer, ssize_t* data_size)
{
    int packet_recv_count;

    /* 260 is Maximum Size for Modbus TCP Communication*/
    if ((*data_size = recv(sockfd, data_buffer, sizeof(uint8_t) * 260, 0)) == -1)
    {

        printf("recv error\n");
        printf("Value of errno: %d\n", errno);
        perror("Error message:");
        return -1;
    }
    else if(*data_size == 0)
    {
        printf("Connection Closed\n");
        return -1;
    }

    return 0;
}

/*****************************************************************************/

