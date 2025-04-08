/*
    file: test.c
    date: 04.04.2025
    author: Emir
    brief: Test File for Modbus Module 
    description: This is the test file of modbus module.
    8 Functions of modbus tcp will be tested here. 
    We have a modbus tcp server that is created with libmodbus library.
    We have to run that server to test modbus tcp client.
    Test will be made with check framework. 
    Test names are self-explanatory
    Additional info will be added to README.md
    Test for Connection lost or other kind of Modbus Errors can't be
    tested. Maybe those tests can be made in real devices like unplugging
    cables.
*/
#define _GNU_SOURCE

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <check.h>
#include "modbus.h"

uint16_t pdu_buffer_uint16[(uint8_t)MODBUS_RECEIVE_MAX_DATA_SIZE / 2];
uint8_t pdu_buffer_uint8[MODBUS_RECEIVE_MAX_DATA_SIZE];
uint8_t pdu_write_buffer[MODBUS_WRITE_MULT_REQ_MAX_DATA_SIZE];

void tcase_default_setup(void)
{
    if(connect_to_modbus_server("localhost") == -1)
    {
        exit(EXIT_FAILURE);
    }
}

void tcase_default_teardown(void)
{
    close_connection();
}

void tcase_revert_changes_teardown(void)
{
    uint16_t address;
    uint16_t number_of_registers;

    uint8_t data_to_write[] = { 0x0C, 0x03 };
    write_single_coil_value_t coil_val;

    /* This will bring server back to the original state */
    ck_assert_int_ne(check_modbus_server_connection(), (int)-1);

    ck_assert_int_eq((int)send_write_single_coil_req(0x00, COIL_ON), (int)MODBUS_REQ_OK);

    /* Checks connection, if -1 connection is lost */
    ck_assert_int_ne(check_modbus_server_connection(), (int)-1);

    ck_assert_int_eq((int)receive_write_single_coil_response(&address, &coil_val), (int)MODBUS_REQ_OK);

    ck_assert_int_ne(check_modbus_server_connection(), (int)-1);

    ck_assert_int_eq((int)send_write_mult_coils_req(0x00, data_to_write, 10), (int)MODBUS_REQ_OK);

    /* Checks connection, if -1 connection is lost */
    ck_assert_int_ne(check_modbus_server_connection(), (int)-1);

    ck_assert_int_eq((int)receive_write_mult_response(&address, &number_of_registers), (int)MODBUS_REQ_OK);

    uint16_t data_to_write2[] = { 0x1234, 0x5678 , 0x0000 };

    /* Checks connection, if -1 connection is lost */
    ck_assert_int_ne(check_modbus_server_connection(), (int)-1);

    ck_assert_int_eq((int)send_write_mult_reg_req(0x00, data_to_write2, 3), (int)MODBUS_REQ_OK);

    /* Checks connection, if -1 connection is lost */
    ck_assert_int_ne(check_modbus_server_connection(), (int)-1);

    ck_assert_int_eq((int)receive_write_mult_response(&address, &number_of_registers), (int)MODBUS_REQ_OK);

    close_connection();
}

/*****************************************************************************/
/* This will test send_read_req function with illegal function*/
START_TEST(test_read_illegal_function)
{
    /* Checks connection, if -1 connection is lost */
    ck_assert_int_ne(check_modbus_server_connection(), (int)-1);

    ck_assert_int_eq((int)send_read_req(FUNC_WRITE_SINGLE_COIL, 0x00, 1), (int)MODBUS_REQ_INVALID_FUNCTION);
}

/*****************************************************************************/
/* This will test send_read_req function with illegal function*/
START_TEST(test_read_illegal_address)
{
    modbus_response_return_val_t ret_val;
    uint8_t counter = 0;
    uint8_t data_length;

    /* Checks connection, if -1 connection is lost */
    ck_assert_int_ne(check_modbus_server_connection(), (int)-1);
    
    ck_assert_int_eq((int)send_read_req(FUNC_READ_COILS, (uint16_t)0xFF, (uint16_t)10), (int)MODBUS_REQ_OK);
    
    /* Checks connection, if -1 connection is lost */
    ck_assert_int_ne(check_modbus_server_connection(), (int)-1);
    
    while((ret_val = receive_read_coils_or_inputs_response(pdu_buffer_uint8, &data_length)) == MODBUS_RESPONSE_NO_ANSWER_YET)
    {
        printf("Waiting Message\n");
        counter++;
        if(counter == 10)
        {
            break;
        }
    }
    
    /* It has to be MODBUS_RESPONSE_OK*/
    ck_assert_int_eq(ret_val, (int)MODBUS_RESPONSE_ILLEGAL_ADDRESS);
    
}

