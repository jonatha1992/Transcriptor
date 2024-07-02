import os
import logging
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import speech_recognition as sr
from pydub import AudioSegment
from pydub.utils import which
from googletrans import Translator, LANGUAGES
import pygame
from mutagen.mp3 import MP3
import time
from mutagen import File
import wave
import contextlib
import pygame
from tkinter import messagebox
import urllib.request
import sys

# Configuración de logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Inicializar el reconocedor y el traductor
recognizer = sr.Recognizer()
translator = Translator()

# Configurar rutas de FFmpeg
script_dir = os.path.dirname(os.path.abspath(__file__))
ffmpeg_path = os.path.join(script_dir, "ffmpeg", "bin", "ffmpeg.exe")
ffprobe_path = os.path.join(script_dir, "ffmpeg", "bin", "ffprobe.exe")

# Agregar la carpeta de FFmpeg al PATH
ffmpeg_bin_path = os.path.join(script_dir, "ffmpeg", "bin")
os.environ["PATH"] = ffmpeg_bin_path + os.pathsep + os.environ["PATH"]

AudioSegment.converter = ffmpeg_path
AudioSegment.ffmpeg = ffmpeg_path
AudioSegment.ffprobe = ffprobe_path


logging.debug(f"FFmpeg path: {ffmpeg_path}")
logging.debug(f"FFprobe path: {ffprobe_path}")

# Definir las variables globales
transcripcion_activa = False
idiomas = {v.capitalize(): k for k, v in LANGUAGES.items()}

# Inicializar pygame mixer
pygame.mixer.init()

reproduciendo = False
audio_actual = None
tiempo_reproduccion = 0
reproduccion_en_curso = False
transcripcion_en_curso = False


def convertir_a_wav(audio_path):
    try:
        print(f"Intentando convertir: {audio_path}")
        print(f"FFMPEG path: {AudioSegment.converter}")
        print(f"FFPROBE path: {AudioSegment.ffprobe}")
        audio_format = audio_path.split(".")[-1]
        print(f"Formato de audio detectado: {audio_format}")
        audio = AudioSegment.from_file(audio_path, format=audio_format)
        wav_path = audio_path.replace(audio_format, "wav")
        audio.export(wav_path, format="wav")
        print(f"Archivo convertido a WAV: {wav_path}")
        return wav_path
    except Exception as e:
        print(f"Error al convertir archivo a WAV: {e}")
        print(f"Tipo de error: {type(e)}")
        import traceback

        print(traceback.format_exc())
        raise


def detectar_y_configurar_proxy():
    proxy_handler = urllib.request.ProxyHandler()
    opener = urllib.request.build_opener(proxy_handler)
    try:
        # Intenta conectarse a un sitio web sin configurar el proxy
        opener.open("http://www.google.com", timeout=5)
        print("Conexión directa exitosa, no se necesita proxy.")
        return False
    except Exception:
        # Si falla, intenta configurar el proxy
        print("Conexión directa fallida, configurando proxy...")
        os.environ["http_proxy"] = "http://proxy.psa.gob.ar:3128"
        os.environ["https_proxy"] = "https://proxy.psa.gob.ar:3128"

        # Verifica si la conexión funciona con el proxy
        try:
            proxy_handler = urllib.request.ProxyHandler(
                {
                    "http": "http://proxy.psa.gob.ar:3128",
                    "https": "https://proxy.psa.gob.ar:3128",
                }
            )
            opener = urllib.request.build_opener(proxy_handler)
            opener.open("http://www.google.com", timeout=5)
            print("Proxy configurado exitosamente.")
            return True
        except Exception:
            print("No se pudo establecer conexión incluso con el proxy.")
            return False


def check_proxy():
    http_proxy = os.environ.get("http_proxy")
    https_proxy = os.environ.get("https_proxy")
    if http_proxy or https_proxy:
        return f"Proxy configurado:\nHTTP: {http_proxy}\nHTTPS: {https_proxy}"
    else:
        return "No se detectó ningún proxy configurado"


def obtener_duracion_audio(ruta_archivo):
    try:
        # Intenta primero con mutagen
        audio = File(ruta_archivo)
        if audio is not None:
            return int(audio.info.length)
    except:
        pass

    # Si mutagen falla, intenta con wave para archivos WAV
    if ruta_archivo.lower().endswith(".wav"):
        try:
            with contextlib.closing(wave.open(ruta_archivo, "r")) as f:
                frames = f.getnframes()
                rate = f.getframerate()
                duration = frames / float(rate)
                return int(duration)
        except:
            pass

    return 0  # Si no se puede determinar la duración


