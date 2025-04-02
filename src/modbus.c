/*
    file: modbus.c
    date: 18.03.2025
    author: Emir
    brief: Modbus Code for Modbus TCP
    description: This module will handle Modbus TCP Packages and Modbus Communication
*/

#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "modbus.h"

/*****************************************************************************/
static void parse_read_data(uint8_t *data);

/*****************************************************************************/
static void parse_write_single_response(uint8_t *data);

/*****************************************************************************/
static void parse_write_mult_response(uint8_t *data);

/*****************************************************************************/
static modbus_error_t parse_error(uint8_t *data);

/*****************************************************************************/
static void print_sent_package(uint8_t *package, uint8_t package_size);

/*****************************************************************************/

#define MODBUS_PACKAGE_MAX_SIZE 260

#define MODBUS_ERROR_BIT_VALUE 0x80

/* Used to fill read request package at beginning*/
/* Transaction ID Must be changed with every request. Will be applied later. */
#define READ_REQ_PACKAGE_DEFAULT (read_req_package_t){ \
    0x01,                                              \
    0x02,                                              \
    0x00,                                              \
    0x00,                                              \
    0x00,                                              \
    0x06,                                              \
    0x01,                                              \
    0,                                                 \
    0,                                                 \
    0,                                                 \
    0,                                                 \
    0}

#define WRITE_SINGLE_REQ_PACKAGE_DEFAULT (write_single_req_package_t){ \
    0x01,                                                              \
    0x02,                                                              \
    0x00,                                                              \
    0x00,                                                              \
    0x00,                                                              \
    0x06,                                                              \
    0x01,                                                              \
    0,                                                                 \
    0,                                                                 \
    0,                                                                 \
    0,                                                                 \
    0}

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

read_resp_package_t read_response_package;
write_single_resp_package_t write_single_response_package;
write_mult_resp_package_t write_mult_response_package;

uint8_t modbus_buffer[MODBUS_PACKAGE_MAX_SIZE];

struct addrinfo *res;
int sfd;

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
        freeaddrinfo(res);
        close(sfd);
        return -1;
    }

    return 0;
}

/*****************************************************************************/
int check_modbus_server_connection(void)
{
    if (check_connection(sfd) == -1)
    {
        freeaddrinfo(res);
        close(sfd);
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
        freeaddrinfo(res);
        close(sfd);
        return MODBUS_REQ_COMMUNICATION_PROBLEM;
    }

    return MODBUS_REQ_OK;
}

/*****************************************************************************/
/* Writes to single coil */
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
        freeaddrinfo(res);
        close(sfd);
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
        freeaddrinfo(res);
        close(sfd);
        return MODBUS_REQ_COMMUNICATION_PROBLEM;
    }

    return MODBUS_REQ_OK;
}

/*****************************************************************************/
modbus_req_return_val_t send_write_mult_coils_req(modbus_functions_t modbus_func,
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
        freeaddrinfo(res);
        close(sfd);
        return MODBUS_REQ_COMMUNICATION_PROBLEM;
    }

    return MODBUS_REQ_OK;
}

