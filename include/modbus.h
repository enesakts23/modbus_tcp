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

typedef enum e_write_single_coil_value_t
{
    COIL_ON,
    COIL_OFF
} write_single_coil_value_t;

typedef enum e_modbus_req_return_val_t
{
    MODBUS_REQ_OK,
    MODBUS_REQ_GENERAL_ERROR,
    MODBUS_REQ_INVALID_FUNCTION,      // Wrong Function Parameter
    MODBUS_REQ_COMMUNICATION_PROBLEM, // Communication problem
    MODBUS_REQ_WRONG_VALUE,           // Wrong Value Entered
} modbus_req_return_val_t;
  
typedef enum e_modbus_response_return_val_t
{
    MODBUS_RESPONSE_OK,
    MODBUS_RESPONSE_GENERAL_ERROR,
    MODBUS_RESPONSE_COMMUNICATION_PROBLEM, // Communication problem
    MODBUS_RESPONSE_WRONG_DATA_RETURNED,
    MODBUS_RESPONSE_NO_ANSWER_YET,    // Server didn't respond yet
    MODBUS_RESPONSE_ILLEGAL_FUNCTION, // Server responded Wrong Function Code(0x01)
    MODBUS_RESPONSE_ILLEGAL_ADDRESS,  // Server responded Invalid Address(0x02)
} modbus_response_return_val_t;

/*****************************************************************************/
/**
 * @brief Connects to modbus server with given ip address or domain name.
 * @details Tries to connect to the server, if not available returns error.
 * @param[in] connection_address [const char*] domain name or direct ip address
 * string of modbus device. can be used with "localhost" to simulate on pc.
 * @return [int] returns 0 if connection is succesfull, otherwise returns -1
 */
int connect_to_modbus_server(const char *connection_address);

/*****************************************************************************/
/**
 * @brief Checks if connection is still available or not.
 * @details
 * @return [int] returns 0 if connection is still available. otherwise
 * returns -1
 */
int check_modbus_server_connection(void);

/*****************************************************************************/
/**
 * @brief Sends read request to modbus server
 * @details This function only sends request. Here is another functions that
 * achieves receiving responses from server. Transaction ID is not used for
 * now, can be added later.
 * @param[in] modbus_func [modbus_functions_t] modbus function indicator,
 * This value can be one of four read functions. it must be FUNC_READ_COILS,
 * FUNC_READ_DISCRETE_INPUTS, FUNC_READ_HOLDING_REGISTERS or
 * FUNC_READ_INPUT_REGISTERS. Otherwise it'll return error
 * MODBUS_REQ_INVALID_FUNCTION.
 * @param[in] address [uint16_t] register address that wants to be received
 * @param[in] length [uint16_t] number of registers that is wanted to be
 * received. Can't exceed 125 for reading registers.
 * @return [modbus_req_return_val_t] returns request errors or MODBUS_REQ_OK
 * if no problem occured.
 */
modbus_req_return_val_t send_read_req(modbus_functions_t modbus_func,
                                      uint16_t address,
                                      uint16_t length);

/*****************************************************************************/
/**
 * @brief Sends write single coil request to modbus server.
 * @details Sends COIL_ON or COIL_OFF request to the coil on the given address.
 * @param[in] address [uint16_t] register address that wants to be written
 * @param[in] value [write_single_coil_value_t] COIL_ON or COIL_OFF value must
 * be used.
 * @return [modbus_req_return_val_t] returns request errors or MODBUS_REQ_OK
 * if no problem occured.
 */
modbus_req_return_val_t send_write_single_coil_req(uint16_t address,
                                                   write_single_coil_value_t value);

/*****************************************************************************/
/**
 * @brief Sends write single register request to modbus server.
 * @details Sets the register to the given uint16_t value
 * @param[in] address [uint16_t] register address that wants to be written
 * @param[in] value [uint16_t] value that'll be written to the written
 * @return [modbus_req_return_val_t] returns request errors or MODBUS_REQ_OK
 * if no problem occured.
 */
modbus_req_return_val_t send_write_single_reg_req(uint16_t address,
                                                  uint16_t value);