/*****************************************************************************/
/* This test is a successfull reading of coils */
START_TEST(test_read_coils_func)
{
    modbus_response_return_val_t ret_val;
    uint8_t counter = 0;
    uint8_t data_length;

    /* Checks connection, if -1 connection is lost */
    ck_assert_int_ne(check_modbus_server_connection(), (int)-1);
    
    ck_assert_int_eq((int)send_read_req(FUNC_READ_COILS, 0x00, 10), (int)MODBUS_REQ_OK);
    
    /* Checks connection, if -1 connection is lost */
    ck_assert_int_ne(check_modbus_server_connection(), (int)-1);

    while((ret_val = receive_read_coils_or_inputs_response(pdu_buffer_uint8, &data_length)) == MODBUS_RESPONSE_NO_ANSWER_YET)
    {
        printf("Waiting Message\n");
        counter++;
        if(counter == 10)
        {
            break;
        }
    }

    /* It has to be MODBUS_RESPONSE_OK*/
    ck_assert_int_eq(ret_val, (int)MODBUS_RESPONSE_OK);

    ck_assert_int_eq((int)data_length, (int)2);
    /* These values come from server code. */
    ck_assert_int_eq((int)pdu_buffer_uint8[0], (int)0x0C);
    ck_assert_int_eq((int)pdu_buffer_uint8[1], (int)0x03);
}
END_TEST

/*****************************************************************************/
/* This test is a successfull reading of discrete inputs */
START_TEST(test_read_discrete_inputs_func)
{
    modbus_response_return_val_t ret_val;
    uint8_t counter = 0;
    uint8_t data_length;
    
    /* Checks connection, if -1 connection is lost */
    ck_assert_int_ne(check_modbus_server_connection(), (int)-1);

    ck_assert_int_eq((int)send_read_req(FUNC_READ_DISCRETE_INPUTS, (uint16_t)0x00, (uint16_t)10), (int)MODBUS_REQ_OK);

    /* Checks connection, if -1 connection is lost */
    ck_assert_int_ne(check_modbus_server_connection(), (int)-1);

    while((ret_val = receive_read_coils_or_inputs_response(pdu_buffer_uint8, &data_length)) == MODBUS_RESPONSE_NO_ANSWER_YET)
    {
        printf("Waiting Message\n");
        counter++;
        if(counter == 10)
        {
            break;
        }
    }

    /* It has to be MODBUS_RESPONSE_OK*/
    ck_assert_int_eq(ret_val, (int)MODBUS_RESPONSE_OK);

    ck_assert_int_eq((int)data_length, (int)2);
    /* These values come from server code. */
    ck_assert_int_eq((int)pdu_buffer_uint8[0], (int)0xC5);
    ck_assert_int_eq((int)pdu_buffer_uint8[1], (int)0x02);

}

/*****************************************************************************/
/* This test is a successfull reading of holding registers */
START_TEST(test_read_holding_registers_func)
{
    modbus_response_return_val_t ret_val;
    uint8_t counter = 0;
    uint8_t data_length;
    
    /* Checks connection, if -1 connection is lost */
    ck_assert_int_ne(check_modbus_server_connection(), (int)-1);

    ck_assert_int_eq((int)send_read_req(FUNC_READ_HOLDING_REGISTERS, (uint16_t)0x00, (uint16_t)10), (int)MODBUS_REQ_OK);

    /* Checks connection, if -1 connection is lost */
    ck_assert_int_ne(check_modbus_server_connection(), (int)-1);

    while((ret_val = receive_read_registers_response(pdu_buffer_uint16, &data_length)) == MODBUS_RESPONSE_NO_ANSWER_YET)
    {
        printf("Waiting Message\n");
        counter++;
        if(counter == 10)
        {
            break;
        }
    }

    /* It has to be MODBUS_RESPONSE_OK*/
    ck_assert_int_eq(ret_val, (int)MODBUS_RESPONSE_OK);

    ck_assert_int_eq((int)data_length, (int)10);

    // /* These values come from server code. */ 
    ck_assert_int_eq((int)pdu_buffer_uint16[0], (int)0x1234);
    ck_assert_int_eq((int)pdu_buffer_uint16[1], (int)0x5678);

}

