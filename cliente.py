import socket
import threading
from threading import Lock
import time
import multiprocessing
import json

HOST = '0.0.0.0' 
# IP de donde esta el servidor corriendo, si lo quieres probar
# entre computadoras, pon la IP de la computadora donde esta el servidor
# y en la otra, si ahi estas corriendo el servidor ponlo con 0.0.0.0 para que
# se ponga automatico con su ip local
PORT = 80
cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
cliente.connect((HOST, PORT))
id_mensajero = cliente.getsockname()[1]

o = 0
lock = Lock()
lista_clientes = []

def recibir_server(conn):
    global lista_clientes
    try:
        with lock:
            data = conn.recv(1024).decode()
            if data:
                print(f"\n[Server]: {data}\n", end="")
                lista_clientes = data.strip("[]").replace(" ", "").split(",")
            else:
                conn.close()
    except Exception as e:
        print(f"Error: {e}")
        conn.close()

def get_clientes():
    cliente.send("GET_CLIENTES".encode())
    recibir_server(cliente)

# Funciones entre clientes. 
# -
def recibir_mensajes_clientes(conn):
    while True:
        try:
            data = conn.recv(1024).decode()
            if data:
                with lock:
                    print(f"\n{data}\n", end="")
            elif not data:
                raise Exception("Cliente desconectado")
        except Exception as e:
            print("Error al recibir mensajes: ", e)
            break

def mandar_mensaje(conn, id_receptor, id_mensajero):
    while True:
        try:
            data = input("Ingrese su mensaje: ")
            cadena_json = {
                "id_mensajero": id_mensajero,
                "id_receptor": id_receptor,
                "mensaje": data
            }

            conn.send(json.dumps(cadena_json).encode())
        
            print("Salir del chat? (s/n): ")
            salir = input()
            if salir == "s":
                break
        except Exception as e:
            print("Error al mandar mensajes: ", e)
            break
    
# -

while True:
    print(f"\n### Eres el cliente: {id_mensajero} ###\n")
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

        print("\nClientes disponibles:")
        with lock:
            for i,j in zip(range(len(lista_clientes)), lista_clientes):
                print(f"Cliente: {i} - {j}")

        # Solo por ahora porque es terminar, ya en web sera de otra manera
        # +
        try:
            id_receptor = int(input("Ingrese el id del cliente: ")) 
            # En web se puede llegar a seleccionar o no sé como lo quieras impelementar
            if str(id_receptor) not in lista_clientes:
                print("\nEl cliente no existe")
                continue
        except ValueError:
            print("\nEl cliente no existe")
            continue
        # +
        threading.Thread(target=recibir_mensajes_clientes, args=(cliente,), daemon=True).start()
        #threading.Thread(target=mandar_mensaje, args=(cliente, id_receptor, id_mensajero), daemon=True).start()
        mandar_mensaje(cliente, id_receptor, id_mensajero)


    elif o == 2:
        break
    
    
cliente.close()