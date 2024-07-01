import os
import logging
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import speech_recognition as sr
from pydub import AudioSegment
from pydub.utils import which
from googletrans import Translator, LANGUAGES


# Inicializar el reconocedor y el traductor
recognizer = sr.Recognizer()
translator = Translator()

current_dir = os.path.dirname(os.path.abspath(__file__))
ffmpeg_path = os.path.join(current_dir, "ffmpeg", "bin", "ffmpeg.exe")
ffprobe_path = os.path.join(current_dir, "ffmpeg", "bin", "ffprobe.exe")
AudioSegment.converter = ffmpeg_path
AudioSegment.ffprobe = ffprobe_path


# # Asegurarse de que pydub encuentre ffmpeg y ffprobe
# AudioSegment.converter = which("ffmpeg")
# AudioSegment.ffprobe = which("ffprobe")

# Definir la variable global para controlar el estado de la transcripción
transcripcion_activa = False
idiomas = {v.capitalize(): k for k, v in LANGUAGES.items()}


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
def seleccionar_archivos(lista_archivos, lista_archivos_paths):
    file_paths = filedialog.askopenfilenames(
        filetypes=[("Archivos de Audio", "*.wav *.mp3 *.flac *.ogg *.m4a *.mp4 *.aac")],
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
def limpiar(lista_archivos, text_area):
    lista_archivos.delete(0, tk.END)
    text_area.delete("1.0", tk.END)


# Función para iniciar la transcripción en un hilo separado
def iniciar_transcripcion_thread(
    lista_archivos,
    text_area,
    archivo_procesando,
    lista_archivos_paths,
    transcripcion_resultado,
    progress_bar,
    ventana,
    boton_transcribir,
    combobox_idioma_entrada,
    combobox_idioma_salida,
):
    global transcripcion_activa
    if transcripcion_activa:
        transcripcion_activa = False
        boton_transcribir.config(text="Iniciar Transcripción")
        progress_bar["value"] = 0
        progress_bar.pack_forget()

    else:
        transcripcion_activa = True
        boton_transcribir.config(text="Detener Transcripción")
        progress_bar["value"] = 0
        progress_bar.pack(
            pady=0, padx=60, fill=tk.X
        )  # Hacer visible la barra de progreso
        threading.Thread(
            target=iniciar_transcripcion,
            args=(
                lista_archivos,
                text_area,
                archivo_procesando,
                lista_archivos_paths,
                transcripcion_resultado,
                progress_bar,
                ventana,
                boton_transcribir,
                combobox_idioma_entrada,
                combobox_idioma_salida,
            ),
        ).start()


# Función para iniciar la transcripción
def iniciar_transcripcion(
    lista_archivos,
    text_area,
    archivo_procesando,
    lista_archivos_paths,
    transcripcion_resultado,
    progress_bar,
    ventana,
    boton_transcribir,
    combobox_idioma_entrada,
    combobox_idioma_salida,
):
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

            # Ajustar el texto transcrito
            texto_transcrito = ajustar_texto_sencillo(texto_transcrito)

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

    transcripcion_resultado = transcripcion_total


def ajustar_texto_sencillo(texto, max_ancho=75):
    palabras = texto.split()
    lineas = []
    linea_actual = []

    for palabra in palabras:
        if len(" ".join(linea_actual + [palabra])) <= max_ancho:
            linea_actual.append(palabra)
        else:
            lineas.append(" ".join(linea_actual))
            linea_actual = [palabra]

    if linea_actual:
        lineas.append(" ".join(linea_actual))

    # Ajustar la última línea para evitar palabras sueltas
    if len(lineas) > 1 and len(lineas[-1].split()) == 1:
        lineas[-2] += " " + lineas.pop()

    return "\n".join(lineas)


# Función para exportar la transcripción a un archivo de texto
def exportar_transcripcion(transcripcion_resultado):
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
