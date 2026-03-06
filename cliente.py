import socket
import threading
from threading import Lock
import time

HOST = '0.0.0.0'
PORT = 80
cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
cliente.connect((HOST, PORT))

def recibir(conn):
    try:
        lock.acquire()
        data = conn.recv(1024)
        if data:
            print(f"\n[Server]: {data.decode()}\n", end="")
        else:
            conn.close()
    except Exception as e:
        print(f"Error: {e}")
        conn.close()
    finally:
        lock.release()
    
o = 0
lock = Lock()

def get_clientes():
    cliente.send("GET_CLIENTES".encode())
    

while True:
    
    print("Seleccione una opción:\n")
    print("1) Mensajeria\n")
    print("2) Salir\n")

    try:
        o = int(input("Ingrese una opción: "))
    except ValueError:
        print("\nIngrese un número válido")
        continue

    if o == 1:
        get_clientes()
        recibir(cliente)
        data = input("Ingrese un mensaje: ")
        cliente.send(data.encode("utf-8"))
    elif o == 2:
        break
    
    
cliente.close()