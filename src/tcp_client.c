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

/* This struct holds data resources used while communication. */
struct st_tcp_client
{
    struct addrinfo *res;
    int sockfd;
};

/*****************************************************************************/
/**
 * @brief Get AddrInfo from System to use later with socket
 * @param[in] connection_address [const char*] string for connection address
 * can be localhost or ip address like "127.0.0.1"
 * @param[in] port_number [const char*] port number string that is going to
 * be used in communication.
 * @param[out] res [struct addrinfo **] result that will be used with
 * socket
 * @return [int] returns 0 if no error occured.
 */
static int get_addr_info(const char *connection_address,
                         const char *port_number,
                         struct addrinfo **res);

/*****************************************************************************/
tcp_client_t *tcp_client_create(void)
{
    tcp_client_t *client = malloc(sizeof(tcp_client_t));
    client->sockfd = -1;

    return client;
}

/*****************************************************************************/
int tcp_client_init(tcp_client_t *client,
                    const char *connection_address,
                    const char *port_number)
{
    int error_holder;

    error_holder = get_addr_info(connection_address, port_number, &(client->res));

    if ((error_holder) != 0)
    {
        fprintf(stderr, "getaddrinfo: %s\n", gai_strerror(error_holder));
        return -1;
    }

    if ((client->sockfd = socket((client->res)->ai_family, (client->res)->ai_socktype, (client->res)->ai_protocol)) == -1)
    {
        printf("Couldn't Create Socket\n");
        freeaddrinfo(client->res);
        return -2; // Socket Creation Error
    }

    return 0;
}

/*****************************************************************************/
void tcp_client_set_socket_nonblocking(tcp_client_t *client)
{
    // Socket'i non-blocking mode'a al
    int flags = fcntl(client->sockfd, F_GETFL, 0);
    if (flags == -1)
    {
        perror("fcntl F_GETFL");
        return;
    }

    if (fcntl(client->sockfd, F_SETFL, flags | O_NONBLOCK) == -1)
    {
        perror("fcntl F_SETFL");
    }
}

/*****************************************************************************/
int tcp_client_connect_to_server(tcp_client_t *client)
{
    struct pollfd pfd;
    int ret;
    int so_error;
    socklen_t len = sizeof(int);

    if (connect(client->sockfd, client->res->ai_addr, client->res->ai_addrlen) == 0)
    {
        printf("Connection is successfull\n");
        return 0;
    }

    if (errno != EINPROGRESS)
    {
        printf("Value of errno: %d\n", errno);
        perror("Error message:");

        return -1;
    }

    pfd.fd = client->sockfd;
    pfd.events = POLLOUT;

    ret = poll(&pfd, 1, 500);
    if (ret == 0)
    {
        // Timeout
        printf("Connection timeout!\n");
        return -1;
    }
    else if (ret < 0)
    {
        perror("poll error");
        return -1;
    }

    getsockopt(client->sockfd, SOL_SOCKET, SO_ERROR, &so_error, &len);
    if (so_error != 0)
    {
        errno = so_error;
        perror("connect failed");
        return -1;
    }

    printf("Connection is successfull\n");

    return 0; // Bağlantı başarılı
}

/*****************************************************************************/
int tcp_client_check_connection(tcp_client_t *client)
{
    char buffer[1];
    // checks if connection is lost or not
    if (recv(client->sockfd, buffer, 1, MSG_PEEK) == 0)
    {
        return -1;
    }

    return 0;
}

/*****************************************************************************/
int tcp_client_send_data_to_server(tcp_client_t *client,
                                   uint8_t *data_buffer,
                                   size_t data_size)
{
    int packet_send;

    if ((packet_send = send(client->sockfd, data_buffer, data_size, 0)) == -1)
    {
        printf("Value of errno: %d\n", errno);
        perror("Error message:");
        return -1;
    }

    return 0;
}

/*****************************************************************************/
int tcp_client_check_input_buffer(tcp_client_t *client)
{
    int ret;
    struct pollfd pfd;
    pfd.fd = client->sockfd;
    pfd.events = POLLIN;

    ret = poll(&pfd, 1, 1000);

    if (ret > 0)
    {
        if (pfd.revents & POLLIN)
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
int tcp_client_receive_data_from_server(tcp_client_t *client,
                                        uint8_t *data_buffer,
                                        ssize_t *data_size)
{
    int packet_recv_count;

    /* 260 is Maximum Size for Modbus TCP Communication*/
    if ((*data_size = recv(client->sockfd, data_buffer, sizeof(uint8_t) * 260, 0)) == -1)
    {

        printf("recv error\n");
        printf("Value of errno: %d\n", errno);
        perror("Error message:");
        return -1;
    }
    else if (*data_size == 0)
    {
        printf("Connection is closed by server\n");
        return -1;
    }

    return 0;
}

/*****************************************************************************/
void tcp_client_close_connection(tcp_client_t *client)
{
    if (client != NULL)
    {
        freeaddrinfo(client->res);
        close(client->sockfd);
        free(client);
    }
}

/*****************************************************************************/
static int get_addr_info(const char *connection_address,
                         const char *port_number,
                         struct addrinfo **res)
{
    struct addrinfo hints;
    int get_addr_err;

    memset(&hints, 0, sizeof(hints));
    hints.ai_family = AF_INET;
    hints.ai_socktype = SOCK_STREAM; // tcp
    hints.ai_flags = AI_NUMERICSERV;

    get_addr_err = getaddrinfo(connection_address, port_number, &hints, res);

    return get_addr_err;
}

/*****************************************************************************/