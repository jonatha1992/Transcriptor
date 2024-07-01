import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import speech_recognition as sr
import threading
from pydub import AudioSegment
from pydub.utils import which
from googletrans import Translator
import logging

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    filename="transcriptor.log",
    filemode="w",
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Inicializar el reconocedor y el traductor
recognizer = sr.Recognizer()
translator = Translator()

# Variable global para controlar el estado de la transcripción
transcripcion_activa = False

# Asegurarse de que pydub encuentra ffmpeg y ffprobe
AudioSegment.converter = which("ffmpeg")
AudioSegment.ffprobe = which("ffprobe")


# Función para convertir audio a WAV
def convertir_a_wav(audio_path):
    try:
        audio_format = audio_path.split(".")[-1]
        audio = AudioSegment.from_file(audio_path, format=audio_format)
        wav_path = audio_path.replace(audio_format, "wav")
        audio.export(wav_path, format="wav")
        logging.info(f"Archivo convertido a WAV: {wav_path}")
        return wav_path
    except Exception as e:
        logging.error(f"Error al convertir archivo a WAV: {e}")
        raise


# Función para transcribir archivos WAV
def transcribir_archivo(audio_path, idioma_entrada):
    try:
        with sr.AudioFile(audio_path) as source:
            audio = recognizer.record(source)
            text = recognizer.recognize_google(audio, language=idioma_entrada)
            logging.info(f"Transcripción inicial: {text}")
            return text
    except sr.UnknownValueError:
        logging.warning("Audio no claro / inaudible.")
        return "Audio no claro / inaudible."
    except sr.RequestError as e:
        logging.error(f"Error en el servicio de reconocimiento: {e}")
        return f"Error en el servicio de reconocimiento: {e}"
    except Exception as e:
        logging.error(f"Error al procesar el archivo: {e}")
        return f"Error al procesar el archivo: {e}"


# Función para traducir texto
def traducir_texto(texto, idioma_salida):
    try:
        traduccion = translator.translate(texto, dest=idioma_salida)
        logging.info(f"Texto traducido: {traduccion.text}")
        return traduccion.text
    except Exception as e:
        logging.error(f"Error al traducir texto: {e}")
        return f"Error al traducir texto: {e}"


# Función para seleccionar archivos de audio
def seleccionar_archivos():
    file_paths = filedialog.askopenfilenames(
        filetypes=[("Archivos de Audio", "*.wav *.mp3 *.flac *.ogg *.m4a")],
        title="Seleccionar archivos de audio",
    )
    archivos_no_agregados = []
    if file_paths:
        for file_path in file_paths:
            file_name = os.path.basename(file_path)
            if file_name not in lista_archivos.get(0, tk.END):
                lista_archivos.insert(tk.END, file_name)
                lista_archivos_paths[file_path] = file_name
            else:
                archivos_no_agregados.append(file_name)
        if archivos_no_agregados:
            messagebox.showwarning(
                "Archivos Duplicados",
                f"Los siguientes archivos ya estaban en la lista y no se añadieron nuevamente:\n{', '.join(archivos_no_agregados)}",
            )


# Función para limpiar el Text y Listbox
def limpiar():
    lista_archivos.delete(0, tk.END)
    text_area.delete("1.0", tk.END)


# Función para iniciar la transcripción en un hilo separado
def iniciar_transcripcion_thread():
    global transcripcion_activa
    if transcripcion_activa:
        transcripcion_activa = False
        boton_transcribir.config(text="Iniciar Transcripción")
    else:
        transcripcion_activa = True
        boton_transcribir.config(text="Detener Transcripción")
        progress_bar["value"] = 0
        progress_bar.pack(
            pady=10, padx=60, fill=tk.X
        )  # Hacer visible la barra de progreso
        threading.Thread(target=iniciar_transcripcion).start()


