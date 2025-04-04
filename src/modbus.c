/*
    file: modbus.c
    date: 18.03.2025
    author: Emir
    brief: Modbus Code for Modbus TCP
    description: This module will handle Modbus TCP Packages and Modbus 
    Communication
*/

#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "modbus.h"

typedef struct __attribute__((packed)) st_read_req_package_t
{
    uint8_t transaction_identifier_h;
    uint8_t transaction_identifier_l;
    uint8_t protocol_identifier_h;
    uint8_t protocol_identifier_l;
    uint8_t message_length_h;
    uint8_t message_length_l;
    uint8_t device_address;
    uint8_t function_code;
    uint8_t address_high;
    uint8_t address_low;
    uint8_t number_of_regs_high;
    uint8_t number_of_regs_low;
} read_req_package_t;

typedef struct __attribute__((packed)) st_write_single_req_package_t
{
    uint8_t transaction_identifier_h;
    uint8_t transaction_identifier_l;
    uint8_t protocol_identifier_h;
    uint8_t protocol_identifier_l;
    uint8_t message_length_h;
    uint8_t message_length_l;
    uint8_t device_address;
    uint8_t function_code;
    uint8_t address_high;
    uint8_t address_low;
    uint8_t byte_meaning_high;
    uint8_t byte_meaning_low;
} write_single_req_package_t;

typedef struct __attribute__((packed)) st_write_mult_req_package_t
{
    uint8_t transaction_identifier_h;
    uint8_t transaction_identifier_l;
    uint8_t protocol_identifier_h;
    uint8_t protocol_identifier_l;
    uint8_t message_length_h;
    uint8_t message_length_l;
    uint8_t device_address;
    uint8_t function_code;
    uint8_t address_high;
    uint8_t address_low;
    uint8_t number_of_regs_high;
    uint8_t number_of_regs_low;
    uint8_t number_of_bytes_more;
    // uint8_t* data_buffer;           // 247 Byte
} write_mult_req_package_t;

typedef struct __attribute__((packed)) st_read_resp_package_t
{
    uint8_t transaction_identifier_h;
    uint8_t transaction_identifier_l;
    uint8_t protocol_identifier_h;
    uint8_t protocol_identifier_l;
    uint8_t message_length_h;
    uint8_t message_length_l;
    uint8_t device_address;
    uint8_t function_code;
    uint8_t num_of_bytes_more;
    uint8_t* data_buffer;           // 251 Byte
} read_resp_package_t;

// This one is same with the req package
typedef struct __attribute__((packed)) st_write_single_resp_package_t
{
    uint8_t transaction_identifier_h;
    uint8_t transaction_identifier_l;
    uint8_t protocol_identifier_h;
    uint8_t protocol_identifier_l;
    uint8_t message_length_h;
    uint8_t message_length_l;
    uint8_t device_address;
    uint8_t function_code;
    uint8_t address_high;
    uint8_t address_low;
    uint8_t byte_meaning_high;
    uint8_t byte_meaning_low;
} write_single_resp_package_t;

typedef struct __attribute__((packed)) st_write_mult_resp_package_t
{
    uint8_t transaction_identifier_h;
    uint8_t transaction_identifier_l;
    uint8_t protocol_identifier_h;
    uint8_t protocol_identifier_l;
    uint8_t message_length_h;
    uint8_t message_length_l;
    uint8_t device_address;
    uint8_t function_code;
    uint8_t address_high;
    uint8_t address_low;
    uint8_t number_of_recorded_reg_high;
    uint8_t number_of_recorded_reg_low;
} write_mult_resp_package_t;

/* Maximum Package Size of Modbus */
#define MODBUS_PACKAGE_MAX_SIZE 260
/* Corresponding bit means error on modbus tcp */
#define MODBUS_ERROR_BIT_VALUE 0x80

/* Used to fill read request package at beginning*/
/* Transaction ID Must be changed with every request. Will be applied later. */
#define READ_REQ_PACKAGE_DEFAULT (read_req_package_t){                  \
    0x01,                                                               \
    0x02,                                                               \
    0x00,                                                               \
    0x00,                                                               \
    0x00,                                                               \
    0x06,                                                               \
    0x01,                                                               \
    0,                                                                  \
    0,                                                                  \
    0,                                                                  \
    0,                                                                  \
