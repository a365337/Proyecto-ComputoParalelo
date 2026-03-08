import socket
import threading
from threading import Lock
import json

HOST = '0.0.0.0'
PORT = 12345  

#Socket del servidor con TCP (AF_INET = IPv4, SOCK_STREAM = TCP)
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Permite reutilizar el puerto inmediatamente después de cerrar el servidor
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((HOST, PORT))
s.listen(10)  #de 1 a 10 para que permita más conexiones en cola simultaneamente

#Diccionario en vez de lista, para que se identifique mediante puerto y nombre en ez de solo puerto 
#algo asi queda: { puerto: {"conn": socket, "nombre": str} }
connexiones = {}
lock = Lock()  


#Chat general
def broadcast(mensaje, excluir_puerto=None):
    
    with lock:
        for puerto, datos in list(connexiones.items()):
            if puerto == excluir_puerto:
                continue
            try:
                datos["conn"].send(mensaje.encode())
            except Exception:
                pass

#Aqui se hace la logica de actualizar la cantidad de usuarios conectados
#Para el tema de escalabilidad, aqui se podrian ir agregando funciones nuevas
#y se aplicaria la logica dependiendo de cual sea el prefijo que se le ponga al mensaje
def comandos(data, conn):
    try:
        if data == "GET_CLIENTES":
            with lock:
                clientes = {str(p): d["nombre"] for p, d in connexiones.items()}
            #Prefijo LIST para que el cliente sepa que es la lista de usuarios conectados
            conn.send(("LIST:" + json.dumps(clientes)).encode())
        else:
            conn.close()
    except Exception as e:
        print(f"[Servidor] Error en comando: {e}")
        conn.close()


#MENSAJES ENTRE CLIENTES
#Espera JSON con: id_mensajero, id_receptor, mensaje, nombre_mensajero
#Si id_receptor == "todos", sgnifica q es mensaje para todos 
def mensajes_clientes(data_raw, conn, addr):
    try:
        m = json.loads(data_raw)
        id_mensajero  = m["id_mensajero"]
        id_receptor = m["id_receptor"]
        mensaje = m["mensaje"]
        #para esto el diccionario
        nombre = m.get("nombre_mensajero", f"Cliente#{id_mensajero}")

        texto = f"{nombre}: {mensaje}"

        if id_receptor == "todos":
            #Prefijo MSG: para que el cliente sepa que es un mensaje de chat
            #y el excluir_puerto evita que el mensaje se envíe de vuelta al que envio el mensaje
            broadcast(f"MSG:[Todos] {texto}", excluir_puerto=addr[1])
        else:
            id_receptor_int = int(id_receptor)
            with lock:
                if id_receptor_int in connexiones:
                    #Mensaje privado con prefijo MSG:
                    connexiones[id_receptor_int]["conn"].send(f"MSG:[Privado] {texto}".encode())
                else:
                    #Aviso del sistema con prefijo SYS:
                    conn.send("SYS:El destinatario no está conectado.".encode())
    except Exception as e:
        print(f"[Servidor] Error al rutear mensaje: {e}")


#Logica para manejar cada cliente, usando un hilo para cada uno
def manejar_conn(conn, addr):
    #El primer mensaje que manda el cliente es su nombre de usuario
    
    nombre_raw = conn.recv(1024).decode().strip()
    #operador ternario para asignar un nombre por defecto si el cliente no envía uno o envía uno vacío
    #tqm pithon <3
    nombre = nombre_raw if nombre_raw else f"Cliente#{addr[1]}"
 
    #Registrar cliente en el diccionario compartido
    with lock:
        connexiones[addr[1]] = {"conn": conn, "nombre": nombre}

    print(f"[Servidor] '{nombre}' conectado (puerto {addr[1]}). Hilos activos: {threading.active_count()}")

    #Avisar a todos que entró un nuevo usuario — prefijo SYS: para avisos
    broadcast(f"SYS:'{nombre}' se unió al chat.", excluir_puerto=addr[1])

    while True:
        try:
            data = conn.recv(1024)

            if not data:
                #si no hay nada pues se fue el cliente 
                raise ConnectionResetError("Cliente desconectado")

            decoded = data.decode()

            if decoded == "GET_CLIENTES":
                comandos(decoded, conn)
            else:
                mensajes_clientes(decoded, conn, addr)

        except Exception as e:
            #Cualquier error de red o desconexión limpia al cliente del dict
            print(f"[Servidor] '{nombre}' desconectado: {e}")
            with lock:
                connexiones.pop(addr[1], None)  #pop con default evita KeyError al parecer
            broadcast(f"SYS:'{nombre}' salió del chat.")
            conn.close()
            break  


#LOOP PRINCIPAL 
def recibir_conexiones():
    print(f"[Servidor] Escuchando en {HOST}:{PORT}...")
    while True:
        try:
            conn, addr = s.accept()
            #Lanzar hilo para este cliente (el dict se llena dentro de manejar_conn
            #para evitar registrar sin nombre)
            #el lock se usa despues para proteger el acceso al dict de conexiones
            threading.Thread(
                target=manejar_conn,
                args=(conn, addr),
                daemon=True   
            ).start()
        except Exception as e:
            print(f"[Servidor] Error aceptando conexión: {e}")


if __name__ == "__main__":
    recibir_conexiones()