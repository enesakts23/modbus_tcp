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

/*****************************************************************************/
/**
 * @brief Get AddrInfo from System to use later with socket
 * @param[in] connection_address [const char*] string for connection address
 * can be localhost or ip address like "127.0.0.1"
 * @param[out] res [struct addrinfo **] result that will be used with
 * socket
 * @return [int] returns 0 if no error occured.
 */
int get_addr_info(const char* connection_address, struct addrinfo **res);

/*****************************************************************************/
/**
 * @brief Creates Socket with given config(with res param)
 * @param[in] res [struct addrinfo *]
 * @return [int] if any error occured it returns -1. 
 * Otherwise any positive value means socket file descriptor.
 */
int create_socket(struct addrinfo* res);

/*****************************************************************************/
/**
 * @brief Creates Socket with given config(with res param)
 * @details we are configuring socket as non-blocking with this function. We
 * don't want poll to be stucked at no input.
 * @param[in] sockfd [int] socket file descriptor which will be manipulated.
 * @return [void] 
 */
void set_socket_nonblocking(int sockfd);

/*****************************************************************************/
/**
 * @brief Connects to the server which is given with res
 * @details Tries to connect until 500ms.
 * @param[in] sockfd [int] socket file descriptor of socket which is going to
 * connect to server.
 * @param[in] res [struct addrinfo*] struct that keeps settings of server.
 * @return [int] returns 0 if connection is succesfull, otherwise returns -1
 */
int connect_to_server(int sockfd, struct addrinfo* res);

/*****************************************************************************/
/**
 * @brief Checks if connection is still stable or not
 * @details Checks with recv function of berkeley sockets if recv returns with
 * 0 it means connection is lost. it doesn't pop data with recv function. So
 * if any data was in buffer it'll stay there.
 * @param[in] sockfd [int] socket file descriptor of socket which is connected
 * to a server.
 * @return [int] if connection is lost it returns -1, Otherwise it returns 0
 */
int check_connection(int sockfd);

/*****************************************************************************/
/**
 * @brief Sends data via given sockfd at the given size
 * @details 
 * @param[in] sockfd [int] socket file descriptor of socket which contains
 * connection settings.
 * @param[in] data_buffer [uint8_t *] buffer that contains data to be sent.
 * @param[in] data_size [size_t] data length of data to be sent.
 * @return [int] returns 0 if no error occured. otherwise return -1. Doesn't
 * give info about how many data has been sent.
 */
int send_data_to_server(int sockfd, uint8_t* data_buffer, size_t data_size);

/*****************************************************************************/
/**
 * @brief Checks if any data arrived or not
 * @details 
 * @param[in] sockfd [int] socket file descriptor of socket which contains
 * connection settings.
 * @return [int] returns positive value on data in buffer. Returns 0 if no
 * data in receive buffer. Returns -1 on any error.
 */
int check_input_buffer(int sockfd);

/*****************************************************************************/
/**
 * @brief Receives data from server at given sockfd
 * @details it returns at size of maximum 260 bytes for using with modbus tcp.
 * @param[in] sockfd [int] socket file descriptor of socket which contains
 * connection settings.
 * @param[out] data_buffer [uint8_t *] data buffer which data from the server
 * will be put into. 
 * @param[out] data_size [ssize_t *] data size of read data. 
 * @return [int] returns -1 if connection is closed or any other error occured.
 * returns 0 on any data received successfully.
 */
int receive_data_from_server(int sockfd, uint8_t* data_buffer, ssize_t* data_size);

/*****************************************************************************/

#endif