0                                                                       \
}

#define WRITE_SINGLE_REQ_PACKAGE_DEFAULT (write_single_req_package_t){  \
    0x01,                                                               \
    0x02,                                                               \
    0x00,                                                               \
    0x00,                                                               \
    0x00,                                                               \
    0x06,                                                               \
    0x01,                                                               \
    0,                                                                  \
    0,                                                                  \
    0,                                                                  \
    0,                                                                  \
    0                                                                   \
}

#define WRITE_MULT_REQ_PACKAGE_DEFAULT  (write_mult_req_package_t) {    \
    0x01,                                                               \
    0x02,                                                               \
    0x00,                                                               \
    0x00,                                                               \
    0x00,                                                               \
    0x00,                                                               \
    0x01,                                                               \
    0,                                                                  \
    0,                                                                  \
    0,                                                                  \
    0,                                                                  \
    0,                                                                  \
    0,                                                                  \
    /* NULL */                                                          \
    }

/*****************************************************************************/

/**
 * @brief Checks if any error returned at response from modbus server
 * @details Can only detect illegal address or illegal function. All other
 * errors are not identified and returned as general error.
 * @param[in] modbus_buffer [uint8_t *] data array which is holding the received
 * data from tcp.
 * @return [modbus_response_return_val_t] returns MODBUS_RESPONSE_OK in no 
 * error situation. Can return illegal address or illegal function. Other
 * errors will be returned as MODBUS_RESPONSE_GENERAL_ERROR.
 */
static modbus_response_return_val_t check_error(uint8_t * modbus_buffer);
/*****************************************************************************/
/**
 * @brief Parses given data into a read_resp_package_t structure which is used
 * in this module to parse received data from modbus.
 * @details it parses data to a structure named read_response_package which is 
 * type of read_resp_package_t. Then that structure is used to return received
 * values.
 * @param[in] data [uint8_t *] data array which is holding the received data
 * from tcp.
 * @return [void]
 */
static void parse_read_data(uint8_t *data);

/*****************************************************************************/
/**
 * @brief Parses response of write single functions like write sinlge coil and
 * write single register into a write_single_resp_package_t structure.
 * @details it parses data to a structure named write_single_response_package
 * which is type of write_single_resp_package_t. Then that structure is used to
 * return received values.
 * @param[in] data [uint8_t *] data array which is holding the received data
 * from tcp.
 * @return [void]
 */
static void parse_write_single_response(uint8_t *data);

/*****************************************************************************/
/**
 * @brief Parses given data into a write_mult_resp_package_t structure which is
 * used in this module to parse received data from modbus.
 * @details it parses data to a structure named write_mult_response_package 
 * which is type of write_mult_resp_package_t. Then that structure is used to
 * return received values.
 * @param[in] data [uint8_t *] data array which is holding the received data
 * from tcp.
 * @return [void]
 */
static void parse_write_mult_response(uint8_t *data);

/*****************************************************************************/
/**
 * @brief it parses and returns error type as modbus_error_t from given data
 * @details error check of data must be done before using this function. This
 * function doesn't check if any error occured or not. 
 * @param[in] data [uint8_t *] data array which is holding the received data
 * from modbus tcp and has the error type in it.
 * @return [modbus_error_t] it returns error type but doesn't provide every type
 * of modbus error for now. it only indicates if error is function code wrong or
 * invalid address. Otherwise it only returns it as unknown error. And if the
 * error check is made carefully it can't return MODBUS_ERROR_NONE.
 */
static modbus_error_t parse_error(uint8_t *data);

/*****************************************************************************/
/* This function will be deleted later. Used for debugging purpose. */
static void print_sent_package(uint8_t *package, uint8_t package_size);

/*****************************************************************************/

/* Package Variables */
static read_resp_package_t read_response_package;
static write_single_resp_package_t write_single_response_package;
static write_mult_resp_package_t write_mult_response_package;

