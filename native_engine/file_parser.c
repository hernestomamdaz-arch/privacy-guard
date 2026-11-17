#include <stdio.h>
#include <stdlib.h>

int verificar_cabecera_segura(const char* filepath) {
    FILE *file = fopen(filepath, "rb");
    if (!file) return -1;

    unsigned char buffer[4];
    size_t bytes_leidos = fread(buffer, 1, 4, file);
    fclose(file);

    if (bytes_leidos < 4) return 0;

    if (buffer[0] == 'M' && buffer[1] == 'Z') return 1; // Windows PE
    if (buffer[0] == 0x7F && buffer[1] == 'E' && buffer[2] == 'L' && buffer[3] == 'F') return 2; // Linux ELF
    
    return 0;
}