# Función para iniciar la transcripción
def iniciar_transcripcion():
    global transcripcion_activa
    archivos = lista_archivos.get(0, tk.END)
    if not archivos:
        messagebox.showwarning(
            "Advertencia", "Seleccione al menos un archivo de audio."
        )
        return

    transcripcion_total = ""
    text_area.delete("1.0", tk.END)
    idioma_entrada = idiomas[combobox_idioma_entrada.get()]
    idioma_salida = idiomas[combobox_idioma_salida.get()]

    progress_bar["maximum"] = len(archivos)
    for i, archivo in enumerate(archivos):
        if not transcripcion_activa:
            break
        audio_file = next(
            key for key, value in lista_archivos_paths.items() if value == archivo
        )
        archivo_procesando.set(f"Procesando: {archivo}")
        logging.info(f"Procesando archivo: {audio_file}")

        try:
            # Convertir archivo a WAV si no es WAV
            if not audio_file.endswith(".wav"):
                audio_file = convertir_a_wav(audio_file)

            texto_transcrito = transcribir_archivo(audio_file, idioma_entrada)

            if idioma_entrada != idioma_salida:
                texto_transcrito = traducir_texto(texto_transcrito, idioma_salida)

        except Exception as e:
            texto_transcrito = f"Error al procesar el archivo: {e}"
            logging.error(texto_transcrito)

        # Agregar la transcripción al texto total
        transcripcion_total += f"Transcripción de {archivo}:\n{texto_transcrito}\n\n"
        text_area.insert(tk.END, f"Transcripción de {archivo}:\n{texto_transcrito}\n\n")

        progress_bar["value"] = i + 1
        ventana.update_idletasks()

    archivo_procesando.set("")
    if transcripcion_activa:
        messagebox.showinfo("Información", "Transcripción completa.")
        boton_transcribir.config(text="Iniciar Transcripción")
        transcripcion_activa = False
        progress_bar.pack_forget()  # Ocultar la barra de progreso
        progress_bar["value"] = 0

    global transcripcion_resultado
    transcripcion_resultado = transcripcion_total


# Función para exportar la transcripción a un archivo de texto
def exportar_transcripcion():
    if not transcripcion_resultado:
        messagebox.showwarning("Advertencia", "No hay transcripción para exportar.")
        return
    output_file = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Archivo de texto", "*.txt")],
        title="Guardar transcripción como",
    )
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(transcripcion_resultado)
        messagebox.showinfo("Información", f"Transcripción guardada en {output_file}.")
        logging.info(f"Transcripción guardada en {output_file}.")


# Función para centrar la ventana en la pantalla
def centrar_ventana(ventana):
    ventana.update_idletasks()
    ancho_ventana = ventana.winfo_width()
    alto_ventana = ventana.winfo_height()
    ancho_pantalla = ventana.winfo_screenwidth()
    alto_pantalla = ventana.winfo_screenheight()
    x = (ancho_pantalla // 2) - (ancho_ventana // 2)
    y = (alto_pantalla // 2) - (alto_ventana // 2)
    ventana.geometry(f"{ancho_ventana}x{alto_ventana}+{x}+{y}")


# Crear la ventana principal
ventana = tk.Tk()
ventana.title("Transcriptor")

# Variable para mostrar el archivo que se está procesando
archivo_procesando = tk.StringVar()

# Crear los widgets
main_frame = tk.Frame(ventana)
main_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

# Diccionario para mantener la relación entre rutas completas y nombres de archivos
lista_archivos_paths = {}

label_titulo = tk.Label(
    main_frame, text="Transcriptor de Audio a Texto", font=("Helvetica", 16)
)
label_titulo.pack(side=tk.TOP, pady=5)

# Frame para el listbox
frame_listbox = tk.Frame(main_frame)
frame_listbox.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=2)

# Etiqueta para el listbox
label_listbox = tk.Label(frame_listbox, text="Lista de archivos")
label_listbox.pack(side=tk.TOP)

# Listbox con scrollbar
scrollbar_listbox = tk.Scrollbar(frame_listbox, orient=tk.VERTICAL)
lista_archivos = tk.Listbox(
    frame_listbox,
    selectmode=tk.SINGLE,
    width=40,
    height=20,
    yscrollcommand=scrollbar_listbox.set,
)
lista_archivos.pack(side=tk.LEFT, fill=tk.BOTH)
scrollbar_listbox.pack(side=tk.RIGHT, fill=tk.Y)
scrollbar_listbox.config(command=lista_archivos.yview)

# Frame para el Text widget y su scrollbar
frame_text = tk.Frame(main_frame)
frame_text.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=2)

