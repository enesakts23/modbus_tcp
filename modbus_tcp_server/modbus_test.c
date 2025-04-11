#include <modbus.h>
#include <modbus-tcp.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

int main() {
    modbus_t *mb;
    modbus_mapping_t *mb_mapping;
    int rc;
    int socket;

    // Modbus TCP bağlantısını başlatma
    mb = modbus_new_tcp("0.0.0.0", 502);
    if (mb == NULL) {
        fprintf(stderr, "Unable to create the libmodbus context\n");
        return -1;
    }

    // Modbus mapping (register'lar, coils, vb.)
    mb_mapping = modbus_mapping_new(10, 10, 10, 10);  // 10 coils, 10 holding registers
    if (mb_mapping == NULL) {
        fprintf(stderr, "Unable to allocate the mapping\n");
        modbus_free(mb);
        return -1;
    }

    // Coil (0x01) örneği
    mb_mapping->tab_bits[2] = 1;
    mb_mapping->tab_bits[3] = 1;
    mb_mapping->tab_bits[8] = 1;
    mb_mapping->tab_bits[9] = 1;

    // Discrete Input (0x02) örneği
    mb_mapping->tab_input_bits[0] = 1;  // İlk input "HIGH"
    mb_mapping->tab_input_bits[1] = 0;  // İkinci input "LOW"
    mb_mapping->tab_input_bits[2] = 1;  // Üçüncü input "HIGH"
    mb_mapping->tab_input_bits[6] = 1;  
    mb_mapping->tab_input_bits[7] = 1;  
    mb_mapping->tab_input_bits[9] = 1;  

    // Holding Register (0x03) örneği
    mb_mapping->tab_registers[0] = 0x1234;  
    mb_mapping->tab_registers[1] = 0x5678;  
    
    // Read Discrete Registers (0x04) örneği
    mb_mapping->tab_input_registers[2] = 0x9ABC; 
    mb_mapping->tab_input_registers[3] = 0xDEF1; 

    // Modbus TCP sunucusu için socket oluşturma
    socket = modbus_tcp_listen(mb, 1);
    if (socket == -1) {
        fprintf(stderr, "Unable to open socket\n");
        modbus_free(mb);
        return -1;
    }

    printf("Modbus TCP server is listening on port 502...\n");

    // Yeni bağlantıyı kabul etme
    int client_socket = modbus_tcp_accept(mb, &socket);
    if (client_socket == -1) {
        perror("Failed to accept client connection");
        modbus_mapping_free(mb_mapping);
        modbus_close(mb);
        modbus_free(mb);
        return -1;
    }

    while (1) {
        uint8_t query[MODBUS_TCP_MAX_ADU_LENGTH];

        // Gelen isteği alma
        rc = modbus_receive(mb, query);
        if (rc > 0) {
            modbus_reply(mb, query, rc, mb_mapping);
        } else if (rc == -1) {
            printf("Bağlantı kapandı, yeni istemci bekleniyor...\n");
            close(client_socket);
            client_socket = modbus_tcp_accept(mb, &socket);
            if (client_socket == -1) {
                perror("Yeni istemci kabul edilemedi");
                break;
            }
        }
    }

    // Kaynakları serbest bırakma
    modbus_mapping_free(mb_mapping);
    modbus_close(mb);
    modbus_free(mb);

    return 0;
}