/*****************************************************************************/
/**
 * @brief Sends write multiple coils request to modbus server.
 * @details This function will be used with write multiple coils, data given
 * must be sized as big as to contain reg_count number of bits.
 * Ex: reg_count is 10 that means 2 byte will be used. First bit is
 * contained as first bit of first byte and 8th bit is the last bit of first
 * byte. 9th bits is first byte of second byte etc.
 * @param[in] start_address [uint16_t] first address of the registers those
 * wanted to be written.
 * @param[in] data [uint8_t *] byte sequence that contains corresponding bits
 * of coils, for example: first bit is first byte's first bit and 9th bit is
 * second byte's first bit.
 * @param[in] reg_count [uint16_t] number of registers which is wanted to
 * be manipulated.
 * @return [modbus_req_return_val_t] returns request errors or MODBUS_REQ_OK
 * if no problem occured.
 */
modbus_req_return_val_t send_write_mult_coils_req(uint16_t start_address,
                                                  uint8_t *data,
                                                  uint16_t reg_count);

/*****************************************************************************/
/**
 * @brief Sends write multiple registers request to modbus server.
 * @details This function will be used with multiple register sequence. Every
 * register is 16 bits.
 * @param[in] start_address [uint16_t] first address of the registers those
 * wanted to be written.
 * @param[in] data [uint16_t *] value list that'll be written to registers.
 * size must be same with reg_count parameter.
 * @param[in] reg_count [uint16_t] number of registers which is wanted to
 * be manipulated.
 * @return [modbus_req_return_val_t] returns request errors or MODBUS_REQ_OK
 * if no problem occured.
 */
modbus_req_return_val_t send_write_mult_reg_req(uint16_t start_address,
                                                uint16_t *data,
                                                uint16_t reg_count);

/*****************************************************************************/
/**
 * @brief it tries to receive responses from modbus server. if returns
 * MODBUS_RESPONSE_OK data received successfully, otherwise a problem occured
 * or server didn't answer yet. it waits data for 1 seconds.
 * @details Returns the requested data with data_received parameter. This
 * function will fill it with the corresponding data. And will return the
 * data size with data_length parameter. if it returnss MODBUS_RESPONSE_OK it
 * means no error occured. Can return modbus errors like illegal function or
 * illegal address. Other modbus errors will be returned as
 * MODBUS_RESPONSE_GENERAL_ERROR. One of the other error is
 * MODBUS_RESPONSE_COMMUNICATION_PROBLEM. This indicates there was a problem
 * in communication. if return is MODBUS_RESPONSE_NO_ANSWER_YET, it means
 * server didn't respond yet. Can be called again.
 * @param[out] data_received [uint8_t *] this is a buffer and must be at
 * least big as data requested. maximum size limit is 251 byte which is
 * indicated with macro MODBUS_RECEIVE_MAX_DATA_SIZE.
 * @param[out] data_length [uint8_t *] the size of data at response. the
 * function will fill this parameter. it'll get how many bytes are returned
 * for example if you read 10 coils or discrete inputs. This parameter
 * will be 2 bytes. If you read registers. You'll get ,
 * (register count * 2) because every register is 2 byte
 * @return [modbus_response_return_val_t] returns response errors or
 * MODBUS_RESPONSE_OK.
 */
modbus_response_return_val_t receive_read_coils_or_inputs_response(uint8_t *data_received,
                                                                   uint8_t *data_length);

/*****************************************************************************/
/**
 * @brief it tries to receive read registers functions' responses from modbus
 * server. Function are read holding registers and read discrete inputs.
 * if returns MODBUS_RESPONSE_OK data received successfully, otherwise a
 * problem occured or server didn't answer yet. it waits data for 1 seconds.
 * @details Returns the requested data with data_received parameter. This
 * function will fill it with the corresponding data. And will return the
 * data size with data_length parameter. if it returnss MODBUS_RESPONSE_OK it
 * means no error occured. Can return modbus errors like illegal function or
 * illegal address. Other modbus errors will be returned as
 * MODBUS_RESPONSE_GENERAL_ERROR. One of the other error is
 * MODBUS_RESPONSE_COMMUNICATION_PROBLEM. This indicates there was a problem
 * in communication. if return is MODBUS_RESPONSE_NO_ANSWER_YET, it means
 * server didn't respond yet. Can be called again.
 * @param[out] data_received [uint16_t *] this is a buffer and must be at
 * least big as data requested. maximum size limit is 125 byte which is
 * indicated with macro MODBUS_RECEIVE_MAX_DATA_SIZE / 2.
 * @param[out] data_length [uint8_t *] the size of data at response. the
 * function will fill this parameter. You'll get number of registers returned
 * @return [modbus_response_return_val_t] returns response errors or
 * MODBUS_RESPONSE_OK.
 */
