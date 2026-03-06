import socket
import threading
from threading import Lock

HOST = 'localhost'
PORT = 65432

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen(1)

addresses = []
lock = Lock()

def mensaje(m, conn, addr):
    try:
        if m == "clientes":
            lock.acquire()
            data = str(addresses)
            conn.send(data.encode("utf-8"))
            lock.release()

        elif m:
            lock.acquire()
            print(f"\nCliente #{addresses.index(addr[1])}: {m}\n")
            lock.release()
            
    except Exception as e:
        print("Error al recibir el mensaje: ", e)

def manejar_conn(addresses, addr, conn):
    while True:
        try:
            data = conn.recv(1024)
            if not data:
                raise Exception("Cliente desconectado")
            mensaje(data.decode('utf-8'), conn, addr)
        except:
            print(f"Se quita al cliente #{addresses.index(addr[1])}")
            addresses.remove(addr[1])
            break


def recibir_conexiones():
    while True:
        conn, addr = s.accept()
        lock.acquire()
        addresses.append(addr[1])
        print(f"Conexion Aceptada: {addr}")
        lock.release()
        
        threading.Thread(target=manejar_conn, args=(addresses, addr, conn)).start()
        print(f"Hilos vivos: {threading.active_count()}")

recibir_conexiones()
