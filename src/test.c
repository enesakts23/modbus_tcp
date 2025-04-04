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
    Additional info will be added to README.md
*/
#define _GNU_SOURCE

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "modbus.h"
#include <check.h>

uint8_t pdu_buffer[MODBUS_RECEIVE_MAX_DATA_SIZE];
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

/*****************************************************************************/
/* This will test send_read_req function with illegal function*/
START_TEST(test_read_req_illegal_function)
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
    
    while((ret_val = receive_read_response(pdu_buffer, &data_length)) == MODBUS_RESPONSE_NO_ANSWER_YET)
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

    while((ret_val = receive_read_response(pdu_buffer, &data_length)) == MODBUS_RESPONSE_NO_ANSWER_YET)
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
    ck_assert_int_eq((int)pdu_buffer[0], (int)0x0D);
    ck_assert_int_eq((int)pdu_buffer[1], (int)0x03);
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

    while((ret_val = receive_read_response(pdu_buffer, &data_length)) == MODBUS_RESPONSE_NO_ANSWER_YET)
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
    ck_assert_int_eq((int)pdu_buffer[0], (int)0xC5);
    ck_assert_int_eq((int)pdu_buffer[1], (int)0x02);

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

    while((ret_val = receive_read_response(pdu_buffer, &data_length)) == MODBUS_RESPONSE_NO_ANSWER_YET)
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

    /* Birleştirme olursa 20 değil de 10 olarak kullanılabilir bunlar da.*/
    ck_assert_int_eq((int)data_length, (int)20);

    /* These values come from server code. */ 
    /* We can merge those 2 bytes. */
    ck_assert_int_eq((int)pdu_buffer[0], (int)0x12);
    ck_assert_int_eq((int)pdu_buffer[1], (int)0x34);
    ck_assert_int_eq((int)pdu_buffer[2], (int)0x56);
    ck_assert_int_eq((int)pdu_buffer[3], (int)0x78);
    
    /* Bu bir denemedir kalıcı eklenebilir düşünmek lazım. */
    uint16_t value;
    value = ((uint16_t)pdu_buffer[0] << 8 ) + (uint16_t) pdu_buffer[1];
    ck_assert_int_eq((int)value, (int)0x1234);
    value = ((uint16_t)pdu_buffer[2] << 8 ) + (uint16_t) pdu_buffer[3];
    ck_assert_int_eq((int)value, (int)0x678);

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
    tcase_add_test(tc_read_functions, test_read_coils_func);
    tcase_add_test(tc_read_functions, test_read_req_illegal_function);
    tcase_add_test(tc_read_functions, test_read_illegal_address);
    tcase_add_test(tc_read_functions, test_read_discrete_inputs_func);
    tcase_add_test(tc_read_functions, test_read_holding_registers_func);
    suite_add_tcase(s, tc_read_functions);

    // /* Get Functions' tests */
    // TCase *tc_get;
    // tc_get = tcase_create("Get Tests");
    // tcase_add_checked_fixture(tc_get, tcase_fill_list_setup, tcase_default_teardown);
    // tcase_add_test(tc_get, test_get_tail);
    // tcase_add_test(tc_get, test_get_head);
    // tcase_add_test(tc_get, test_get_with_index);
    // tcase_add_test(tc_get, test_get_index_with_compare_func);
    // suite_add_tcase(s, tc_get);

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