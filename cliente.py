import socket
import threading
import queue
import json
import customtkinter as ctk

HOST = '127.0.0.1'  #Por mientras local jjeje xd lol
PORT = 12345

cliente = None   # Socket del cliente
mi_puerto = None   # Puerto local asignado automáticamente
mi_nombre = ""     # Nombre que eligió el usuario
lista_clientes = {}     # { puerto_str: nombre } — se actualiza con GET_CLIENTES
receptor_actual = None   # Puerto (int) del cliente al que se le escribe ahora

# Cola thread-safe para pasar mensajes desde hilos secundarios al hilo principal.
# NUNCA se puede tocar un widget desde
# un hilo secundario, hacerlo causa crashes. La solución es:
# hilo de red  ->  escribe en cola ->  hilo principal lee la cola con .after()
cola_mensajes = queue.Queue()


#Aqui llega login para hacer la conexión, y si es exitosa se abre la ventana del chat
def conectar(nombre):
    #Abre el socket TCP, se conecta al servidor y envía el nombre de usuario
    #como primer mensaje para que el servidor lo registre.
    #Devuelve True si tuvo éxito, False si falló.
    global cliente, mi_puerto, mi_nombre
    try:
        #saco los datos de la maquina que corre el cliente 
        cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cliente.connect((HOST, PORT))
        mi_puerto = cliente.getsockname()[1]
        mi_nombre = nombre

        #El servidor espera el nombre como primer mensaje
        cliente.send(nombre.encode())
        return True
    except Exception as e:
        return False


#Recepcion de mensajes (hilo separado) 
def recibir_mensajes():
    #Cada dato que llega trae un prefijo que indica su tipo:
    #  MSG: mensaje de chat (se muestra en el área de conversación)
    #  LIST: respuesta a GET_CLIENTES (JSON con la lista de usuarios)
    #  SYS: aviso del servidor (conexión, desconexión, errores)
    #Separar por prefijo resuelve el bug donde get_clientes() y recibir_mensajes()
    #competían por el mismo dato o accedian al mismo tiempo y se "robaban" los datos el uo al otrp
    
    while True:
        try:
            data = cliente.recv(1024).decode()
            if not data:
                cola_mensajes.put("SYS:Conexión cerrada por el servidor.")
                break

            if data.startswith("MSG:"):
                #Mensaje de chat: mostrarlo en pantalla
                cola_mensajes.put(data[4:])

            elif data.startswith("LIST:"):
                #Respuesta a GET_CLIENTES: actualizar lista lateral
                global lista_clientes
                lista_clientes = json.loads(data[5:])
                cola_mensajes.put("__ACTUALIZAR_LISTA__")

            elif data.startswith("SYS:"):
                #Aviso del servidor: mostrarlo como mensaje de sistema
                cola_mensajes.put(f"[Servidor] {data[4:]}")

            else:
                # ato sin prefijo (no debería ocurrir, pero por si acaso)
                cola_mensajes.put(data)

        except Exception as e:
            cola_mensajes.put(f"[Sistema] Error de conexión: {e}")
            break


#Logica para el boton de actualizar 
def get_clientes():
    #Solo envía el comando GET_CLIENTES al servidor.
    #La respuesta (LIST:...) llega por recibir_mensajes() que la interpreta
    try:
        cliente.send("GET_CLIENTES".encode())
    except Exception as e:
        cola_mensajes.put(f"[Sistema] Error al pedir clientes: {e}")


#ENVIAR MENSAJE
def enviar_mensaje():
    #Lee el campo de texto, construye el JSON y lo envía al servidor
    #Si no hay receptor seleccionado, envía broadcast (o sea a todos)
    global receptor_actual
    texto = entry_mensaje.get().strip()
    if not texto:
        return

    id_receptor = str(receptor_actual) if receptor_actual else "todos"

    payload = {
        "id_mensajero":    mi_puerto,
        "id_receptor":     id_receptor,
        "mensaje":         texto,
        "nombre_mensajero": mi_nombre
    }

    try:
        cliente.send(json.dumps(payload).encode())
        #Mostrar el propio mensaje en pantalla (el servidor no nos lo reenvía)
        destino = lista_clientes.get(str(receptor_actual), "Todos") if receptor_actual else "Todos"
        mostrar_mensaje(f"[Tú → {destino}] {texto}")
        entry_mensaje.delete(0, "end")
    except Exception as e:
        mostrar_mensaje(f"[Sistema] Error al enviar: {e}")


