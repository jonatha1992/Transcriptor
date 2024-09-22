from pydub import effects
from Config import logger, idiomas, resource_path, transcripcion_activa, transcripcion_en_curso
import whisper
import os
from googletrans import Translator
import subprocess
import platform
import threading
import tkinter as tk
from mutagen import File
import wave
import contextlib
import time
from Config import *
from pydub import AudioSegment
from Config import logger
from scipy.signal import butter, lfilter
from tkinter import messagebox, filedialog
from pydub import AudioSegment
import numpy as np


# Configuración de AudioSegment
AudioSegment.converter = ffmpeg_path
AudioSegment.ffmpeg = ffmpeg_path
AudioSegment.ffprobe = ffprobe_path

print(whisper.__file__)


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
    combobox_idioma_salida,
    checkBox
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
                combobox_idioma_salida,
                checkBox
            ),
            daemon=True,
        ).start()


def contar_palabras_y_inaudibles(texto):
    palabras = texto.split()
    inaudibles = palabras.count("[inaudible]")
    palabras_sin_inaudibles = len(palabras) - inaudibles
    return palabras_sin_inaudibles, inaudibles


def butter_bandpass(lowcut, highcut, fs, order=5):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a


def butter_bandpass_filter(data, lowcut, highcut, fs, order=5):
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    y = lfilter(b, a, data)
    return y


def mejorar_audio(audio, lowcut=300, highcut=3000):
    try:
        # Convertir a mono
        audio = audio.set_channels(1)

        # Aplicar filtro paso banda
        samples = np.array(audio.get_array_of_samples())
        filtered = butter_bandpass_filter(samples, lowcut, highcut, audio.frame_rate)

        # Normalizar
        filtered = np.int16(filtered / np.max(np.abs(filtered)) * 32767)

        # Crear nuevo AudioSegment
        mejorado = AudioSegment(
            filtered.tobytes(),
            frame_rate=audio.frame_rate,
            sample_width=2,
            channels=1
        )

        return mejorado
    except Exception as e:
        logger.error(f"Error en mejorar_audio: {e}")
        return audio


# def procesar_audio_wisper(audio_file, model, progress_bar, ventana):
#     filename = os.path.basename(audio_file)

#     # Obtener la duración total del audio
#     audio = AudioSegment.from_file(audio_file)
#     duracion_total = len(audio) / 1000  # Duración en segundos
#     # Mejorar el audio
#     audio = mejorar_audio(audio)

#     # Dividir el audio en fragmentos basados en silencio usando VAD

#     stop_event = threading.Event()
#     progress_thread = threading.Thread(
#         target=actualizar_progreso,
#         args=(progress_bar, ventana, duracion_total, stop_event)
#     )
#     progress_thread.start()

#     try:
#         # Usar Whisper para transcribir
#         result = model.transcribe(audio_file)
#         transcripcion = result["text"]
#     finally:
#         stop_event.set()
#         progress_thread.join()

#     palabras, inaudibles = contar_palabras_y_inaudibles(transcripcion)
#     return {
#         "filename": filename,
#         "archivo": audio_file,
#         "transcripcion": transcripcion,
#         "num_chunk s": 1,  # Whisper procesa el archivo completo
#         "inaudibles": inaudibles,
#         "palabras": palabras
#     }


def iniciar_transcripcion(
    lista_archivos,
    text_area,
    archivo_procesando,
    lista_archivos_paths,
    transcripcion_resultado,
    progress_bar,
    ventana,
    boton_transcribir,
    combobox_idioma_salida,
    checkBox
):
    global transcripcion_activa, transcripcion_en_curso

    seleccion = lista_archivos.curselection()
    if not seleccion:
        messagebox.showwarning("Advertencia", "Por favor, seleccione al menos un archivo para transcribir.")
        return

    archivos_seleccionados = [lista_archivos.get(i) for i in seleccion]
    total_archivos = len(archivos_seleccionados)

    idioma_salida = idiomas[combobox_idioma_salida.get()]

    transcripcion_activa = True
    transcripcion_en_curso = True
    boton_transcribir.config(text="Detener Transcripción")
    progress_bar.pack(pady=5, padx=60, fill=tk.X)  # Asegurarse de que la barra de progreso esté visible

    for index, archivo in enumerate(archivos_seleccionados):
        if not transcripcion_activa:
            break

        audio_file = next(key for key, value in lista_archivos_paths.items() if value == archivo)

        archivo_procesando.set(f"Procesando: {archivo} ({index + 1}/{total_archivos})")
        logger.info(f"Procesando archivo: {audio_file}")

        try:
            progress_bar["value"] = 0
            ventana.update_idletasks()

            # resultado_wisper_M = procesar_audio_wisper(audio_file, model_M, progress_bar, ventana)

            resultado_wisper_M = procesar_audio_whisper_por_fragmentos(audio_file, model_M, progress_bar, ventana)

            checkBox_value = checkBox.get()
            if checkBox_value:
                resultado_wisper_M['transcripcion'] = traducir_texto(resultado_wisper_M['transcripcion'], idioma_salida)

            if transcripcion_activa:
                texto_transcrito = ajustar_texto_sencillo(resultado_wisper_M['transcripcion'])
                nuevo_texto = f"Transcripción  {archivo}: \n{texto_transcrito} \n\nPalabras: {resultado_wisper_M['palabras']} \nInaudibles: {resultado_wisper_M['inaudibles']}\n\n"
                text_area.insert(tk.END, nuevo_texto)
                text_area.see(tk.END)

            # Actualizar la barra de progreso general
            progress_bar["value"] = ((index + 1) / total_archivos) * 100
            ventana.update_idletasks()

        except Exception as e:
            logger.error(f"Error al procesar el archivo {archivo}: {e}")
            messagebox.showerror("Error", f"Error al procesar el archivo {archivo}: {e}")

        if not transcripcion_activa:
            break

    archivo_procesando.set("")

    if transcripcion_activa:
        messagebox.showinfo("Información", f"Transcripción completa para {total_archivos} archivo(s).")

    boton_transcribir.config(text="Transcribir")
    transcripcion_activa = False
    progress_bar.pack_forget()
    progress_bar["value"] = 0
    transcripcion_en_curso = False