/* Buffer to use with TCP/IP */
static uint8_t modbus_buffer[MODBUS_PACKAGE_MAX_SIZE];

/* TCP/IP communication variables*/
static struct addrinfo *res;
static int sfd;

/* Function Definitions */
/*****************************************************************************/
int connect_to_modbus_server(const char *connection_address)
{
    int error_holder;

    error_holder = get_addr_info(connection_address, &res);

    if ((error_holder) == 0)
    {
        printf("Getted Addr Info\n");
    }
    else
    {
        fprintf(stderr, "getaddrinfo: %s\n", gai_strerror(error_holder));
        return -1;
    }

    sfd = create_socket(res);

    if (sfd == -1)
    {
        freeaddrinfo(res);
        return -1;
    }

    set_socket_nonblocking(sfd);

    if (connect_to_server(sfd, res) != 0)
    {
        printf("Can't connect to server\n");
        close_connection();
        return -1;
    }

    return 0;
}

/*****************************************************************************/
int check_modbus_server_connection(void)
{
    if (check_connection(sfd) == -1)
    {
        close_connection();
        return -1;
    }

    return 0;
}

/*****************************************************************************/
modbus_req_return_val_t send_read_req(modbus_functions_t modbus_func,
                                      uint16_t address,
                                      uint16_t length)
{
    read_req_package_t read_req_pack = READ_REQ_PACKAGE_DEFAULT;

    if (
        (modbus_func != FUNC_READ_COILS) &&
        (modbus_func != FUNC_READ_DISCRETE_INPUTS) &&
        (modbus_func != FUNC_READ_HOLDING_REGISTERS) &&
        (modbus_func != FUNC_READ_INPUT_REGISTERS))
    {
        return MODBUS_REQ_INVALID_FUNCTION;
    }

    read_req_pack.function_code = (uint8_t)modbus_func;
    read_req_pack.address_high = (uint8_t)((address & (uint16_t)0xFF00) >> 8);
    read_req_pack.address_low = (uint8_t)(address & 0x00FF);
    read_req_pack.number_of_regs_high = 0x00;
    read_req_pack.number_of_regs_low = (uint8_t)length;

    print_sent_package((uint8_t *)&read_req_pack, (uint8_t) sizeof(read_req_package_t));

    if (send_data_to_server(sfd, (uint8_t *)&read_req_pack, sizeof(read_req_package_t)) == -1)
    {
        close_connection();
        return MODBUS_REQ_COMMUNICATION_PROBLEM;
    }

    return MODBUS_REQ_OK;
}

/*****************************************************************************/
modbus_req_return_val_t send_write_single_coil_req(uint16_t address,
                                                   write_single_req_value_t value)
{
    write_single_req_package_t write_req_pack = WRITE_SINGLE_REQ_PACKAGE_DEFAULT;

    // otherwise it'll stay as 0x00 and that means OFF
    if (value == COIL_ON)
    {
        write_req_pack.byte_meaning_high = 0xFF;
    }
    else if (value != COIL_OFF)
    {
        return MODBUS_REQ_WRONG_VALUE;
    }

    write_req_pack.function_code = (uint8_t)FUNC_WRITE_SINGLE_COIL;
    write_req_pack.address_high = (uint8_t)((address & (uint16_t)0xFF00) >> 8);
    write_req_pack.address_low = (uint8_t)(address & 0x00FF);

    print_sent_package((uint8_t *)&write_req_pack, (uint8_t) sizeof(write_single_req_package_t));

    if (send_data_to_server(sfd, (uint8_t *)&write_req_pack, sizeof(write_single_req_package_t)) == -1)
    {
        close_connection();
        return MODBUS_REQ_COMMUNICATION_PROBLEM;
    }

    return MODBUS_REQ_OK;
}

