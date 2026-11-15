#include <stdio.h>
#include <string.h>

void procesar_nombre(char *nombre) {
    // ¡PELIGRO! Búfer de solo 10 bytes
    char buffer[10];
    
    // strcpy no verifica el tamaño, copia lo que sea.
    // Si 'nombre' es más largo de 10 caracteres, sobreescribe la memoria.
    strcpy(buffer, nombre); 
    
    printf("Nombre procesado: %s\n", buffer);
}

int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("Uso: %s <tu_nombre>\n", argv[0]);
        return 1;
    }
    // Pasamos el argumento a la función vulnerable
    procesar_nombre(argv[1]);
    return 0;
}
