import os
import speech_recognition as sr
from pydub import AudioSegment
from googletrans import Translator
import tempfile
import subprocess
import platform
import threading
from tkinter import messagebox
import tkinter as tk
from mutagen import File
import wave
import contextlib
from tkinter import filedialog
import time
from Config import (
    logging,
    ffmpeg_path,
    ffprobe_path,
    idiomas,
    transcripcion_activa,
    transcripcion_en_curso,
    check_proxy,
)
import numpy as np
import librosa
import whisper
from pydub import AudioSegment
from pydub.silence import split_on_silence


# Inicializar el reconocedor
recognizer = sr.Recognizer()

AudioSegment.converter = ffmpeg_path
AudioSegment.ffmpeg = ffmpeg_path
AudioSegment.ffprobe = ffprobe_path


def convertir_a_wav(audio_path):
    try:
        logging.info(f"Intentando convertir: {audio_path}")
        audio_format = audio_path.split(".")[-1]
        logging.info(f"Formato de audio detectado: {audio_format}")
        audio = AudioSegment.from_file(audio_path, format=audio_format)
        wav_path = audio_path.replace(audio_format, "wav")
        audio.export(wav_path, format="wav")
        logging.info(f"Archivo convertido a WAV: {wav_path}")
        return wav_path
    except Exception as e:
        logging.error(f"Error al convertir archivo a WAV: {e}")
        raise


def obtener_duracion_audio(ruta_archivo):

    try:
        audio = File(ruta_archivo)
        if audio is not None:
            return int(audio.info.length)
    except:
        pass

    if ruta_archivo.lower().endswith(".wav"):
        try:
            with contextlib.closing(wave.open(ruta_archivo, "r")) as f:
                frames = f.getnframes()
                rate = f.getframerate()
                duration = frames / float(rate)
                return int(duration)
        except:
            pass

    return 0


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
        if check_proxy() == "Proxy configurado:":
            proxy_config = {
                "http": "http://proxy.psa.gob.ar:3128",
                "https": "http://proxy.psa.gob.ar:3128",
            }
            translator = Translator(proxies=proxy_config)
        else:
            translator = Translator()
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


def limpiar(text_area):
    text_area.delete("1.0", tk.END)


def ajustar_texto_sencillo(texto, max_ancho=90):
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
    if len(lineas) > 1 and len(lineas[-1].split()) == 1:
        lineas[-2] += " " + lineas.pop()
    return "\n".join(lineas)


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

        # Abrir el archivo
        try:
            if platform.system() == "Darwin":  # macOS
                subprocess.call(("open", output_file))
            elif platform.system() == "Windows":  # Windows
                os.startfile(output_file)
            else:  # linux variants
                subprocess.call(("xdg-open", output_file))

            logging.info(f"Archivo abierto: {output_file}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el archivo: {str(e)}")
            logging.error(f"Error al abrir el archivo: {str(e)}")


def borrar_archivo(lista_archivos, lista_archivos_paths):
    seleccion = lista_archivos.curselection()
    if seleccion:
        indice = seleccion[0]
        archivo = lista_archivos.get(indice)
        lista_archivos.delete(indice)
        lista_archivos_paths.pop(
            next(
                key for key, value in lista_archivos_paths.items() if value == archivo
            ),
            None,
        )
        return True
    return False


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
    global transcripcion_activa, transcripcion_en_curso
    from Reproductor import reproductor

    if reproductor.reproduciendo:
        messagebox.showwarning(
            "Advertencia",
            "Hay una reproducción en curso. Por favor, detenga la reproducción antes de transcribir.",
        )
        return

    seleccion = lista_archivos.curselection()
    if not seleccion:
        messagebox.showwarning(
            "Advertencia", "Seleccione un archivo de audio para transcribir."
        )
        transcripcion_en_curso = False
        return

    if transcripcion_activa:
        transcripcion_activa = False
        boton_transcribir.config(text="Transcribir")
        progress_bar["value"] = 0
        progress_bar.pack_forget()
    else:
        transcripcion_activa = True
        transcripcion_en_curso = True
        boton_transcribir.config(text="Detener Transcripción")
        progress_bar["value"] = 0
        progress_bar.pack(pady=5, padx=60, fill=tk.X)
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
            daemon=True,
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

    seleccion = lista_archivos.curselection()
    # if not seleccion:
    #     messagebox.showwarning(
    #         "Advertencia", "Seleccione un archivo de audio para transcribir."
    #     )
    #     transcripcion_en_curso = False
    #     return

    archivo = lista_archivos.get(seleccion[0])
    audio_file = next(
        key for key, value in lista_archivos_paths.items() if value == archivo
    )

    idioma_entrada = idiomas[combobox_idioma_entrada.get()]
    idioma_salida = idiomas[combobox_idioma_salida.get()]

    archivo_procesando.set(f"Procesando: {archivo}")
    logging.info(f"Procesando archivo: {audio_file}")

    try:
        if not audio_file.endswith(".wav"):
            audio_file = convertir_a_wav(audio_file)

        audio = AudioSegment.from_wav(audio_file)
        duracion_total = len(audio)

        progress_bar["maximum"] = duracion_total
        ventana.update_idletasks()

        texto_transcrito = transcribir_archivo_grande(
            audio_file, idioma_entrada, progress_bar, ventana, transcripcion_activa
        )

        if transcripcion_activa and idioma_entrada != idioma_salida:
            texto_transcrito = traducir_texto(texto_transcrito, idioma_salida)

        if transcripcion_activa:
            texto_transcrito = ajustar_texto_sencillo(texto_transcrito)
            nuevo_texto = f"Transcripción de {archivo}:\n{texto_transcrito}\n\n"
            text_area.insert(tk.END, nuevo_texto)
            text_area.see(tk.END)

    except Exception as e:
        logging.error(f"Error al procesar el archivo: {e}")
        messagebox.showerror("Error", f"Error al procesar el archivo: {e}")

    archivo_procesando.set("")

    if transcripcion_activa:
        messagebox.showinfo("Información", "Transcripción completa.")

    boton_transcribir.config(text="Transcribir")
    transcripcion_activa = False
    progress_bar.pack_forget()
    progress_bar["value"] = 0
    transcripcion_en_curso = False


