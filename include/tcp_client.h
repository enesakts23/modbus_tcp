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

typedef struct st_tcp_client tcp_client_t;

/*****************************************************************************/
/**
 * @brief Returns tcp_client_t typed structure that holds data for
 * communication.
 * @details in posix systems. This'll malloc a data point but in other systems
 * that can just return an address from stack.
 * @param[in] client [tcp_client_t*] tcp client data that is going to be used
 * while communicating with tcp server.
 * @return [tcp_client_t*]
 */
tcp_client_t *tcp_client_create(void);

/*****************************************************************************/
/**
 * @brief Returns tcp_client_t typed structure that holds data for
 * communication. This init must be done before any request.
 * @details In posix systems. This'll malloc a data point but in other systems
 * that can just return an address from stack.
 * @param[in] client [tcp_client_t*] tcp client data that is going to be used
 * while communicating with tcp server.
 * @param[in] connection_address [const char*] string for connection address
 * can be localhost or ip address like "127.0.0.1"
 * @param[in] port_number [const char*] port number string that is going to
 * be used in communication.
 * @return [int] returns 0 if no error occured. if it can't get address info 
 * it'll return -1, if it can't create socket it'll return -2. 
 */
int tcp_client_init(tcp_client_t *client,
                    const char *connection_address,
                    const char *port_number);

/*****************************************************************************/
/**
 * @brief Configures communication as non blocking
 * @details we are configuring socket as non-blocking with this function. We
 * don't want poll to be stucked at no input.
 * @param[in] client [tcp_client_t*] tcp client data that is going to be used
 * while communicating with tcp server.
 * @return [void]
 */
void tcp_client_set_socket_nonblocking(tcp_client_t *client);

/*****************************************************************************/
/**
 * @brief Connects to the server which is given with res
 * @details Tries to connect until 500ms.
 * @param[in] client [tcp_client_t*] tcp client data that is going to be used
 * while communicating with tcp server.
 * @return [int] returns 0 if connection is succesfull, otherwise returns -1
 */
int tcp_client_connect_to_server(tcp_client_t *client);

/*****************************************************************************/
/**
 * @brief Checks if connection is still stable or not
 * @details Checks with recv function of berkeley sockets if recv returns with
 * 0 it means connection is lost. it doesn't pop data with recv function. So
 * if any data was in buffer it'll stay there.
 * @param[in] client [tcp_client_t*] tcp client data that is going to be used
 * while communicating with tcp server.
 * @return [int] if connection is lost it returns -1, Otherwise it returns 0
 */
int tcp_client_check_connection(tcp_client_t *client);

/*****************************************************************************/
/**
 * @brief Sends data via given sockfd at the given size
 * @details
 * @param[in] client [tcp_client_t*] tcp client data that is going to be used
 * while communicating with tcp server.
 * @param[in] data_buffer [uint8_t *] buffer that contains data to be sent.
 * @param[in] data_size [size_t] data length of data to be sent.
 * @return [int] returns 0 if no error occured. otherwise return -1. Doesn't
 * give info about how many data has been sent.
 */
int tcp_client_send_data_to_server(tcp_client_t *client,
                                   uint8_t *data_buffer,
                                   size_t data_size);

/*****************************************************************************/
/**
 * @brief Checks if any data arrived or not
 * @details
 * @param[in] client [tcp_client_t*] tcp client data that is going to be used
 * while communicating with tcp server.
 * @return [int] returns positive value on data in buffer. Returns 0 if no
 * data in receive buffer. Returns -1 on any error.
 */
int tcp_client_check_input_buffer(tcp_client_t *client);

/*****************************************************************************/
/**
 * @brief Receives data from server at given sockfd
 * @details it returns at size of maximum 260 bytes for using with modbus tcp.
 * @param[in] client [tcp_client_t*] tcp client data that is going to be used
 * while communicating with tcp server..
 * @param[out] data_buffer [uint8_t *] data buffer which data from the server
 * will be put into.
 * @param[out] data_size [ssize_t *] data size of read data.
 * @return [int] returns -1 if connection is closed or any other error occured.
 * returns 0 on any data received successfully.
 */
int tcp_client_receive_data_from_server(tcp_client_t *client,
                                        uint8_t *data_buffer,
                                        ssize_t *data_size);

/*****************************************************************************/
/**
 * @brief This frees memory used by communication and releases OS sources
 * that's used while communicating. Must be called after communication errors.
 * Must be called for terminating communication.
 * @details Closes connection to modbus server by releasing socket file
 * descriptor and data taken with getaddrinfo and freeing memory allocated for
 * tcp_client_t.
 * @param[in] client [tcp_client_t*] tcp client data that holds data about
 * resources given by os.
 * @return [void]
 */
void tcp_client_close_connection(tcp_client_t *client);

/*****************************************************************************/

#endif
