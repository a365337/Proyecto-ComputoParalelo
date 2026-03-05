import socket
import threading

HOST = 'localhost'
PORT = 65432
cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
cliente.connect((HOST, PORT))

def recibir(conn):
    while True:
        try:
            data = conn.recv(1024)
            if data:
                print(f"\nServer: {data.decode('utf-8')}\nIngrese un mensaje: ", end="")
            else:
                break
        except Exception as e:
            print(e)
            break
    

while True:
    data = input("Ingrese un mensaje: ")
    cliente.send(data.encode("utf-8"))
    threading.Thread(target=recibir, args=(cliente,)).start()