START_TEST(test_read_input_registers_func)
{
    modbus_response_return_val_t ret_val;
    uint8_t counter = 0;
    uint8_t data_length;
    
    /* Checks connection, if -1 connection is lost */
    ck_assert_int_ne(check_modbus_server_connection(), (int)-1);

    ck_assert_int_eq((int)send_read_req(FUNC_READ_INPUT_REGISTERS, (uint16_t)0x00, (uint16_t)10), (int)MODBUS_REQ_OK);

    /* Checks connection, if -1 connection is lost */
    ck_assert_int_ne(check_modbus_server_connection(), (int)-1);

    while((ret_val = receive_read_registers_response(pdu_buffer_uint16, &data_length)) == MODBUS_RESPONSE_NO_ANSWER_YET)
    {
        printf("Waiting Message\n");
        counter++;
        if(counter == 10)
        {
            break;
        }
    }

    /* It has to be MODBUS_RESPONSE_OK*/
    ck_assert_int_eq(ret_val, (int)MODBUS_RESPONSE_OK);

    ck_assert_int_eq((int)data_length, (int)10);

    // /* These values come from server code. */ 
    ck_assert_int_eq((int)pdu_buffer_uint16[2], (int)0x9ABC);
    ck_assert_int_eq((int)pdu_buffer_uint16[3], (int)0xDEF1);
}

START_TEST(test_write_single_coil_wrong_value)
{
    modbus_response_return_val_t ret_val;
    uint8_t counter = 0;
    uint16_t address;
    uint8_t data_length;
    write_single_coil_value_t coil_val;

    /* Checks connection, if -1 connection is lost */
    ck_assert_int_ne(check_modbus_server_connection(), (int)-1);

    ck_assert_int_eq((int)send_write_single_coil_req(0x00, 7), (int)MODBUS_REQ_WRONG_VALUE);
}

START_TEST(test_write_single_coil_illegal_address)
{
    modbus_response_return_val_t ret_val;
    uint8_t counter = 0;
    uint16_t address;
    uint8_t data_length;
    write_single_coil_value_t coil_val;

    /* Checks connection, if -1 connection is lost */
    ck_assert_int_ne(check_modbus_server_connection(), (int)-1);

    ck_assert_int_eq((int)send_write_single_coil_req(0xFF, COIL_ON), (int)MODBUS_REQ_OK);

    ck_assert_int_ne(check_modbus_server_connection(), (int)-1);

    ck_assert_int_eq((int)receive_write_single_coil_response(&address, &coil_val), (int)MODBUS_RESPONSE_ILLEGAL_ADDRESS);
}

START_TEST(test_write_single_coil_func)
{
    modbus_response_return_val_t ret_val;
    uint8_t counter = 0;
    uint16_t address;
    uint8_t data_length;
    write_single_coil_value_t coil_val;

    /* Checks connection, if -1 connection is lost */
    ck_assert_int_ne(check_modbus_server_connection(), (int)-1);

    ck_assert_int_eq((int)send_write_single_coil_req(0x00, COIL_ON), (int)MODBUS_REQ_OK);

    /* Checks connection, if -1 connection is lost */
    ck_assert_int_ne(check_modbus_server_connection(), (int)-1);

    ck_assert_int_eq((int)receive_write_single_coil_response(&address, &coil_val), (int)MODBUS_RESPONSE_OK);

    ck_assert_uint_eq((uint)address, (uint)0x00);
    ck_assert_uint_eq((uint)coil_val, (uint)COIL_ON);
    
    /* Checks connection, if -1 connection is lost */
    ck_assert_int_ne(check_modbus_server_connection(), (int)-1);

    ck_assert_int_eq((int)send_read_req(FUNC_READ_COILS, (uint16_t)0x00, (uint16_t)10), (int)MODBUS_REQ_OK);

    /* Checks connection, if -1 connection is lost */
    ck_assert_int_ne(check_modbus_server_connection(), (int)-1);

    while((ret_val = receive_read_coils_or_inputs_response(pdu_buffer_uint8, &data_length)) == MODBUS_RESPONSE_NO_ANSWER_YET)
    {
        printf("Waiting Message\n");
        counter++;
        if(counter == 10)
        {
            break;
        }
    }

    /* It has to be MODBUS_RESPONSE_OK*/
    ck_assert_int_eq(ret_val, (int)MODBUS_RESPONSE_OK);

    /* This is 2 because it we tried to read 10 registers. */
    ck_assert_int_eq((int)data_length, (int)2);

    /* These values come from server code. */
    ck_assert_int_eq((int)pdu_buffer_uint8[0], (int)0x0D);
}