/*****************************************************************************/
modbus_req_return_val_t send_write_single_reg_req(uint16_t address,
                                                  uint16_t value)
{
    write_single_req_package_t write_req_pack = WRITE_SINGLE_REQ_PACKAGE_DEFAULT;

    write_req_pack.function_code = (uint8_t)FUNC_WRITE_SINGLE_REGISTER;
    write_req_pack.address_high = (uint8_t)((address & (uint16_t)0xFF00) >> 8);
    write_req_pack.address_low = (uint8_t)(address & 0x00FF);
    write_req_pack.byte_meaning_high = (uint8_t)((value & (uint16_t)0xFF00) >> 8);
    write_req_pack.byte_meaning_low = (uint8_t)(value & 0x00FF);

    print_sent_package((uint8_t *)&write_req_pack, (uint8_t) sizeof(write_single_req_package_t));

    if (send_data_to_server(sfd, (uint8_t *)&write_req_pack, sizeof(read_req_package_t)) == -1)
    {
        close_connection();
        return MODBUS_REQ_COMMUNICATION_PROBLEM;
    }

    return MODBUS_REQ_OK;
}

/*****************************************************************************/
modbus_req_return_val_t send_write_mult_req(modbus_functions_t modbus_func,
                                            uint16_t start_address,
                                            uint8_t *data,
                                            uint16_t reg_count)
{
    write_mult_req_package_t write_mult_req_pack = WRITE_MULT_REQ_PACKAGE_DEFAULT;

    if (
        (modbus_func != FUNC_WRITE_MULTIPLE_COILS) &&
        (modbus_func != FUNC_WRITE_MULTIPLE_REGISTERS) 
    )
    {
        return MODBUS_REQ_INVALID_FUNCTION;
    }

    write_mult_req_pack.function_code = (uint8_t)modbus_func;
    write_mult_req_pack.address_high = (uint8_t)((start_address & (uint16_t)0xFF00) >> 8);
    write_mult_req_pack.address_low = (uint8_t)(start_address & 0x00FF);
    write_mult_req_pack.number_of_regs_high = (uint8_t)((reg_count & (uint16_t)0xFF00) >> 8);
    write_mult_req_pack.number_of_regs_low = (uint8_t)(reg_count & 0x00FF);

    if(modbus_func == FUNC_WRITE_MULTIPLE_COILS)
    {
        write_mult_req_pack.number_of_bytes_more = (uint8_t)(reg_count / 8);
    
        if ((reg_count % 8) != 0)
        {
            write_mult_req_pack.number_of_bytes_more++;
        }
    }
    else
    {
        write_mult_req_pack.number_of_bytes_more = (uint8_t)(reg_count * 2);
    }

    write_mult_req_pack.message_length_l = 7 + write_mult_req_pack.number_of_bytes_more; // 247 + 7 = 255 so it can't exceed 1 byte

    memcpy(modbus_buffer, &write_mult_req_pack, sizeof(write_mult_req_package_t));
    memcpy((modbus_buffer +  sizeof(write_mult_req_package_t)), data, (size_t)write_mult_req_pack.number_of_bytes_more);

    print_sent_package((uint8_t *)modbus_buffer, (uint8_t)(sizeof(write_mult_req_package_t) + (size_t)write_mult_req_pack.number_of_bytes_more)); // Will be deleted
    
    if (send_data_to_server(sfd, (uint8_t *)&modbus_buffer, (sizeof(write_mult_req_package_t) + (size_t)write_mult_req_pack.number_of_bytes_more)) == -1)
    {
        close_connection();
        return MODBUS_REQ_COMMUNICATION_PROBLEM;
    }

    return MODBUS_REQ_OK;
}

/*****************************************************************************/
modbus_response_return_val_t receive_read_response(uint8_t *data_received,
                                                   uint8_t *data_length)
{
    int poll_res;
    ssize_t recv_size;
    modbus_response_return_val_t modbus_response_error;

    // if 0 it can be still waiting but it should answer(in modbus tcp)
    if ((poll_res = check_input_buffer(sfd)) > 0)
    {
        if (receive_data_from_server(sfd, modbus_buffer, &recv_size) == 0)
        {
            if((modbus_response_error = check_error(modbus_buffer)) != MODBUS_RESPONSE_OK)
            {
                return modbus_response_error;
            }

            read_response_package.data_buffer = data_received;
            parse_read_data(modbus_buffer);
            *data_length = read_response_package.num_of_bytes_more;

            return MODBUS_RESPONSE_OK;
        }
    }
    else if (poll_res == 0)
    {
        printf("No Answer From Modbus Server\n");
        return MODBUS_RESPONSE_NO_ANSWER_YET; // No Answer Yet.
    }
    else
    {
        close_connection();
        return MODBUS_RESPONSE_COMMUNICATION_PROBLEM;
    }

    return 0;
}