def cargar_modelo_whisper():
    try:

        # Ruta al directorio de modelos de Whisper en el ejecutable
        whisper_root = resource_path("whisper")
        os.makedirs(whisper_root, exist_ok=True)

        # Ruta a los assets de Whisper dentro de la carpeta whisper
        whisper_assets_path = os.path.join(whisper_root, "assets")
        os.makedirs(whisper_assets_path, exist_ok=True)

        # Copiar archivos necesarios
        for file in ['mel_filters.npz', 'gpt2.tiktoken', 'multilingual.tiktoken']:
            src = os.path.join(whisper_root, file)
            dst = os.path.join(whisper_assets_path, file)
            if os.path.exists(src):
                shutil.copy(src, dst)
        global model_M
        # Configurar Whisper para usar la nueva ubicación
        os.environ['WHISPER_HOME'] = whisper_root
        model_M = whisper.load_model("medium", download_root=whisper_root)

        # Imprimir información de depuración
        print(f"Whisper file location: {whisper.__file__}")
        print(f"Model download location: {whisper_root}")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Files in whisper_root: {os.listdir(whisper_root)}")
        print(f"Files in whisper assets: {os.listdir(whisper_assets_path)}")

    except Exception as e:
        logger.error(f"Error al cargar el modelo Whisper: {e}")
        messagebox.showerror("Error", f"No se pudo cargar el modelo Whisper: {e}")


def procesar_audio_whisper_por_fragmentos(audio_file, model, progress_bar, ventana):
    filename = os.path.basename(audio_file)

    # Cargar el audio completo
    audio = AudioSegment.from_file(audio_file)

    # Dividir el audio en fragmentos de duración fija (por ejemplo, 30 segundos)
    chunk_duration_ms = 30 * 1000  # 30 segundos en milisegundos
    chunks = [audio[i:i + chunk_duration_ms] for i in range(0, len(audio), chunk_duration_ms)]
    num_chunks = len(chunks)

    transcripcion_completa = ""
    palabras_totales, inaudibles_totales = 0, 0

    for idx, chunk in enumerate(chunks):
        # Asegurarse de que el fragmento tenga una tasa de muestreo de 16000 Hz y sea mono
        chunk = chunk.set_frame_rate(16000)
        chunk = chunk.set_channels(1)

        # Normalizar el audio
        chunk = effects.normalize(chunk)

        # Obtener los datos de audio del fragmento como un arreglo de NumPy
        samples = chunk.get_array_of_samples()
        audio_np = np.array(samples).astype(np.float32) / 32768.0  # Convertir a float32 en el rango [-1.0, 1.0]

        # Transcribir el fragmento
        result = model.transcribe(audio_np)
        transcribed_text = result['text']

        # Actualizar la transcripción completa
        transcripcion_completa += transcribed_text + "\n"

        # Actualizar la barra de progreso
        progress = ((idx + 1) / num_chunks) * 100
        progress_bar["value"] = progress
        ventana.update_idletasks()

    # Calcular estadísticas si lo deseas
    palabras_totales = len(transcripcion_completa.split())
    inaudibles_totales = transcripcion_completa.count('[inaudible]')

    # Retornar resultados
    return {
        "filename": filename,
        "archivo": audio_file,
        "transcripcion": transcripcion_completa,
        "num_chunks": num_chunks,
        "inaudibles": inaudibles_totales,
        "palabras": palabras_totales
    }
