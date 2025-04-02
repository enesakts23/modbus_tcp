/*
    file: main.c
    date: 18.03.2025
    author: Emir
    brief: Main of Reap Modbus TCP Example Project 
    description: This will be the main.c file of Modbus TCP Communication Example,
    TCP Communication is based on tcp_project tcp_client module. This module needs
    to be improved.
*/

#define _GNU_SOURCE
#define MAX_MESSAGE_SIZE 500

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "modbus.h"
// #include "tcp_client.h"

void ReadEMSData(void);
void ReadFromPCServer(void);
void WriteToPCServeWriteSingleCoil(void);
void WriteToPCServerWriteSingleReg(void);
void WriteToPCServerWriteMultiCoils(void);
void WriteToPCServerWriteMultiRegisters(void);
void print_received_data(uint8_t data_length);
void return_errors(modbus_respond_return_val_t ret_val);

uint8_t pdu_buffer[MODBUS_RECEIVE_MAX_DATA_SIZE];
uint8_t pdu_write_buffer[MODBUS_WRITE_MULT_REQ_MAX_DATA_SIZE];

int main(void)
{
    // ReadFromPCServer();
    // WriteToPCServeWriteSingleCoil();
    // WriteToPCServerWriteSingleReg();
    // WriteToPCServerWriteMultiCoils();
    WriteToPCServerWriteMultiRegisters();

    return 0;
}

void ReadFromPCServer(void)
{  
    uint8_t data_length;
    uint8_t counter = 0;
    modbus_respond_return_val_t ret_val;

    if(connect_to_modbus_server("localhost") == -1)
    {
        exit(EXIT_FAILURE);
    }

    if (check_modbus_server_connection() == -1)
    {
        printf("Connection Closed\n");
        exit(EXIT_FAILURE);
    }

    if(send_read_req(FUNC_READ_COILS, 0, 8) != MODBUS_REQ_OK)
    {
        printf("Communication Error, Exitting...\n");
        exit(EXIT_FAILURE);
    }

    while((ret_val = receive_read_response(pdu_buffer, &data_length)) == MODBUS_RESPONSE_NO_ANSWER_YET)
    {
        printf("Waiting Message\n");
        counter++;
        if(counter == 10)
        {
            break;
        }
    }

    if(ret_val == MODBUS_RESPONSE_OK){
        print_received_data(data_length);
    }
    else
    {
        return_errors(ret_val);
    }

    if (check_modbus_server_connection() == -1)
    {
        printf("Connection Closed\n");
        exit(EXIT_FAILURE);
    }
    
    if(send_read_req(FUNC_READ_DISCRETE_INPUTS, 0, 10) != MODBUS_REQ_OK)
    {
        printf("Communication Error, Exitting...\n");
        exit(EXIT_FAILURE);
    }

    while((ret_val = receive_read_response(pdu_buffer, &data_length)) == MODBUS_RESPONSE_NO_ANSWER_YET)
    {
        printf("Waiting Message\n");
        counter++;
        if(counter == 10)
        {
            break;
        }
    }

    if(ret_val == MODBUS_RESPONSE_OK){
        print_received_data(data_length);
    }
    else
    {
        return_errors(ret_val);
    }

    if(send_read_req(FUNC_READ_HOLDING_REGISTERS, 0, 2) != MODBUS_REQ_OK)
    {
        printf("Communication Error, Exitting...\n");
        exit(EXIT_FAILURE);
    }

    while((ret_val = receive_read_response(pdu_buffer, &data_length)) == MODBUS_RESPONSE_NO_ANSWER_YET)
    {
        printf("Waiting Message\n");
        counter++;
        if(counter == 10)
        {
            break;
        }
    }
    if(ret_val == MODBUS_RESPONSE_OK){
        print_received_data(data_length);
    }
    else
    {
        return_errors(ret_val);
    }


    if(send_read_req(FUNC_READ_INPUT_REGISTERS, 2, 2) != MODBUS_REQ_OK)
    {
        printf("An Error Occured\nExitting...\n");
        exit(EXIT_FAILURE);
    }

    while((ret_val = receive_read_response(pdu_buffer, &data_length)) == MODBUS_RESPONSE_NO_ANSWER_YET)
    {
        printf("Waiting Message\n");
        counter++;
        if(counter == 10)
        {
            break;
        }
    }

    if(ret_val == MODBUS_RESPONSE_OK){
        print_received_data(data_length);
    }
    else
    {
        return_errors(ret_val);
    }
}