/*****************************************************************************/
modbus_response_return_val_t receive_write_single_coil_response(uint16_t *address,
                                                                write_single_req_value_t *value)
{
    int poll_res;
    ssize_t recv_size;
    modbus_response_return_val_t modbus_response_error;

    // if 0 it can be still waiting but it should answer(in modbus tcp)
    if ((poll_res = check_input_buffer(sfd)) > 0)
    {
        if (receive_data_from_server(sfd, modbus_buffer, &recv_size) == 0)
        {
            if((modbus_response_error = check_error(modbus_buffer)) != MODBUS_RESPONSE_OK)
            {
                return modbus_response_error;
            }

            parse_write_single_response(modbus_buffer);
            /* We are returning value of returned package, so we can check if
               it is written right or not in application.
               high is 0xFF and low is 0x00 for COIL_ON 0x00 0x00 for COIL OFF */
            if (write_single_response_package.byte_meaning_low == 0x00)
            {
                if (write_single_response_package.byte_meaning_high == 0x00)
                {
                    *value = COIL_OFF;
                }
                else if (write_single_response_package.byte_meaning_high == 0xFF)
                {
                    *value = COIL_ON;
                }
                else
                {
                    return MODBUS_RESPONSE_WRONG_DATA_RETURNED;
                }
            }
            else
            {
                return MODBUS_RESPONSE_WRONG_DATA_RETURNED;
            }

            /* We are returning address returned so we can know if it's address is
               right or not in the application*/
            *address = (((uint16_t)write_single_response_package.address_high) << 8) + ((uint16_t)write_single_response_package.address_low);

            return MODBUS_RESPONSE_OK;
        }
    }
    else if (poll_res == 0) // No Answer received
    {
        printf("No Answer From Modbus Server\n");
        return MODBUS_RESPONSE_NO_ANSWER_YET; // No Answer Yet.
    }
    else // means poll_res < 0 and that means communication error.
    {
        close_connection();
        return MODBUS_RESPONSE_COMMUNICATION_PROBLEM;
    }

    return MODBUS_RESPONSE_OK;
}

/*****************************************************************************/
modbus_response_return_val_t receive_write_single_reg_response(uint16_t *address,
                                                               uint16_t *value)
{
    int poll_res;
    ssize_t recv_size;
    modbus_response_return_val_t modbus_response_error;

    // if 0 it can be still waiting but it should answer(in modbus tcp)
    if ((poll_res = check_input_buffer(sfd)) < 0)
    {
        close_connection();
        return MODBUS_RESPONSE_COMMUNICATION_PROBLEM;
    }
    else if (poll_res == 0) // No Answer received
    {
        printf("No Answer From Modbus Server\n");
        return MODBUS_RESPONSE_NO_ANSWER_YET; // No Answer Yet.
    }

    if (receive_data_from_server(sfd, modbus_buffer, &recv_size) == -1)
    {
        close_connection();
    }

    if((modbus_response_error = check_error(modbus_buffer)) != MODBUS_RESPONSE_OK)
    {
        return modbus_response_error;
    }

    parse_write_single_response(modbus_buffer);
    /* We are returning value of returned package, so we can check if it is writtem
    right or not in application */
    *value = (((uint16_t)write_single_response_package.byte_meaning_high) << 8) + ((uint16_t)write_single_response_package.byte_meaning_low);
    /* We are returning address returned so we can if it's address is
    right or not in the application*/
    *address = (((uint16_t)write_single_response_package.address_high) << 8) + ((uint16_t)write_single_response_package.address_low);

    return MODBUS_RESPONSE_OK;
}

