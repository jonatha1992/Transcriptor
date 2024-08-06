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
    ffmpeg_path,
    ffprobe_path,
    idiomas,
    transcripcion_activa,
    transcripcion_en_curso,
    check_proxy,
)
import numpy as np
import librosa
from pydub.silence import split_on_silence
import io
from concurrent.futures import ThreadPoolExecutor, as_completed
import speech_recognition as sr
from pydub import AudioSegment
from pydub.silence import split_on_silence
import io
from Config import logger


# Inicializar el reconocedor
recognizer = sr.Recognizer()

# Configuración de AudioSegment
AudioSegment.converter = ffmpeg_path
AudioSegment.ffmpeg = ffmpeg_path
AudioSegment.ffprobe = ffprobe_path


def convertir_a_wav(audio_path):
    try:
        logger.info(f"Intentando convertir: {audio_path}")
        audio_format = audio_path.split(".")[-1]
        logger.info(f"Formato de audio detectado: {audio_format}")
        output_path = audio_path.replace(audio_format, "wav")

        # Verificar si el archivo WAV ya existe
        if os.path.exists(output_path):
            logger.info(f"El archivo WAV ya existe: {output_path}")
            return output_path

        command = [ffmpeg_path, "-i", audio_path, output_path]

        startupinfo = subprocess.STARTUPINFO()
        if platform.system() == "Windows":
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

        subprocess.run(
            command,
            startupinfo=startupinfo,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        logger.info(f"Archivo convertido a WAV: {output_path}")
        return output_path
    except subprocess.CalledProcessError as e:
        logger.error(f"ffmpeg proceso devolvió un error: {e.stderr.decode('utf-8')}")
        raise
    except FileNotFoundError as e:
        logger.error(f"ffmpeg no encontrado: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error al convertir archivo a WAV: {str(e)}")
        raise


def obtener_duracion_audio(ruta_archivo):
    try:
        audio = File(ruta_archivo)
        if audio is not None:
            return int(audio.info.length)
    except Exception:
        pass

    if ruta_archivo.lower().endswith(".wav"):
        try:
            with contextlib.closing(wave.open(ruta_archivo, "r")) as f:
                frames = f.getnframes()
                rate = f.getframerate()
                duration = frames / float(rate)
                return int(duration)
        except Exception:
            pass

    return 0


def transcribir_archivo(audio_path, idioma_entrada):
    try:
        with sr.AudioFile(audio_path) as source:
            audio = recognizer.record(source)
            text = recognizer.recognize_google(audio, language=idioma_entrada)
            logger.info(f"Transcripción inicial: {text}")
            return text
    except sr.UnknownValueError:
        logger.warning("Audio no claro / inaudible.")
        return "Audio no claro / inaudible."
    except sr.RequestError as e:
        logger.error(f"Error en el servicio de reconocimiento: {e}")
        return f"Error en el servicio de reconocimiento: {e}"
    except Exception as e:
        logger.error(f"Error al procesar el archivo: {e}")
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
        if traduccion:
            logger.info(f"Texto traducido: {traduccion.text}")
            return traduccion.text
        else:
            logger.error("La traducción devolvió un resultado vacío.")
            return f"Error al traducir el texto."
    except Exception as e:
        logger.error(f"Error al traducir texto: {e}")
        return f"Error al traducir texto: {e}"


def seleccionar_archivos(lista_archivos, lista_archivos_paths):
    file_paths = filedialog.askopenfilenames(
        filetypes=[
            ("Archivos de Audio", "*.mp3 *.wav *.flac *.ogg *.m4a *.mp4 *.aac *.opus")
        ],
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
    longitud_actual = 0

    for palabra in palabras:
        if len(palabra) > max_ancho:
            if linea_actual:
                lineas.append(" ".join(linea_actual))
            for i in range(0, len(palabra), max_ancho):
                lineas.append(palabra[i: i + max_ancho])
            linea_actual = []
            longitud_actual = 0
        elif longitud_actual + len(palabra) + (1 if linea_actual else 0) <= max_ancho:
            linea_actual.append(palabra)
            longitud_actual += len(palabra) + (1 if linea_actual else 0)
        else:
            lineas.append(" ".join(linea_actual))
            linea_actual = [palabra]
            longitud_actual = len(palabra)

    if linea_actual:
        lineas.append(" ".join(linea_actual))

    if len(lineas) > 1 and len(lineas[-1]) < max_ancho // 2:
        penultima = lineas[-2].split()
        ultima = lineas[-1].split()
        while penultima and len(" ".join(penultima + [ultima[0]])) <= max_ancho:
            ultima.insert(0, penultima.pop())
        lineas[-2] = " ".join(penultima)
        lineas[-1] = " ".join(ultima)

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
        logger.info(f"Transcripción guardada en {output_file}.")

        try:
            if platform.system() == "Darwin":
                subprocess.call(("open", output_file))
            elif platform.system() == "Windows":
                os.startfile(output_file)
            else:
                subprocess.call(("xdg-open", output_file))

            logger.info(f"Archivo abierto: {output_file}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el archivo: {str(e)}")
            logger.error(f"Error al abrir el archivo: {str(e)}")


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
        transcripcion_en_curso = False
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

    archivo = lista_archivos.get(seleccion[0])
    audio_file = next(
        key for key, value in lista_archivos_paths.items() if value == archivo
    )

    idioma_entrada = idiomas[combobox_idioma_entrada.get()]
    idioma_salida = idiomas[combobox_idioma_salida.get()]

    archivo_procesando.set(f"Procesando: {archivo}")
    logger.info(f"Procesando archivo: {audio_file}")

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
        logger.error(f"Error al procesar el archivo: {e}")
        messagebox.showerror("Error", f"Error al procesar el archivo: {e}")

    archivo_procesando.set("")

    if transcripcion_activa:
        messagebox.showinfo("Información", "Transcripción completa.")

    boton_transcribir.config(text="Transcribir")
    transcripcion_activa = False
    progress_bar.pack_forget()
    progress_bar["value"] = 0
    transcripcion_en_curso = False


def mejorar_audio(audio):
    try:
        audio = audio.set_channels(1)  # Convertir a mono
        audio = audio.high_pass_filter(80)
        audio = audio.normalize()
        return audio
    except Exception as e:
        logger.error(f"Error en mejorar_audio: {e}")
        return audio


def dividir_fragmento_largo(chunks, max_length):
    nuevos_chunks = []
    for chunk in chunks:
        if len(chunk) > max_length:
            nuevos_chunks.extend([chunk[i:i + max_length] for i in range(0, len(chunk), max_length)])
        else:
            nuevos_chunks.append(chunk)
    return nuevos_chunks


def transcribir_archivo_grande(audio_path, idioma_entrada, progress_bar, ventana, transcripcion_activa):
    transcripcion_completa = []
    progreso_actual = 0

    try:
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"El archivo {audio_path} no existe")

        audio = AudioSegment.from_file(audio_path)
        if len(audio) == 0:
            raise ValueError("El archivo de audio está vacío")

        duracion_total = len(audio)
        audio = mejorar_audio(audio)

        # Dividir el audio en fragmentos basados en silencio
        chunks = split_on_silence(
            audio,
            min_silence_len=500,
            silence_thresh=audio.dBFS - 25,
            keep_silence=100,
        )

        # Dividir cualquier fragmento que sea mayor a 10 segundos
        max_chunk_length = 10000  # 10 segundos en milisegundos
        chunks = dividir_fragmento_largo(chunks, max_chunk_length)

        # Log the duration of each chunk
        for i, chunk in enumerate(chunks):
            duracion_chunk = len(chunk) / 1000  # Duración en segundos
            logger.info(f"Chunk {i} duración: {duracion_chunk} segundos")

        if not chunks:
            logger.warning("No se pudieron crear chunks de audio. Procesando el archivo completo.")
            chunks = [audio]

        recognizer = sr.Recognizer()
        recognizer.energy_threshold = 300
        recognizer.dynamic_energy_threshold = True

        chunks_numerados = list(enumerate(chunks))
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for i, chunk in chunks_numerados:
                if not transcripcion_activa:
                    break
                logger.info(f"Transcribiendo chunk {i} con duración {len(chunk) / 1000} segundos")
                futures.append(executor.submit(transcribir_chunk, recognizer, chunk, idioma_entrada, i))

            resultados = []
            for future in as_completed(futures):
                if not transcripcion_activa:
                    break
                i, texto = future.result()
                if texto and not texto.startswith("[error:"):
                    resultados.append((i, texto))

                progreso_actual += len(chunks[i])
                progress_bar["value"] = min(progreso_actual, duracion_total)
                ventana.update_idletasks()

            # Ordenar los resultados por el índice original
            resultados.sort(key=lambda x: x[0])
            transcripcion_completa = [texto for i, texto in resultados]

        # Si no se reconoció nada, intentar con el archivo completo
        if not transcripcion_completa:
            logger.warning("Intentando transcribir el archivo completo...")
            _, texto_completo = transcribir_chunk(recognizer, audio, idioma_entrada, 0)
            if texto_completo and not texto_completo.startswith("[error:"):
                transcripcion_completa.append(texto_completo)

        transcripcion_final = " ".join(transcripcion_completa).strip()
        transcripcion_final = transcripcion_final.capitalize()

        if not transcripcion_final:
            return "No se pudo transcribir ninguna parte del audio."

        return transcripcion_final

    except FileNotFoundError as e:
        logger.error(f"Error de archivo: {e}")
        return f"Error: {str(e)}"
    except ValueError as e:
        logger.error(f"Error de valor: {e}")
        return f"Error: {str(e)}"
    except Exception as e:
        logger.error(f"Error al procesar el archivo: {e}")
        return f"Error al procesar el archivo: {e}"


def transcribir_chunk(recognizer, audio_chunk, idioma_entrada, indice):
    try:
        if len(audio_chunk) == 0:
            return indice, "[chunk vacío]"

        buffer = io.BytesIO()
        audio_chunk.export(buffer, format="wav")
        buffer.seek(0)

        with sr.AudioFile(buffer) as source:
            audio_data = recognizer.record(source)

        if not audio_data or len(audio_data.frame_data) == 0:
            return indice, "[datos de audio vacíos]"

        texto = recognizer.recognize_google(audio_data, language=idioma_entrada)
        duracion_chunk = len(audio_chunk) / 1000  # Duración en segundos
        logger.info(f"Chunk {indice} transcrito: {texto}... (Duración: {duracion_chunk} segundos)")
        return indice, texto
    except sr.UnknownValueError:
        logger.warning(
            f"Audio no reconocido en chunk {indice} - Duración: {len(audio_chunk) / 1000} segundos"
        )
        return indice, "[inaudible]"
    except sr.RequestError as e:
        logger.error(f"Error en el servicio de reconocimiento para chunk {indice}: {e}")
        return indice, "[error de reconocimiento]"
    except Exception as e:
        logger.error(f"Error inesperado al procesar chunk {indice}: {e}")
        return indice, f"[error: {str(e)}]"