void WriteToPCServeWriteSingleCoil(void)
{
    uint8_t data_length;
    uint8_t counter = 0;
    modbus_respond_return_val_t ret_val;
    
    if(connect_to_modbus_server("localhost") == -1)
    {
        exit(EXIT_FAILURE);
    }

    if (check_modbus_server_connection() == -1)
    {
        printf("Connection Closed\n");
        exit(EXIT_FAILURE);
    }

    send_write_single_coil_req(0x02, COIL_ON);

    if (check_modbus_server_connection() == -1)
    {
        printf("Connection Closed\n");
        exit(EXIT_FAILURE);
    }

    uint16_t address_received;
    write_single_req_value_t value;
    receive_write_single_coil_response(&address_received, &value);

    if((value != COIL_ON) || (address_received != 0x02))
    {
        printf("Wrong Value\n");
        exit(EXIT_FAILURE);
    }

    if (check_modbus_server_connection() == -1)
    {
        printf("Connection Closed\n");
        exit(EXIT_FAILURE);
    }

    if(send_read_req(FUNC_READ_COILS, 0, 8) != MODBUS_REQ_OK)
    {
        printf("Communication Error, Exitting...\n");
        exit(EXIT_FAILURE);
    }

    while((ret_val = receive_read_response(pdu_buffer, &data_length)) == MODBUS_RESPONSE_NO_ANSWER_YET)
    {
        printf("Waiting Message\n");
        counter++;
        if(counter == 10)
        {
            break;
        }
    }

    if(ret_val == MODBUS_RESPONSE_OK){
        print_received_data(data_length);
    }
    else
    {
        return_errors(ret_val);
    }
}

void WriteToPCServerWriteSingleReg(void)
{
    uint8_t data_length;
    uint8_t counter = 0;
    modbus_respond_return_val_t ret_val;
    
    if(connect_to_modbus_server("localhost") == -1)
    {
        exit(EXIT_FAILURE);
    }

    if (check_modbus_server_connection() == -1)
    {
        printf("Connection Closed\n");
        exit(EXIT_FAILURE);
    }

    send_write_single_reg_req(0x02, 0xABCD);

    if (check_modbus_server_connection() == -1)
    {
        printf("Connection Closed\n");
        exit(EXIT_FAILURE);
    }

    uint16_t address_received;
    uint16_t value;

    receive_write_single_reg_response(&address_received, &value);

    printf("Address = 0x%X\n", address_received);
    printf("Value = 0x%X\n", value);

    if (check_modbus_server_connection() == -1)
    {
        printf("Connection Closed\n");
        exit(EXIT_FAILURE);
    }

    if(send_read_req(FUNC_READ_HOLDING_REGISTERS, 2, 1) != MODBUS_REQ_OK)
    {
        printf("Communication Error, Exitting...\n");
        exit(EXIT_FAILURE);
    }

    while((ret_val = receive_read_response(pdu_buffer, &data_length)) == MODBUS_RESPONSE_NO_ANSWER_YET)
    {
        printf("Waiting Message\n");
        counter++;
        if(counter == 10)
        {
            break;
        }
    }

    if(ret_val == MODBUS_RESPONSE_OK){
        print_received_data(data_length);
    }
    else
    {
        return_errors(ret_val);
    }
}

void WriteToPCServerWriteMultiCoils(void)
{
    uint8_t data_length;
    uint8_t counter = 0;
    modbus_respond_return_val_t ret_val;
    
    if(connect_to_modbus_server("localhost") == -1)
    {
        exit(EXIT_FAILURE);
    }

    if (check_modbus_server_connection() == -1)
    {
        printf("Connection Closed\n");
        exit(EXIT_FAILURE);
    }

    pdu_write_buffer[0] = 0x8C;
    pdu_write_buffer[1] = 0x02;

    send_write_mult_coils_req(FUNC_WRITE_MULTIPLE_COILS, 0x00, pdu_write_buffer, 10);

    if (check_modbus_server_connection() == -1)
    {
        printf("Connection Closed\n");
        exit(EXIT_FAILURE);
    }

    uint16_t address_received;
    uint16_t nums_of_recorded_registers;

    receive_write_mult_response(&address_received, &nums_of_recorded_registers);

    printf("Address = 0x%X\n", address_received);
    printf("Value = 0x%X\n", nums_of_recorded_registers);

    if (check_modbus_server_connection() == -1)
    {
        printf("Connection Closed\n");
        exit(EXIT_FAILURE);
    }

    if(send_read_req(FUNC_READ_COILS, 0x00, 10) != MODBUS_REQ_OK)
    {
        printf("Communication Error, Exitting...\n");
        exit(EXIT_FAILURE);
    }

    while((ret_val = receive_read_response(pdu_buffer, &data_length)) == MODBUS_RESPONSE_NO_ANSWER_YET)
    {
        printf("Waiting Message\n");
        counter++;
        if(counter == 10)
        {
            break;
        }
    }

    if(ret_val == MODBUS_RESPONSE_OK){
        print_received_data(data_length);
    }
    else
    {
        return_errors(ret_val);
    }
}

