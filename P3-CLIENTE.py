import socket

HOST = input("Introduce la IP del servidor: ")
PORT = int(input("Introduce el puerto: "))
buffer_size = 1024

try:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as TCPClientSocket:
        TCPClientSocket.connect((HOST, PORT))
        print("Conexión establecida con el servidor.")

        # Escuchar mensaje inicial (símbolo y confirmación de turno)
        data = TCPClientSocket.recv(buffer_size).decode()
        print(data)

        # Ciclo de juego
        while True:
            data = TCPClientSocket.recv(buffer_size).decode()
            if not data:
                print("El servidor cerró la conexión.")
                break

            # Muestra cualquier mensaje recibido del servidor
            print(data)

            # Solo pide el movimiento si es el turno del jugador
            if "Es tu turno" in data:
                movimiento = input("")
                TCPClientSocket.sendall(movimiento.encode())

            # Condición de finalización
            if "Ganaste" in data or "Perdiste" in data or "Empate" in data:
                print("Juego finalizado.")
                break

except ConnectionResetError:
    print("Conexión con el servidor cerrada inesperadamente.")
except Exception as e:
    print(f"Ocurrió un error: {e}")