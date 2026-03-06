import socket
import threading
from threading import Lock

HOST = 'localhost'
PORT = 65432
cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
cliente.connect((HOST, PORT))

def recibir(conn, lock):
    while True:
        try:
            data = conn.recv(1024)
            if data:
                print(f"\nServer: {data.decode('utf-8')}\n", end="")
            else:
                conn.close()
                break
        except Exception as e:
            print(f"Error: {e}")
            conn.close()
            break
    
o = 0
lock = Lock()
while True:

    lock.acquire()
    print("Seleccione una opción:\n")
    print("1) Mandar mensajes\n")
    print("2) Mostrar conectados\n  ")
    print("3) Salir\n")
    lock.release()
    try:
        o = int(input("Ingrese una opción: "))
        #lock.release()
    except ValueError:
        print("\nIngrese un número válido")
        continue

    if o == 1:
        data = input("Ingrese un mensaje: ")
        cliente.send(data.encode("utf-8"))
        threading.Thread(target=recibir, args=(cliente,lock)).start()
    elif o == 2:
        data = "clientes"
        cliente.send(data.encode("utf-8"))
        threading.Thread(target=recibir, args=(cliente,lock)).start()
    elif o == 3:
        break
    
cliente.close()
    