# Etiqueta para el Text area
label_text_area = tk.Label(frame_text, text="Transcripción")
label_text_area.pack(side=tk.TOP)

# Text widget con scrollbar
scrollbar_text = tk.Scrollbar(frame_text, orient=tk.VERTICAL)
text_area = tk.Text(frame_text, height=25, width=80, yscrollcommand=scrollbar_text.set)
text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scrollbar_text.pack(side=tk.RIGHT, fill=tk.Y)
scrollbar_text.config(command=text_area.yview)

# Frame para los botones
frame_botones = tk.Frame(ventana)
frame_botones.pack(side=tk.BOTTOM, pady=10)

boton_seleccionar = tk.Button(
    frame_botones, text="Seleccionar Archivos", command=seleccionar_archivos
)
boton_seleccionar.pack(side=tk.LEFT, padx=30)

boton_transcribir = tk.Button(
    frame_botones, text="Iniciar Transcripción", command=iniciar_transcripcion_thread
)
boton_transcribir.pack(side=tk.LEFT, padx=5)

boton_exportar = tk.Button(
    frame_botones, text="Exportar", command=exportar_transcripcion
)
boton_exportar.pack(side=tk.LEFT, padx=5)

boton_limpiar = tk.Button(frame_botones, text="Limpiar", command=limpiar)
boton_limpiar.pack(side=tk.LEFT, padx=20)

# Frame para la barra de progreso
frame_progress = tk.Frame(ventana)
frame_progress.pack(fill=tk.X, padx=10, pady=10)

progress_label = tk.Label(frame_progress, textvariable=archivo_procesando)
progress_label.pack(pady=5)

progress_bar = ttk.Progressbar(frame_progress, orient="horizontal", mode="determinate")

label_creditos = tk.Label(ventana, text="Producido por Correa Jonathan")
label_creditos.pack(pady=10)

# ComboBox para seleccionar el idioma de entrada
frame_idioma_entrada = tk.Frame(ventana)
frame_idioma_entrada.pack(side=tk.TOP, pady=5)

label_idioma_entrada = tk.Label(
    frame_idioma_entrada, text="Seleccionar Idioma de Entrada:"
)
label_idioma_entrada.pack(side=tk.LEFT, padx=10)

idiomas = {
    "Español": "es",
    "Inglés": "en",
    "Francés": "fr",
    "Alemán": "de",
    "Italiano": "it",
    "Portugués": "pt",
}

combobox_idioma_entrada = ttk.Combobox(
    frame_idioma_entrada, values=list(idiomas.keys())
)
combobox_idioma_entrada.set("Español")  # Valor por defecto
combobox_idioma_entrada.pack(side=tk.LEFT, padx=10)

# ComboBox para seleccionar el idioma de salida
frame_idioma_salida = tk.Frame(ventana)
frame_idioma_salida.pack(side=tk.TOP, pady=5)

label_idioma_salida = tk.Label(
    frame_idioma_salida, text="Seleccionar Idioma de Salida:"
)
label_idioma_salida.pack(side=tk.LEFT, padx=10)

combobox_idioma_salida = ttk.Combobox(frame_idioma_salida, values=list(idiomas.keys()))
combobox_idioma_salida.set("Español")  # Valor por defecto
combobox_idioma_salida.pack(side=tk.LEFT, padx=10)

# Variable global para almacenar el resultado de la transcripción
transcripcion_resultado = ""

# Centrar la ventana en la pantalla
centrar_ventana(ventana)

# Ejecutar la aplicación
ventana.mainloop()