modbus_response_return_val_t receive_read_registers_response(uint16_t *data_received,
                                                             uint8_t *data_length);

/*****************************************************************************/
/**
 * @brief it receives write single coil response and fills buffers with written
 * data.
 * @details address and value parameters will be set after receiving. This
 * function will return MODBUS_RESPONSE_OK at no error. address and value
 * can be checked after calling if it is written right or not. This function
 * will return MODBUS_RESPONSE_WRONG_DATA_RETURNED on inappropriate response
 * received. Can return modbus errors like illegal function or illegal address.
 * Other modbus errors will be returned as MODBUS_RESPONSE_GENERAL_ERROR.
 * if return is MODBUS_RESPONSE_NO_ANSWER_YET, it means server didn't respond
 * yet. Can be called again.
 * @param[out] address [uint16_t *] this parameter is a buffer with length 1,
 * will be filled with response in no error situation.
 * @param[out] value [write_single_coil_value_t *] this will return COIL_ON
 * or COIL_OFF in normal conditions. It'll be not filled if the return is
 * MODBUS_RESPONSE_WRONG_DATA_RETURNED.
 * @return [modbus_response_return_val_t] returns response errors or
 * MODBUS_RESPONSE_OK.
 */
modbus_response_return_val_t receive_write_single_coil_response(uint16_t *address,
                                                                write_single_coil_value_t *value);

/*****************************************************************************/
/**
 * @brief it receives write single register response and fills buffers with
 * written data.
 * @details address and value parameters will be set after receiving. This
 * function will return MODBUS_RESPONSE_OK at no error. Address and value
 * can be checked after calling if it is written right or not. Can return
 * modbus errors like illegal function or illegal address. Other modbus errors
 * will be returned as MODBUS_RESPONSE_GENERAL_ERROR.  if return is
 * MODBUS_RESPONSE_NO_ANSWER_YET, it means server didn't respond  yet. Can be
 * called again.
 * @param[out] address [uint16_t *] this parameter is a buffer with length 1,
 * will be filled with response in no error situation.
 * @param[out] value [uint16_t *] will be filled with given value in the
 * request in no error situation.
 * @return [modbus_response_return_val_t] returns response errors or
 * MODBUS_RESPONSE_OK.
 */
modbus_response_return_val_t receive_write_single_reg_response(uint16_t *address,
                                                               uint16_t *value);

/*****************************************************************************/
/**
 * @brief it receives response of write_multiple_req function. it can receive
 * responses of both write multiple registers and write multiple coils.
 * @details address and num_of_recorded_regs parameters will be set after
 * receiving. Address and number of recorded registers can be checked after
 * calling if it is written right or not. This function will return
 * MODBUS_RESPONSE_OK at no error. Address and value can be checked after
 * calling if it is written right or not. Can return modbus errors like illegal
 * function or illegal address. Other modbus errors will be returned as
 * MODBUS_RESPONSE_GENERAL_ERROR.  if return is  MODBUS_RESPONSE_NO_ANSWER_YET,
 * it means server didn't respond  yet. Can be called again.
 * @param[out] address [uint16_t *] this parameter is a buffer with length 1,
 * will be filled with response in no error situation.
 * @param[out] num_of_recorded_regs [uint16_t *] will be filled with number of
 * recorded registers in no error situation.
 * @return [modbus_response_return_val_t] returns response errors or
 * MODBUS_RESPONSE_OK.
 */
modbus_response_return_val_t receive_write_mult_response(uint16_t *address,
                                                         uint16_t *num_of_recorded_regs);

/*****************************************************************************/
/**
 * @brief Returns resources used while communicating. Must be called after
 * communication errors. Must be called for terminating communication.
 * @details Closes connection by releasing resources used for communication.
 * @return [void]
 */
void close_connection(void);

/*****************************************************************************/

#endif