# def transcribir_archivo_grande(
#     audio_path,
#     idioma_entrada,
#     progress_bar,
#     ventana,
#     transcripcion_activa,
#     chunk_size=60000,
# ):
#     transcripcion_completa = []
#     progreso_actual = 0
#     duracion_total = obtener_duracion_audio(audio_path)

#     try:
#         with sr.AudioFile(audio_path) as source:
#             for i in range(0, duracion_total * 1000, chunk_size):
#                 if not transcripcion_activa:
#                     break

#                 inicio = i / 1000.0
#                 fin = min((i + chunk_size) / 1000.0, duracion_total)

#                 try:
#                     audio_chunk = recognizer.record(
#                         source, offset=inicio, duration=fin - inicio
#                     )

#                     texto = recognizer.recognize_google(
#                         audio_chunk, language=idioma_entrada
#                     )
#                     transcripcion_completa.append(texto)
#                 except sr.UnknownValueError:
#                     transcripcion_completa.append("[inaudible]")
#                 except sr.RequestError as e:
#                     logging.error(f"Error en el servicio de reconocimiento: {e}")
#                     transcripcion_completa.append("[error de reconocimiento]")
#                 except Exception as e:
#                     logging.error(f"Error inesperado al procesar chunk: {e}")
#                     transcripcion_completa.append("[error de procesamiento]")

#                 progreso_actual = int(fin * 1000)
#                 progress_bar["value"] = min(progreso_actual, duracion_total * 1000)
#                 ventana.update_idletasks()

#     except Exception as e:
#         logging.error(f"Error al procesar el archivo: {e}")
#         return f"Error al procesar el archivo: {e}"

#     return " ".join(transcripcion_completa).strip()


def transcribir_archivo_grande(
    audio_path,
    idioma_entrada,
    progress_bar,
    ventana,
    transcripcion_activa,
    chunk_size=60000,
):
    transcripcion_completa = []
    progreso_actual = 0
    duracion_total = obtener_duracion_audio(audio_path)

    try:
        # Cargar el audio y preprocesarlo
        audio = AudioSegment.from_wav(audio_path)
        audio = audio.normalize()

        # Segmentación basada en silencios
        chunks = split_on_silence(audio, min_silence_len=500, silence_thresh=-40)

        # Cargar modelo Whisper
        model = whisper.load_model("base")

        for i, chunk in enumerate(chunks):
            if not transcripcion_activa:
                break

            try:
                # Convertir chunk a numpy array para Whisper
                chunk_np = np.frombuffer(chunk.raw_data, dtype=np.int16)
                chunk_np = (
                    chunk_np.astype(np.float32) / 32768.0
                )  # Normalizar a [-1.0, 1.0]

                # Transcribir con Whisper
                result = model.transcribe(chunk_np, language=idioma_entrada)
                texto = result["text"]

                # Post-procesamiento básico
                texto = texto.strip()
                texto = texto.capitalize()

                transcripcion_completa.append(texto)
            except Exception as e:
                logging.error(f"Error al procesar chunk: {e}")
                transcripcion_completa.append("[error de procesamiento]")

            # Actualizar barra de progreso
            progreso_actual += len(chunk)
            progress_bar["value"] = min(progreso_actual, len(audio))
            ventana.update_idletasks()

        # Si Whisper falla, intentar con el reconocedor de Google como respaldo
        if not transcripcion_completa:
            with sr.AudioFile(audio_path) as source:
                audio_completo = recognizer.record(source)
                try:
                    texto = recognizer.recognize_google(
                        audio_completo, language=idioma_entrada
                    )
                    transcripcion_completa.append(texto)
                except sr.UnknownValueError:
                    transcripcion_completa.append("[inaudible]")
                except sr.RequestError as e:
                    logging.error(
                        f"Error en el servicio de reconocimiento de Google: {e}"
                    )
                    transcripcion_completa.append("[error de reconocimiento]")

    except Exception as e:
        logging.error(f"Error al procesar el archivo: {e}")
        return f"Error al procesar el archivo: {e}"

    return " ".join(transcripcion_completa).strip()
