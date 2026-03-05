import socket
import threading

HOST = 'localhost'
PORT = 65432

def mensaje(conn):
    while True:
        try:
            data = conn.recv(1024)
            if data:
                print(f"\nCliente #{addr[1]}: {data.decode('utf-8')}\nIngrese un mensaje: ", end="")
            else:
                break
        except Exception as e:
            print("Error al recibir el mensaje: ", e)
            break

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    print("Esperando conexion...")
    conn, addr = s.accept()

    t1 = threading.Thread(target=mensaje, args=(conn,), daemon=True)
    t1.start()

    while True:
        data = input("Ingrese un mensaje: ")
        conn.send(data.encode("utf-8"))