#Logica de la interfaz para mostrar mensaje
def mostrar_mensaje(texto):
    #Inserta una línea en el área de texto del chat.
    #Esta función SOLO se llama desde el hilo principal (vía procesar_cola),
    #por lo que ya no necesita lock 
    chat_box.configure(state="normal")
    chat_box.insert("end", texto + "\n")
    chat_box.configure(state="disabled")
    chat_box.see("end") 


#Logica de la interfaz para actualizar lista de clientes
def actualizar_lista_ui():
    #Refresca el listbox lateral con los clientes conectados.
    #Excluye al propio usuario de la lista, pero si quieren se puede mostrar tambien 
    lista_box.configure(state="normal")
    lista_box.delete("1.0", "end")

    lista_box.insert("end", "── Conectados ──\n")
    for puerto, nombre in lista_clientes.items():
        if int(puerto) == mi_puerto:
            continue  #Para no mostrarse a sí mismo
        lista_box.insert("end", f"▸ {nombre} ({puerto})\n")

    lista_box.insert("end", "\n[Todos]\n")  #Opción de broadcast siempre visible
    lista_box.configure(state="disabled")


#La logica de seleccionar el receptor al hacer click en la lista lateral, y mostrar a quién se le va a escribir
def seleccionar_receptor(event):
    #Si se elige "[Todos]", el receptor se pone en None (broadcast).
    global receptor_actual
    try:
        index = lista_box.index("@%d,%d" % (event.x, event.y))
        linea = lista_box.get(index + " linestart", index + " lineend").strip()

        if "[Todos]" in linea:
            receptor_actual = None
            label_receptor.configure(text="Enviando a: Todos")
        elif "▸" in linea:
            #Extraer el puerto del formato ▸ Nombre (puerto)"
            puerto_str = linea.split("(")[-1].replace(")", "").strip()
            receptor_actual = int(puerto_str)
            nombre = lista_clientes.get(puerto_str, puerto_str)
            label_receptor.configure(text=f"Enviando a: {nombre}")
    except Exception:
        pass


#primera ventanita, usuario ingresa su nombre, y si se conecta se abre la ventana del chat
#y se cierra esta, en dado caso que haya error, se queda en esta y lo muestra 
def pantalla_login():
    # se crea la ventana de login
    login = ctk.CTk()
    login.title("Chat — Conectar")
    login.geometry("360x240")
    login.resizable(False, False)

    ctk.CTkLabel(login, text="Bienvenido al Chat", font=("Arial", 18, "bold")).pack(pady=20)
    ctk.CTkLabel(login, text="Ingresa tu nombre:").pack()

    entry_nombre = ctk.CTkEntry(login, placeholder_text="Tu nombre...", width=220)
    entry_nombre.pack(pady=8)

    label_error = ctk.CTkLabel(login, text="", text_color="red")
    label_error.pack()

    def intentar_conexion():
        nombre = entry_nombre.get().strip()
        if not nombre:
            label_error.configure(text="El nombre no puede estar vacío.")
            return
        if conectar(nombre):
            login.destroy()
            pantalla_chat()  #Abre la ventana del chat principl
        else:
            label_error.configure(text=f"No se pudo conectar a {HOST}:{PORT}")

    ctk.CTkButton(login, text="Conectar", command=intentar_conexion).pack(pady=10)

    #También conectar con Enter
    entry_nombre.bind("<Return>", lambda e: intentar_conexion())

    login.mainloop()


