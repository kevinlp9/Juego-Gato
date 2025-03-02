import socket
import threading
from threading import Event, Semaphore

# Configuración inicial
HOST = input("Introduce la IP en la que el servidor escuchará: ")
PORT = int(input("Introduce el puerto: "))
buffer_size = 1024

# Funciones del tablero
def crear_tablero_con_coordenadas(m, n):
    return [[' ' for _ in range(n)] for _ in range(m)]

def imprimir_tablero_con_coordenadas(tablero):
    coordenadas_columnas = "  " + "   ".join(str(i) for i in range(len(tablero[0])))
    filas = [f"{i} | " + " | ".join(tablero[i]) + " |" for i in range(len(tablero))]
    return coordenadas_columnas + "\n" + "\n".join(filas)

def verificar_ganador(tablero, k, jugador):
    for i in range(len(tablero)):
        for j in range(len(tablero[i])):
            if j <= len(tablero[i]) - k and all(tablero[i][j + x] == jugador for x in range(k)):
                return True
            if i <= len(tablero) - k and all(tablero[i + x][j] == jugador for x in range(k)):
                return True
    return False

def verificar_empate(tablero):
    return all(celda != ' ' for fila in tablero for celda in fila)

# Variables de juego
simbolos = ['X', 'O', 'A', 'B', 'C']
tablero = crear_tablero_con_coordenadas(5, 5)
clientes = {}
turno_actual = 0
num_jugadores = 2
inicio_juego = Event()

# Semáforos para turnos
semaforos = []

def manejar_cliente(conn, addr, jugador_id):
    global turno_actual, tablero, clientes

    simbolo = simbolos[jugador_id]
    conn.sendall(f"Conectado como jugador '{simbolo}'. Espera a que el juego inicie.\n".encode())
    inicio_juego.wait()  # Espera a que el juego comience

    try:
        while True:
            # Espera a que el semáforo de este jugador esté disponible
            semaforos[jugador_id].acquire()

            conn.sendall(b"Es tu turno. Ingresa tu movimiento (fila,columna): ")
            data = conn.recv(buffer_size).decode().strip()
            if not data:
                raise ConnectionResetError
            try:
                fila, columna = map(int, data.split(","))
            except ValueError:
                conn.sendall(b"Formato invalido. Usa fila,columna.\n")
                semaforos[jugador_id].release()
                continue

            if 0 <= fila < len(tablero) and 0 <= columna < len(tablero[0]) and tablero[fila][columna] == ' ':
                tablero[fila][columna] = simbolo
                if verificar_ganador(tablero, 5, simbolo):
                    notificar_a_todos(f"¡Jugador '{simbolo}' ha ganado!\n")
                    cerrar_conexiones()
                    return
                if verificar_empate(tablero):
                    notificar_a_todos("El juego ha terminado en empate.\n")
                    cerrar_conexiones()
                    return
                
                # Cambiar al siguiente turno
                turno_actual = (turno_actual + 1) % len(clientes)
                actualizar_y_notificar_clientes()
                # Libera el semáforo del siguiente jugador
                semaforos[turno_actual].release()
            else:
                conn.sendall(b"Movimiento invalido. Intenta de nuevo.\n")
                semaforos[jugador_id].release()
    except (ConnectionResetError, BrokenPipeError):
        print(f"Cliente {addr} desconectado.")
        clientes.pop(conn, None)
        if conn in semaforos:
            semaforos.remove(conn)

def actualizar_y_notificar_clientes():
    mensaje = imprimir_tablero_con_coordenadas(tablero).encode()
    for conn in list(clientes.keys()):
        try:
            conn.sendall(mensaje)
        except (ConnectionResetError, BrokenPipeError):
            pass

def notificar_a_todos(mensaje):
    for conn in list(clientes.keys()):
        try:
            conn.sendall(mensaje.encode())
        except (ConnectionResetError, BrokenPipeError):
            pass

def cerrar_conexiones():
    for conn in list(clientes.keys()):
        conn.close()
    print("Juego terminado. Todas las conexiones cerradas.")

def aceptar_conexiones():
    global num_jugadores, semaforos
    num_jugadores = int(input("Ingresa el número de jugadores: "))

    # Crear un semáforo para cada jugador
    semaforos = [Semaphore(0) for _ in range(num_jugadores)]

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as TCPServerSocket:
        TCPServerSocket.bind((HOST, PORT))
        TCPServerSocket.listen()
        print("Servidor TCP disponible y esperando conexiones")

        while len(clientes) < num_jugadores:
            conn, addr = TCPServerSocket.accept()
            jugador_id = len(clientes)
            clientes[conn] = simbolos[jugador_id]
            print(f"Conectado a {addr} como jugador {simbolos[jugador_id]}")
            thread = threading.Thread(target=manejar_cliente, args=(conn, addr, jugador_id))
            thread.start()

        # Una vez que se conecten todos los jugadores, inicia el juego
        print("Todos los jugadores conectados. ¡Inicia el juego!")
        inicio_juego.set()

        # Liberar el semáforo del primer jugador
        semaforos[0].release()

if __name__ == "__main__":
    aceptar_conexiones()