void WriteToPCServerWriteMultiRegisters(void)
{
    uint8_t data_length;
    uint8_t counter = 0;
    modbus_respond_return_val_t ret_val;
    
    if(connect_to_modbus_server("localhost") == -1)
    {
        exit(EXIT_FAILURE);
    }

    if (check_modbus_server_connection() == -1)
    {
        printf("Connection Closed\n");
        exit(EXIT_FAILURE);
    }

    // 3 Registers
    pdu_write_buffer[0] = 0x6A;
    pdu_write_buffer[1] = 0xCC;
    pdu_write_buffer[2] = 0x0A;
    pdu_write_buffer[3] = 0xFF;
    pdu_write_buffer[4] = 0x00;
    pdu_write_buffer[5] = 0x2D;

    send_write_mult_coils_req(FUNC_WRITE_MULTIPLE_REGISTERS, 0x00, pdu_write_buffer, 3);

    if (check_modbus_server_connection() == -1)
    {
        printf("Connection Closed\n");
        exit(EXIT_FAILURE);
    }

    uint16_t address_received;
    uint16_t nums_of_recorded_registers;

    receive_write_mult_response(&address_received, &nums_of_recorded_registers);

    printf("Address = 0x%X\n", address_received);
    printf("Value = 0x%X\n", nums_of_recorded_registers);

    if (check_modbus_server_connection() == -1)
    {
        printf("Connection Closed\n");
        exit(EXIT_FAILURE);
    }

    if(send_read_req(FUNC_READ_HOLDING_REGISTERS, 0x00, 3) != MODBUS_REQ_OK)
    {
        printf("Communication Error, Exitting...\n");
        exit(EXIT_FAILURE);
    }

    while((ret_val = receive_read_response(pdu_buffer, &data_length)) == MODBUS_RESPONSE_NO_ANSWER_YET)
    {
        printf("Waiting Message\n");
        counter++;
        if(counter == 10)
        {
            break;
        }
    }

    if(ret_val == MODBUS_RESPONSE_OK){
        print_received_data(data_length);
    }
    else
    {
        return_errors(ret_val);
    }
}

void ReadEMSData(void)
{
    uint8_t data_length;
    uint8_t counter = 0;
    int ret_val;
    
    if(connect_to_modbus_server("198.120.0.250") == -1)      // EMS Side
    {
        exit(EXIT_FAILURE);
    }

    if (check_modbus_server_connection() == -1)
    {
        printf("Connection Closed\n");
        exit(EXIT_FAILURE);
    }

    if(send_read_req(FUNC_READ_DISCRETE_INPUTS, 6000, 16) != MODBUS_REQ_OK)
    {
        printf("Communication Error, Exitting...\n");
        exit(EXIT_FAILURE);
    }

    while((ret_val = receive_read_response(pdu_buffer, &data_length)) == MODBUS_RESPONSE_NO_ANSWER_YET)
    {
        printf("Waiting Message\n");
        counter++;
        if(counter == 10)
        {
            break;
        }
    }

    if(ret_val == MODBUS_RESPONSE_OK){
        print_received_data(data_length);
    }
    else
    {
        return_errors(ret_val);
    }
    
}

void print_received_data(uint8_t data_length)
{
    printf("**************** Data Returned ****************\n");
    for(uint8_t i = 0; i < data_length; i++)
    {
        printf("Data[%u] = 0x%.2X\n", i, pdu_buffer[i]);
    }
    printf("\n");
}

void return_errors(modbus_respond_return_val_t ret_val)
{
    if(ret_val == MODBUS_RESPONSE_ILLEGAL_ADDRESS)
    {
        printf("Illegal Address 0x02 Error Returned From Server\n");
    }
    else if(ret_val == MODBUS_RESPONSE_ILLEGAL_FUNCTION)
    {
        printf("Illegal Fucntion 0x01 Error Returned From Server\n");
    }
    else if(ret_val == MODBUS_RESPONSE_GENERAL_ERROR)
    {
        printf("An Error Returned From Server\n");
    }
    else if(ret_val == MODBUS_RESPONSE_COMMUNICATION_PROBLEM)
    {
        printf("Communication Error, Exitting...\n");
        exit(EXIT_FAILURE);
    }
    else{
        printf("Server didn't answer\nExitting\n");
    }
}