#Pantalla principal del chat, con la lista de clientes conectados a la izquierda, 
#el historial de mensajes a la derecha y el campo de texto para escribir abajo
def pantalla_chat():
    #Se declaran como globales porque otras funciones tambien las usaran para escribir/leer
    global chat_box, entry_mensaje, lista_box, label_receptor

    ventana = ctk.CTk()
    ventana.title(f"Chat — {mi_nombre} (puerto {mi_puerto})")
    ventana.geometry("800x520")

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    #La app se dividira en dos columnas principales
    ventana.grid_columnconfigure(0, weight=1)   #Columna lista 
    ventana.grid_columnconfigure(1, weight=4)   #Columna chat (expandible)
    ventana.grid_rowconfigure(0, weight=1)

    #Panel izquierdo, es la lista de clientes conectados
    frame_lista = ctk.CTkFrame(ventana, width=180)
    frame_lista.grid(row=0, column=0, sticky="nsew", padx=(8, 4), pady=8)

    ctk.CTkLabel(frame_lista, text="Contactos", font=("Arial", 13, "bold")).pack(pady=(8, 4))

    lista_box = ctk.CTkTextbox(frame_lista, state="disabled", width=160, wrap="word")
    lista_box.pack(fill="both", expand=True, padx=4, pady=4)
    lista_box.bind("<Button-1>", seleccionar_receptor)  #Si hacemos click, se seleccionara ese cliente para enviarle mensajes privados

    #Botón para refrescar la lista de clientes conectados
    ctk.CTkButton(
        frame_lista, text="⟳ Actualizar",
        command=lambda: threading.Thread(target=get_clientes, daemon=True).start()
    ).pack(pady=(4, 8))

    #Panel derecho, el mero mole el chat
    frame_chat = ctk.CTkFrame(ventana)
    frame_chat.grid(row=0, column=1, sticky="nsew", padx=(4, 8), pady=8)
    frame_chat.grid_rowconfigure(0, weight=1)
    frame_chat.grid_columnconfigure(0, weight=1)

    #Área de mensajes (solo lectura para el usuario)
    chat_box = ctk.CTkTextbox(frame_chat, state="disabled", wrap="word")
    chat_box.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=8, pady=(8, 4))

    #Indicador de a quién se le está escribiendo
    label_receptor = ctk.CTkLabel(frame_chat, text="Enviando a: Todos", anchor="w", text_color="gray")
    label_receptor.grid(row=1, column=0, columnspan=2, sticky="w", padx=10)

    #Campo de texto para escribir
    entry_mensaje = ctk.CTkEntry(frame_chat, placeholder_text="Escribe un mensaje...", height=36)
    entry_mensaje.grid(row=2, column=0, sticky="ew", padx=(8, 4), pady=8)
    entry_mensaje.bind("<Return>", lambda e: enviar_mensaje())  # Enter para enviar

    ctk.CTkButton(frame_chat, text="Enviar", width=80, command=enviar_mensaje).grid(
        row=2, column=1, padx=(0, 8), pady=8
    )

    #Mensaje de bienvenida local
    mostrar_mensaje(f"[Sistema] Conectado como '{mi_nombre}' en puerto {mi_puerto}.")
    mostrar_mensaje("[Sistema] Usa 'Actualizar' para ver quién está conectado y haz clic en un nombre para chatear.")

    #Loop que vacía la cola de mensajes desde el hilo principal
    #ventana.after se pospone para ejecutarse en el hilo principal
    #Al final de cada llamada se re-agenda a sí misma
    def procesar_cola():
        try:
            while True:                          #vaciar todo lo que haya en la cola
                item = cola_mensajes.get_nowait()
                if item == "__ACTUALIZAR_LISTA__":
                    actualizar_lista_ui()        
                else:
                    mostrar_mensaje(item)        #texto normal -> mostrarlo en chat
        except queue.Empty:
            pass                                 #cola vacía, no pasa nada
        ventana.after(100, procesar_cola)        #re-agendar para el siguiente tick

    ventana.after(100, procesar_cola)            #arrancar el loop

    #Lanzar hilo de escucha de mensajes entrantes
    threading.Thread(target=recibir_mensajes, daemon=True).start()

    #Cargar lista inicial de clientes
    threading.Thread(target=get_clientes, daemon=True).start()

    #Al cerrar la ventana, cerrar también el socket
    def al_cerrar():
        try:
            cliente.close()
        except Exception:
            pass
        ventana.destroy()

    ventana.protocol("WM_DELETE_WINDOW", al_cerrar)
    ventana.mainloop()

if __name__ == "__main__":
    pantalla_login()