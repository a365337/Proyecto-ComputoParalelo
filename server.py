import socket
import threading
from threading import Lock
import json

HOST = '0.0.0.0'
PORT = 80

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen(1)

connexiones = {}
lock = Lock()

def comandos(data, conn):
    try:
        if data == "GET_CLIENTES":
            with lock:
                data = str([k for k in connexiones.keys()])
                conn.send(data.encode())
        else:
            conn.close()
    except Exception as e:
        print(f"Error: {e}")
        conn.close()

#Manejar mensajes entre clientes
def mensajes_clientes(m, conn, addr):
    try:
        m = json.loads(m)
        id_mensajero = m["id_mensajero"]
        id_receptor = m["id_receptor"]
        mensaje = m["mensaje"]
        with lock:
            connexiones[id_receptor].send(f"Cliente #{id_mensajero}: {mensaje}".encode())
    except Exception as e:
        with lock:
            connexiones.pop(id_receptor)
        conn.close()
        print("Error al recibir el mensaje: ", e)

def manejar_conn(connexiones, conn, addr):
    while True:
        try:
            data = conn.recv(1024)
            if not data: 
            # No recibe bits en conn.recv, por lo que lanza la exception para que entre en "except"
            # y se elimine en la lista de los clientes conectados
                raise Exception("Cliente desconectado")
            elif data.decode() == "GET_CLIENTES":
                #Se hace en diferentes if para que reconozca entre mensaje, comando o que ya no hay dato
                #para la desconexión o mandar el mensaje correcto.
                comandos(data.decode(), conn)
            else:
                mensajes_clientes(data.decode(), conn, addr)
        except:
            print(f"Se quita al cliente #{addr[1]}")
            with lock:
                connexiones.pop(addr[1])
            break


def recibir_conexiones():
    while True:
        conn, addr = s.accept()
        
        # Por ahora solo se hace con puerto porque es local,
        # pero si quieren usar web se tiene que pasar la IP y el puerto.
        with lock:
            connexiones[addr[1]] = (conn)
            print(f"Conexion Aceptada: {addr[1]}")

        # No se juntan hilos, porque cuando se sale del while con el break
        # la función "manejar_conn" RETORNA, por lo que su función target
        # deja de servir y este de termina y destruye.
        threading.Thread(target=manejar_conn, args=(connexiones, conn, addr)).start()
        print(f"Hilos vivos: {threading.active_count()}")

recibir_conexiones()