START_TEST(test_write_single_reg_func)
{
    modbus_response_return_val_t ret_val;
    uint8_t counter = 0;
    uint8_t data_length;
    uint16_t address;
    uint16_t value;

    uint16_t data_to_write = 0x1234;

    /* Checks connection, if -1 connection is lost */
    ck_assert_int_ne(check_modbus_server_connection(), (int)-1);

    ck_assert_int_eq((int)send_write_single_reg_req(0x09, data_to_write), (int)MODBUS_REQ_OK);

    /* Checks connection, if -1 connection is lost */
    ck_assert_int_ne(check_modbus_server_connection(), (int)-1);

    ck_assert_int_eq((int)receive_write_single_reg_response(&address, &value), (int)MODBUS_RESPONSE_OK);

    ck_assert_uint_eq((uint)address, (uint)0x09);
    ck_assert_uint_eq((uint)value, (uint)0x1234);
    
    /* Checks connection, if -1 connection is lost */
    ck_assert_int_ne(check_modbus_server_connection(), (int)-1);

    ck_assert_int_eq((int)send_read_req(FUNC_READ_HOLDING_REGISTERS, (uint16_t)0x00, (uint16_t)10), (int)MODBUS_REQ_OK);

    /* Checks connection, if -1 connection is lost */
    ck_assert_int_ne(check_modbus_server_connection(), (int)-1);

    while((ret_val = receive_read_registers_response(pdu_buffer_uint16, &data_length)) == MODBUS_RESPONSE_NO_ANSWER_YET)
    {
        printf("Waiting Message\n");
        counter++;
        if(counter == 10)
        {
            break;
        }
    }

    /* It has to be MODBUS_RESPONSE_OK*/
    ck_assert_int_eq(ret_val, (int)MODBUS_RESPONSE_OK);

    ck_assert_int_eq((int)data_length, (int)10);
    /* These values come from server code. */
    ck_assert_int_eq((int)pdu_buffer_uint16[0x09], (int)0x1234);

}

START_TEST(test_write_mult_coils_func)
{
    modbus_response_return_val_t ret_val;
    uint8_t counter = 0;
    uint8_t data_length;
    uint16_t address;
    uint16_t number_of_registers;

    uint8_t data_to_write[] = { 0xFA, 0x02 };

    /* Checks connection, if -1 connection is lost */
    ck_assert_int_ne(check_modbus_server_connection(), (int)-1);

    ck_assert_int_eq((int)send_write_mult_coils_req(0x00, data_to_write, 10), (int)MODBUS_REQ_OK);

    /* Checks connection, if -1 connection is lost */
    ck_assert_int_ne(check_modbus_server_connection(), (int)-1);

    ck_assert_int_eq((int)receive_write_mult_response(&address, &number_of_registers), (int)MODBUS_RESPONSE_OK);

    ck_assert_uint_eq((uint)address, (uint)0x00);
    ck_assert_uint_eq((uint)number_of_registers, (uint)10);
    
    /* Checks connection, if -1 connection is lost */
    ck_assert_int_ne(check_modbus_server_connection(), (int)-1);

    ck_assert_int_eq((int)send_read_req(FUNC_READ_COILS, (uint16_t)0x00, (uint16_t)10), (int)MODBUS_REQ_OK);

    /* Checks connection, if -1 connection is lost */
    ck_assert_int_ne(check_modbus_server_connection(), (int)-1);

    while((ret_val = receive_read_coils_or_inputs_response(pdu_buffer_uint8, &data_length)) == MODBUS_RESPONSE_NO_ANSWER_YET)
    {
        printf("Waiting Message\n");
        counter++;
        if(counter == 10)
        {
            break;
        }
    }

    /* It has to be MODBUS_RESPONSE_OK*/
    ck_assert_int_eq(ret_val, (int)MODBUS_RESPONSE_OK);

    ck_assert_int_eq((int)data_length, (int)2);
    /* These values come from server code. */
    ck_assert_int_eq((int)pdu_buffer_uint8[0], (int)0xFA);
    ck_assert_int_eq((int)pdu_buffer_uint8[1], (int)0x02);
}

