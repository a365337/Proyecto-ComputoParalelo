import socket
import multiprocessing
from multiprocessing import Lock

HOST = '0.0.0.0'
PORT = 80

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen(1)

addresses = []
lock = Lock()

def comandos(data, conn):
    try:
        if data == "GET_CLIENTES":
            data = str(addresses)
            conn.send(data.encode())
        else:
            conn.close()
    except Exception as e:
        print(f"Error: {e}")
        conn.close()

#Manejar mensajes entre clientes
def mensajes_clientes(m, conn, addr):
    try:
        if m:
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
            print(f"Se quita al cliente #{addresses.index(addr[1])}")
            addresses.remove(addr[1])
            break


def recibir_conexiones():
    while True:
        conn, addr = s.accept()
        
        # Por ahora solo se hace con puerto porque es local,
        # pero si quieren usar web se tiene que pasar la IP y el puerto.
        addresses.append(addr[1]) 
        print(f"Conexion Aceptada: {addr}")

        # No se juntan hilos, porque cuando se sale del while con el break
        # la función "manejar_conn" RETORNA, por lo que su función target
        # deja de servir y este de termina y destruye.
        multiprocessing.Process(target=manejar_conn, args=(addresses, addr, conn)).start()
        print(f"Procesos vivos: {multiprocessing.active_count()}")

recibir_conexiones()