/*****************************************************************************/
modbus_respond_return_val_t receive_read_response(uint8_t *data_received,
                                                  uint8_t *data_length)
{
    int poll_res;
    ssize_t recv_size;
    modbus_error_t error;

    // if 0 it can be still waiting but it should answer(in modbus tcp)
    if ((poll_res = check_input_buffer(sfd)) > 0)
    {
        if (receive_data_from_server(sfd, modbus_buffer, &recv_size) == 0)
        {
            if ((modbus_buffer[7] & MODBUS_ERROR_BIT_VALUE))
            {
                error = parse_error(modbus_buffer);
                if (error == MODBUS_ERROR_INVALID_ADDRESS)
                {
                    return MODBUS_RESPONSE_ILLEGAL_ADDRESS; // Invalid Address Error
                }
                else if (error == MODBUS_ERROR_FUNCTION_CODE_WRONG)
                {
                    return MODBUS_RESPONSE_ILLEGAL_FUNCTION;    // Illegal Function Code Sent
                }
                else
                {
                    return MODBUS_RESPONSE_GENERAL_ERROR; // We don't identify other errorss
                }
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
        freeaddrinfo(res);
        close(sfd);
        return MODBUS_RESPONSE_COMMUNICATION_PROBLEM;
    }

    return 0;
}

/*****************************************************************************/
modbus_respond_return_val_t receive_write_single_coil_response(uint16_t *address,
                                                               write_single_req_value_t *value)
{
    int poll_res;
    ssize_t recv_size;
    modbus_error_t error;

    // if 0 it can be still waiting but it should answer(in modbus tcp)
    if ((poll_res = check_input_buffer(sfd)) > 0)
    {
        if (receive_data_from_server(sfd, modbus_buffer, &recv_size) == 0)
        {
            if ((modbus_buffer[7] & MODBUS_ERROR_BIT_VALUE))
            {
                error = parse_error(modbus_buffer);
                if (error == MODBUS_ERROR_INVALID_ADDRESS)
                {
                    return MODBUS_RESPONSE_ILLEGAL_ADDRESS; // Invalid Address Error
                }
                else if (error == MODBUS_ERROR_FUNCTION_CODE_WRONG)
                {
                    printf("Wrong Function Code\n");
                    return MODBUS_RESPONSE_ILLEGAL_FUNCTION;
                }
                else
                {
                    return MODBUS_RESPONSE_GENERAL_ERROR; // We don't identify other errorss
                }
            }

            parse_write_single_response(modbus_buffer);
            /* We are returning value of returned package, so we can check if it is writtem
                right or not in application.
                hight is 0xFF and low is 0x00 for COIL_ON 0x00 0x00 for COIL OFF */
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
        freeaddrinfo(res);
        close(sfd);
        return MODBUS_RESPONSE_COMMUNICATION_PROBLEM;
    }

    return MODBUS_RESPONSE_OK;
}

/*****************************************************************************/
modbus_respond_return_val_t receive_write_single_reg_response(uint16_t *address,
                                                              uint16_t *value)
{
    int poll_res;
    ssize_t recv_size;
    modbus_error_t error;

    // if 0 it can be still waiting but it should answer(in modbus tcp)
    if ((poll_res = check_input_buffer(sfd)) < 0)
    {
        freeaddrinfo(res);
        close(sfd);
        return MODBUS_RESPONSE_COMMUNICATION_PROBLEM;
    }
    else if (poll_res == 0) // No Answer received
    {
        printf("No Answer From Modbus Server\n");
        return MODBUS_RESPONSE_NO_ANSWER_YET; // No Answer Yet.
    }

    if (receive_data_from_server(sfd, modbus_buffer, &recv_size) == -1)
    {
        freeaddrinfo(res);
        close(sfd);
    }

    if ((modbus_buffer[7] & MODBUS_ERROR_BIT_VALUE))
    {
        error = parse_error(modbus_buffer);
        if (error == MODBUS_ERROR_INVALID_ADDRESS)
        {
            return MODBUS_RESPONSE_ILLEGAL_ADDRESS; // Invalid Address Error
        }
        else if (error == MODBUS_ERROR_FUNCTION_CODE_WRONG)
        {
            printf("Wrong Function Code\n");
            return MODBUS_RESPONSE_ILLEGAL_FUNCTION;
        }
        else
        {
            return MODBUS_RESPONSE_GENERAL_ERROR; // We don't identify other errorss
        }
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
modbus_respond_return_val_t receive_write_mult_response(uint16_t *address,
                                                        uint16_t *num_of_recorded_regs)
{
    int poll_res;
    ssize_t recv_size;
    modbus_error_t error;

    // if 0 it can be still waiting but it should answer(in modbus tcp)
    if ((poll_res = check_input_buffer(sfd)) < 0)
    {
        freeaddrinfo(res);
        close(sfd);
        return MODBUS_RESPONSE_COMMUNICATION_PROBLEM;
    }
    else if (poll_res == 0) // No Answer received
    {
        printf("No Answer From Modbus Server\n");
        return MODBUS_RESPONSE_NO_ANSWER_YET; // No Answer Yet.
    }

    if (receive_data_from_server(sfd, modbus_buffer, &recv_size) == -1)
    {
        freeaddrinfo(res);
        close(sfd);
    }

    if ((modbus_buffer[7] & MODBUS_ERROR_BIT_VALUE))
    {
        error = parse_error(modbus_buffer);
        if (error == MODBUS_ERROR_INVALID_ADDRESS)
        {
            return MODBUS_RESPONSE_ILLEGAL_ADDRESS; // Invalid Address Error
        }
        else if (error == MODBUS_ERROR_FUNCTION_CODE_WRONG)
        {
            printf("Wrong Function Code\n");
            return MODBUS_RESPONSE_ILLEGAL_FUNCTION;
        }
        else
        {
            return MODBUS_RESPONSE_GENERAL_ERROR; // We don't identify other errorss
        }
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

static void parse_read_data(uint8_t *data)
{
    // 8 is the address of "number of bytes" so we copy 9 bytes.
    memcpy(&read_response_package, data, 9);

    printf("Byte Count = %d\n", read_response_package.num_of_bytes_more);

    memcpy(read_response_package.data_buffer, (data + 9), read_response_package.num_of_bytes_more);

    print_sent_package(data, 9 + read_response_package.num_of_bytes_more);
}

/*****************************************************************************/
static void parse_write_single_response(uint8_t *data)
{
    memcpy(&write_single_response_package, data, sizeof(write_single_resp_package_t));
    for (int i = 0; i < (int)sizeof(write_single_resp_package_t); i++)
    {
        printf("Data[%d] = 0x%X\n", i, data[i]);
    }
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

    // printf("Data Error is %u\n", data[8]);
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