START_TEST(test_write_mult_reg_func)
{
    modbus_response_return_val_t ret_val;
    uint8_t counter = 0;
    uint8_t data_length;
    uint16_t address;
    uint16_t number_of_registers;

    uint16_t data_to_write[] = { 0x9ABC, 0xEF12, 0x3456 };

    /* Checks connection, if -1 connection is lost */
    ck_assert_int_ne(check_modbus_server_connection(), (int)-1);

    ck_assert_int_eq((int)send_write_mult_reg_req(0x00, data_to_write, 3), (int)MODBUS_REQ_OK);

    /* Checks connection, if -1 connection is lost */
    ck_assert_int_ne(check_modbus_server_connection(), (int)-1);

    ck_assert_int_eq((int)receive_write_mult_response(&address, &number_of_registers), (int)MODBUS_RESPONSE_OK);

    ck_assert_uint_eq((uint)address, (uint)0x00);
    ck_assert_uint_eq((uint)number_of_registers, (uint)3);
    
    /* Checks connection, if -1 connection is lost */
    ck_assert_int_ne(check_modbus_server_connection(), (int)-1);

    ck_assert_int_eq((int)send_read_req(FUNC_READ_HOLDING_REGISTERS, (uint16_t)0x00, (uint16_t)10), (int)MODBUS_REQ_OK);

    /* Checks connection, if -1 connection is lost */
    ck_assert_int_ne(check_modbus_server_connection(), (int)-1);

    while((ret_val = receive_read_registers_response(pdu_buffer_uint16, &data_length)) == MODBUS_RESPONSE_NO_ANSWER_YET)
    {
        printf("Waiting Message\n");
        counter++;
        if(counter == 10)
        {
            break;
        }
    }

    /* It has to be MODBUS_RESPONSE_OK*/
    ck_assert_int_eq(ret_val, (int)MODBUS_RESPONSE_OK);

    ck_assert_int_eq((int)data_length, (int)10);
    /* These values come from server code. */
    ck_assert_int_eq((int)pdu_buffer_uint16[0], (int)0x9ABC);
    ck_assert_int_eq((int)pdu_buffer_uint16[1], (int)0xEF12);
    ck_assert_int_eq((int)pdu_buffer_uint16[2], (int)0x3456);

}

/*****************************************************************************/
Suite * modbus_tcp_suite(void)
{
    Suite *s;

    s = suite_create("Modbus TCP Client");

    /* Read Functions Tests */
    TCase *tc_read_functions;
    tc_read_functions = tcase_create("Read Tests");
    tcase_add_checked_fixture(tc_read_functions, tcase_default_setup, tcase_default_teardown);
    tcase_add_test(tc_read_functions, test_read_illegal_function);
    tcase_add_test(tc_read_functions, test_read_illegal_address);
    tcase_add_test(tc_read_functions, test_read_coils_func);
    tcase_add_test(tc_read_functions, test_read_discrete_inputs_func);
    tcase_add_test(tc_read_functions, test_read_holding_registers_func);
    tcase_add_test(tc_read_functions, test_read_input_registers_func);
    suite_add_tcase(s, tc_read_functions);

    // /* Write Functions' tests */
    TCase *tc_write_functions;
    tc_write_functions = tcase_create("Write Tests");
    tcase_add_checked_fixture(tc_write_functions, tcase_default_setup, tcase_revert_changes_teardown);
    tcase_add_test(tc_write_functions, test_write_single_coil_wrong_value);
    tcase_add_test(tc_write_functions, test_write_single_coil_illegal_address);
    tcase_add_test(tc_write_functions, test_write_single_coil_func);
    tcase_add_test(tc_write_functions, test_write_single_reg_func);
    tcase_add_test(tc_write_functions, test_write_mult_coils_func);
    tcase_add_test(tc_write_functions, test_write_mult_reg_func);
    suite_add_tcase(s, tc_write_functions);

    return s;
}

int main(void)
{
    int number_failed;
    Suite *s;
    SRunner *sr;

    s = modbus_tcp_suite();
    sr = srunner_create(s);

    srunner_run_all(sr, CK_NORMAL);
    number_failed = srunner_ntests_failed(sr);
    srunner_free(sr);
    return (number_failed == 0) ? EXIT_SUCCESS : EXIT_FAILURE;
}