/*
    file: modbus.h
    date: 18.03.2025
    author: Emir
    brief: Modbus Code for Modbus TCP
    description: This module will handle Modbus TCP Packages and Modbus Communication
*/

#ifndef MODBUS_H
#define MODBUS_H

#include "tcp_client.h"

#define MODBUS_RECEIVE_MAX_DATA_SIZE 251
#define MODBUS_WRITE_MULT_REQ_MAX_DATA_SIZE 247

typedef enum e_modbus_functions_t
{
    FUNC_READ_COILS = 0x01,                  
    FUNC_READ_DISCRETE_INPUTS = 0x02,        
    FUNC_READ_HOLDING_REGISTERS = 0x03,
    FUNC_READ_INPUT_REGISTERS = 0x04,
    FUNC_WRITE_SINGLE_COIL = 0x05,
    FUNC_WRITE_SINGLE_REGISTER = 0x06,
    FUNC_WRITE_MULTIPLE_COILS = 0x0F,
    FUNC_WRITE_MULTIPLE_REGISTERS = 0x10
} modbus_functions_t;

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


typedef enum e_write_single_req_value_t
{
    COIL_ON,
    COIL_OFF
}write_single_req_value_t;

typedef enum e_modbus_req_return_val_t
{
    MODBUS_REQ_OK,
    MODBUS_REQ_GENERAL_ERROR,
    MODBUS_REQ_INVALID_FUNCTION,                // Wrong Function Parameter
    MODBUS_REQ_COMMUNICATION_PROBLEM,           // Communication problem
    MODBUS_REQ_WRONG_VALUE,                     // Wrong Value Entered
} modbus_req_return_val_t;

typedef enum e_modbus_respond_return_val_t
{
    MODBUS_RESPONSE_OK,
    MODBUS_RESPONSE_GENERAL_ERROR,
    MODBUS_RESPONSE_COMMUNICATION_PROBLEM,        // Communication problem
    MODBUS_RESPONSE_WRONG_DATA_RETURNED,        // Communication problem
    MODBUS_RESPONSE_NO_ANSWER_YET,                // Server didn't respond yet
    MODBUS_RESPONSE_ILLEGAL_FUNCTION,          // Server responded Wrong Function Code(0x01)
    MODBUS_RESPONSE_ILLEGAL_ADDRESS,              // Server responded Invalid Address(0x02)
} modbus_respond_return_val_t;


typedef enum e_modbus_error_t
{
    MODBUS_ERROR_NONE = 0x00,
    MODBUS_ERROR_FUNCTION_CODE_WRONG = 0x01,
    MODBUS_ERROR_INVALID_ADDRESS = 0x02,
    MODBUS_ERROR_UNKNOWN_ERROR = 0x03,
} modbus_error_t;

/*****************************************************************************/
int connect_to_modbus_server(const char* connection_address);

/*****************************************************************************/
int check_modbus_server_connection(void);

/*****************************************************************************/
modbus_req_return_val_t send_read_req(modbus_functions_t modbus_func,
                                      uint16_t address,
                                      uint16_t length);

/*****************************************************************************/
modbus_req_return_val_t send_write_single_coil_req(uint16_t address,
                                                   write_single_req_value_t value);

/*****************************************************************************/
modbus_req_return_val_t send_write_single_reg_req(uint16_t address,
                                                  uint16_t value);

/*****************************************************************************/
modbus_req_return_val_t send_write_mult_coils_req(modbus_functions_t modbus_func,
                                                  uint16_t start_address,
                                                  uint8_t *data,
                                                  uint16_t reg_count);
/*****************************************************************************/
modbus_respond_return_val_t receive_read_response(uint8_t* data_received, 
                                                  uint8_t* data_length);
/*****************************************************************************/
modbus_respond_return_val_t receive_write_single_coil_response(uint16_t* address,
                                                               write_single_req_value_t* value);
    
/*****************************************************************************/
modbus_respond_return_val_t receive_write_single_reg_response(uint16_t *address,
                                                              uint16_t* value);

/*****************************************************************************/
modbus_respond_return_val_t receive_write_mult_response(uint16_t *address,
                                                        uint16_t *num_of_recorded_regs);

/*****************************************************************************/


#endif