/*****************************************************************************/
modbus_response_return_val_t receive_write_mult_response(uint16_t *address,
                                                         uint16_t *num_of_recorded_regs)
{
    int poll_res;
    ssize_t recv_size;
    modbus_response_return_val_t modbus_response_error;

    // if 0 it can be still waiting but it should answer(in modbus tcp)
    if ((poll_res = check_input_buffer(sfd)) < 0)
    {
        close_connection();
        return MODBUS_RESPONSE_COMMUNICATION_PROBLEM;
    }
    else if (poll_res == 0) // No Answer received
    {
        printf("No Answer From Modbus Server\n");
        return MODBUS_RESPONSE_NO_ANSWER_YET; // No Answer Yet.
    }

    if (receive_data_from_server(sfd, modbus_buffer, &recv_size) == -1)
    {
        close_connection();
    }

    if((modbus_response_error = check_error(modbus_buffer)) != MODBUS_RESPONSE_OK)
    {
        return modbus_response_error;
    }

    parse_write_mult_response(modbus_buffer);
    /* We are returning the number of recorded regs. */
    *num_of_recorded_regs = (((uint16_t)write_mult_response_package.number_of_recorded_reg_high) << 8) + ((uint16_t)write_mult_response_package.number_of_recorded_reg_low);
    /* We are returning address returned so we can if it's address is
    right or not in the application*/
    *address = (((uint16_t)write_mult_response_package.address_high) << 8) + ((uint16_t)write_mult_response_package.address_low);

    return MODBUS_RESPONSE_OK;
}

/*****************************************************************************/
void close_connection(void)
{
    freeaddrinfo(res);
    close(sfd);
}

/*****************************************************************************/
static modbus_response_return_val_t check_error(uint8_t * modbus_buffer)
{
    modbus_response_return_val_t modbus_response_return = MODBUS_RESPONSE_OK;
    modbus_error_t modbus_error;

    if ((modbus_buffer[7] & MODBUS_ERROR_BIT_VALUE))
    {
        modbus_error = parse_error(modbus_buffer);
        if (modbus_error == MODBUS_ERROR_INVALID_ADDRESS)
        {
            modbus_response_return = MODBUS_RESPONSE_ILLEGAL_ADDRESS; // Invalid Address Error
        }
        else if (modbus_error == MODBUS_ERROR_FUNCTION_CODE_WRONG)
        {
            printf("Wrong Function Code\n");
            modbus_response_return = MODBUS_RESPONSE_ILLEGAL_FUNCTION;
        }
        else
        {
            modbus_response_return = MODBUS_RESPONSE_GENERAL_ERROR; // We don't identify other errors
        }
    }

    return modbus_response_return;
}
/*****************************************************************************/
static void parse_read_data(uint8_t *data)
{
    // 8 is the address of "number of bytes" so we copy 9 bytes.
    memcpy(&read_response_package, data, 9);
    memcpy(read_response_package.data_buffer, (data + 9), read_response_package.num_of_bytes_more);
}

/*****************************************************************************/
static void parse_write_single_response(uint8_t *data)
{
    memcpy(&write_single_response_package, data, sizeof(write_single_resp_package_t));
}

/*****************************************************************************/
static void parse_write_mult_response(uint8_t *data)
{
    memcpy(&write_mult_response_package, data, sizeof(write_mult_resp_package_t));
}

/*****************************************************************************/
static modbus_error_t parse_error(uint8_t *data)
{
    uint8_t error_val = data[8];

    if (error_val >= (uint8_t)MODBUS_ERROR_UNKNOWN_ERROR)
    {
        error_val = (uint8_t)MODBUS_ERROR_UNKNOWN_ERROR;
    }

    return (modbus_error_t)error_val;
}

/*****************************************************************************/
static void print_sent_package(uint8_t *package, uint8_t package_size)
{
    // Print Data Sent for Debug
    for (uint8_t i = 0; i < package_size; i++)
    {
        printf("Data %d = 0x%.2x\n", i, package[i]);
    }
}

/*****************************************************************************/