def reproducir(
    lista_archivos,
    lista_archivos_paths,
    boton_pausar_reanudar,
    label_reproduccion,
    label_tiempo,
):
    global reproduciendo, audio_actual, tiempo_reproduccion, reproduccion_en_curso, transcripcion_en_curso

    if transcripcion_en_curso:
        messagebox.showwarning(
            "Advertencia",
            "Hay una transcripción en curso. Por favor, espere a que termine.",
        )
        return

    seleccion = lista_archivos.curselection()
    if not seleccion:
        messagebox.showwarning(
            "Advertencia", "Por favor, seleccione un archivo de audio primero."
        )
        return

    reproduccion_en_curso = True

    indice_seleccionado = seleccion[0]
    item_seleccionado = lista_archivos.get(indice_seleccionado)
    ruta_archivo = next(
        key for key, value in lista_archivos_paths.items() if value == item_seleccionado
    )

    if audio_actual != ruta_archivo:
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()

        try:
            pygame.mixer.music.load(ruta_archivo)
            audio_actual = ruta_archivo
            tiempo_reproduccion = 0
        except pygame.error:
            if not ruta_archivo.lower().endswith(".wav"):
                respuesta = messagebox.askyesno(
                    "Conversión necesaria",
                    f"El archivo {os.path.basename(ruta_archivo)} necesita ser convertido a WAV para reproducirlo. ¿Desea continuar?",
                )
                if respuesta:
                    try:
                        ruta_archivo = convertir_a_wav(ruta_archivo)
                        pygame.mixer.music.load(ruta_archivo)
                        audio_actual = ruta_archivo
                        tiempo_reproduccion = 0
                        messagebox.showinfo(
                            "Conversión exitosa",
                            f"El archivo ha sido convertido y guardado como {os.path.basename(ruta_archivo)}",
                        )
                    except Exception as e:
                        messagebox.showerror(
                            "Error",
                            f"No se pudo convertir o cargar el archivo: {str(e)}",
                        )
                        reproduccion_en_curso = False
                        return
                else:
                    reproduccion_en_curso = False
                    return
            else:
                messagebox.showerror(
                    "Error", "No se puede reproducir este archivo de audio."
                )
                reproduccion_en_curso = False
                return

    try:
        pygame.mixer.music.play(start=tiempo_reproduccion)
        reproduciendo = True
        boton_pausar_reanudar.config(text="Pausar", state="active")
        actualizar_tiempo(label_tiempo, ruta_archivo)
        actualizar_label_reproduccion(label_reproduccion)
    except pygame.error as e:
        messagebox.showerror(
            "Error de reproducción", f"No se pudo reproducir el archivo: {str(e)}"
        )
        reproduciendo = False
    finally:
        reproduccion_en_curso = False


def pausar_reanudar(boton_pausar_reanudar, label_reproduccion, label_tiempo):
    global reproduciendo, tiempo_reproduccion, audio_actual, reproduccion_en_curso

    try:
        if reproduciendo:
            boton_pausar_reanudar.config(text="Reanudar")
            pygame.mixer.music.pause()
            reproduciendo = False
            actualizar_tiempo(label_tiempo, audio_actual)
        else:
            boton_pausar_reanudar.config(text="Pausar")
            pygame.mixer.music.unpause()
            reproduciendo = True
            actualizar_tiempo(label_tiempo, audio_actual)

        # actualizar_label_reproduccion(label_reproduccion)
    except pygame.error as e:
        messagebox.showerror("Error", f"Ocurrió un error al pausar/reanudar: {str(e)}")


def detener_reproduccion(boton_pausar_reanudar, label_reproduccion, label_tiempo):
    global reproduciendo, audio_actual, tiempo_reproduccion, reproduccion_en_curso

    pygame.mixer.music.stop()
    pygame.mixer.music.unload()

    reproduciendo = False
    audio_actual = None
    tiempo_reproduccion = 0
    reproduccion_en_curso = False

    boton_pausar_reanudar.config(text="Pausar", state="disabled")
    actualizar_label_reproduccion(label_reproduccion)
    label_tiempo.config(text="00:00 / 00:00")

    print("Reproducción detenida y audio descargado")


def actualizar_label_reproduccion(label):
    if reproduciendo and audio_actual:
        label.config(text=f"Reproduciendo: {os.path.basename(audio_actual)}")
    else:
        label.config(text="")


