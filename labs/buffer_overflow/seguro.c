#include <stdio.h>
#include <string.h>

void procesar_nombre(char *nombre) {
    char buffer[10];
    
    // Usamos strncpy limitando el tamaño al del búfer - 1
    // El -1 es para dejar espacio al carácter nulo '\0' que marca el fin del texto
    strncpy(buffer, nombre, sizeof(buffer) - 1);
    
    // Nos aseguramos de que el búfer termine en '\0'
    buffer[sizeof(buffer) - 1] = '\0';
    
    printf("Nombre procesado de forma segura: %s\n", buffer);
}

int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("Uso: %s <tu_nombre>\n", argv[0]);
        return 1;
    }
    procesar_nombre(argv[1]);
    return 0;
}