def actualizar_tiempo(label, ruta_archivo):
    global tiempo_reproduccion
    duracion_total = obtener_duracion_audio(ruta_archivo)

    def actualizar():
        global tiempo_reproduccion, reproduciendo
        if reproduciendo:
            tiempo_reproduccion = pygame.mixer.music.get_pos() // 1000
            tiempo_actual = time.strftime("%M:%S", time.gmtime(tiempo_reproduccion))
            tiempo_total = time.strftime("%M:%S", time.gmtime(duracion_total))
            label.config(text=f"{tiempo_actual} / {tiempo_total}")
            label.after(1000, actualizar)
        # elif not pygame.mixer.music.get_busy():
        #     label.config(text="00:00 / 00:00")

    actualizar()


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


def traducir_texto(texto, idioma_salida):
    try:
        traduccion = translator.translate(texto, dest=idioma_salida)
        logging.info(f"Texto traducido: {traduccion.text}")
        return traduccion.text
    except Exception as e:
        logging.error(f"Error al traducir texto: {e}")
        return f"Error al traducir texto: {e}"


def seleccionar_archivos(lista_archivos, lista_archivos_paths):
    file_paths = filedialog.askopenfilenames(
        filetypes=[("Archivos de Audio", "*.mp3 *.wav *.flac *.ogg *.m4a *.mp4 *.aac")],
        title="Seleccionar archivos de audio",
    )
    archivos_no_agregados = []
    if file_paths:
        for file_path in file_paths:
            file_name = os.path.basename(file_path)
            duracion = obtener_duracion_audio(file_path)
            duracion_str = time.strftime("%M:%S", time.gmtime(duracion))
            item = f"{file_name} ({duracion_str})"
            if item not in lista_archivos.get(0, tk.END):
                lista_archivos.insert(tk.END, item)
                lista_archivos_paths[file_path] = item
            else:
                archivos_no_agregados.append(file_name)
        if archivos_no_agregados:
            messagebox.showwarning(
                "Archivos Duplicados",
                f"Los siguientes archivos ya estaban en la lista y no se añadieron nuevamente:\n{', '.join(archivos_no_agregados)}",
            )


def limpiar(lista_archivos, text_area):
    lista_archivos.delete(0, tk.END)
    text_area.delete("1.0", tk.END)


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
    global transcripcion_activa, transcripcion_en_curso, reproduccion_en_curso

    if reproduccion_en_curso:
        messagebox.showwarning(
            "Advertencia",
            "Hay una reproducción en curso. Por favor, detenga la reproducción antes de transcribir.",
        )
        return

    if transcripcion_activa:
        transcripcion_activa = False
        boton_transcribir.config(text="Iniciar Transcripción")
        progress_bar["value"] = 0
        progress_bar.pack_forget()
    else:
        transcripcion_activa = True
        transcripcion_en_curso = True
        boton_transcribir.config(text="Detener Transcripción")
        progress_bar["value"] = 0
        progress_bar.pack(pady=0, padx=60, fill=tk.X)
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
    global transcripcion_activa, transcripcion_en_curso
    archivos = lista_archivos.get(0, tk.END)
    if not archivos:
        messagebox.showwarning(
            "Advertencia", "Seleccione al menos un archivo de audio."
        )
        transcripcion_en_curso = False
        return

    transcripcion_total = ""
    text_area.mark_set(tk.INSERT, tk.END)
    if text_area.get("1.0", tk.END).strip():
        text_area.insert(tk.END, "\n")

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
            if not audio_file.endswith(".wav"):
                audio_file = convertir_a_wav(audio_file)

            texto_transcrito = transcribir_archivo(audio_file, idioma_entrada)

            if idioma_entrada != idioma_salida:
                texto_transcrito = traducir_texto(texto_transcrito, idioma_salida)

            texto_transcrito = ajustar_texto_sencillo(texto_transcrito)

        except Exception as e:
            texto_transcrito = f"Error al procesar el archivo: {e}"
            logging.error(texto_transcrito)

        nuevo_texto = f"Transcripción de {archivo}:\n{texto_transcrito}\n\n"
        transcripcion_total += nuevo_texto
        text_area.insert(tk.END, nuevo_texto)
        text_area.see(tk.END)

        progress_bar["value"] = i + 1
        ventana.update_idletasks()

    archivo_procesando.set("")

    if transcripcion_activa:
        messagebox.showinfo("Información", "Transcripción completa.")
        boton_transcribir.config(text="Iniciar Transcripción")
        transcripcion_activa = False
        progress_bar.pack_forget()
        progress_bar["value"] = 0

    transcripcion_resultado = transcripcion_total
    transcripcion_en_curso = False


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
