import shutil  # Asegúrate de importar io al inicio de tu script
from tkinter import messagebox
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
from config import *
from pydub import AudioSegment
from tkinter import messagebox, filedialog
import numpy as np


idiomas_alrevez = {v.capitalize(): k for k, v in LANGUAGES.items()}


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


def seleccionar_archivos(lista_archivos, lista_archivos_paths):
    file_paths = filedialog.askopenfilenames(
        filetypes=[
            ("Archivos de Audio", "*.wav *.mp3 *.m4a *.ogg *.flac *.aac *.mp4 *.mpeg *.mpga *.3gp *.opus")
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


def contar_palabras_y_inaudibles(texto):
    palabras = texto.split()
    inaudibles = palabras.count("[inaudible]")
    palabras_sin_inaudibles = len(palabras) - inaudibles
    return palabras_sin_inaudibles, inaudibles


def cargar_modelo_whisper(modelo_seleccionado):
    try:
        whisper_root = resource_path("whisper")
        os.makedirs(whisper_root, exist_ok=True)

        whisper_assets_path = os.path.join(whisper_root, "assets")
        os.makedirs(whisper_assets_path, exist_ok=True)

        for file in ['mel_filters.npz', 'gpt2.tiktoken', 'multilingual.tiktoken']:
            src = os.path.join(whisper_root, file)
            dst = os.path.join(whisper_assets_path, file)
            if os.path.exists(src):
                shutil.copy(src, dst)

        global model_whisper
        os.environ['WHISPER_HOME'] = whisper_root
        model_whisper = whisper.load_model(modelo_seleccionado, download_root=whisper_root)

        logger.info(f"Modelo Whisper '{modelo_seleccionado}' cargado correctamente.")
    except Exception as e:
        logger.error(f"Error al cargar el modelo Whisper: {e}")
        messagebox.showerror("Error", f"No se pudo cargar el modelo Whisper: {e}")


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
    combobox_modelo
):

    global transcripcion_activa, transcripcion_en_curso, model_whisper
    from reproductor import reproductor
    if reproductor.reproduciendo:
        messagebox.showwarning(
            "Advertencia",
            "Hay una reproducción en curso. Por favor, detenga la reproducción antes de transcribir.",
        )
        return

    seleccion = lista_archivos.curselection()
    if not seleccion:
        messagebox.showwarning("Advertencia", "Seleccione un archivo de audio para transcribir.")
        transcripcion_en_curso = False
        return

    if transcripcion_activa:
        transcripcion_activa = False
        transcripcion_en_curso = False
        boton_transcribir.config(text="Transcribir")
        progress_bar["value"] = 0
        progress_bar.pack_forget()
        archivo_procesando.set("")
    else:
        transcripcion_activa = True
        transcripcion_en_curso = True
        boton_transcribir.config(text="Detener Transcripción")
        progress_bar["value"] = 0
        progress_bar.pack(pady=5, padx=60, fill=tk.X)

        # Cargar el modelo seleccionado
        modelo_seleccionado = combobox_modelo.get()
        cargar_modelo_whisper(modelo_seleccionado)

        threading.Thread(
            target=iniciar_transcripcion,
            args=(
                lista_archivos,
                text_area,
                archivo_procesando,
                lista_archivos_paths,
                progress_bar,
                ventana,
                boton_transcribir,
                combobox_idioma_entrada,
            ),
            daemon=True,
        ).start()


def actualizar_progreso_simple(progress_bar, ventana, archivo_procesando, audio_file, filename):
    global transcripcion_activa
    duracion = obtener_duracion_audio(audio_file)
    tiempo_estimado = duracion * 1.2  # Asumimos que la transcripción toma 1.2 veces la duración del audio
    intervalo = tiempo_estimado / 100  # Dividimos el tiempo estimado en 100 partes

    tiempo_inicio = time.time()
    for progreso in range(1, 101):
        if not transcripcion_activa:
            break

        ventana.after(0, lambda p=progreso: progress_bar.config(value=p))
        ventana.after(0, lambda f=filename, p=progreso: archivo_procesando.set(f"Procesando: {f} - {p}% completado"))

        tiempo_transcurrido = time.time() - tiempo_inicio
        tiempo_espera = (progreso * intervalo) - tiempo_transcurrido
        if tiempo_espera > 0:
            time.sleep(tiempo_espera)


def procesar_audio_whisper_por_fragmentos(audio_file, model, progress_bar, ventana, archivo_procesando):

    filename = os.path.basename(audio_file)

    # Iniciar la actualización de progreso en un hilo separado
    hilo_progreso = threading.Thread(
        target=actualizar_progreso_simple,
        args=(
            progress_bar,
            ventana,
            archivo_procesando,
            audio_file,
            filename))
    hilo_progreso.start()

    try:
        # Usar Whisper para transcribir directamente el archivo de audio completo
        result = model.transcribe(audio_file, fp16=False)
        transcripcion_completa = result['text']

        # Asegurar que la barra de progreso llegue al 100%
        hilo_progreso.join()
        ventana.after(0, lambda: progress_bar.config(value=100))
        ventana.after(0, lambda f=filename: archivo_procesando.set(f"Completado: {f}"))

        # Calcular estadísticas
        palabras_totales = len(transcripcion_completa.split())
        inaudibles_totales = transcripcion_completa.count('[inaudible]')

        return {
            "filename": filename,
            "archivo": audio_file,
            "transcripcion": transcripcion_completa,
            "num_chunks": 1,
            "inaudibles": inaudibles_totales,
            "palabras": palabras_totales
        }

    except Exception as e:
        logger.error(f"Error al procesar el archivo de audio {audio_file}: {e}")
        return None


def dividir_audio_por_fragmentos(audio_path, duracion_fragmento_s=30):
    """
    Divide un archivo de audio en fragmentos de la duración especificada.

    :param audio_path: Ruta al archivo de audio
    :param duracion_fragmento_s: Duración de cada fragmento en segundos (por defecto 30 segundos)
    :return: Lista de fragmentos de audio y sus tiempos de inicio
    """
    audio = AudioSegment.from_file(audio_path)
    fragmentos = []
    tiempos_inicio = []

    duracion_fragmento_ms = duracion_fragmento_s * 1000  # Convertir segundos a milisegundos

    for i in range(0, len(audio), duracion_fragmento_ms):
        fragmento = audio[i:i + duracion_fragmento_ms]
        fragmentos.append(fragmento)
        tiempos_inicio.append(i / 1000.0)  # Ya está en segundos

    return fragmentos, tiempos_inicio


def procesar_audio_por_fragmentos_whisper(audio_file, model, progress_bar, ventana, archivo_procesando, idioma_entrada):
    """
    Procesa el archivo de audio en fragmentos, transcribiendo cada fragmento y detectando el idioma automáticamente.

    :param audio_file: Ruta al archivo de audio
    :param model: Modelo Whisper cargado
    :return: Transcripción completa uniendo los fragmentos y los idiomas detectados
    """
    fragmentos, tiempos_inicio = dividir_audio_por_fragmentos(audio_file)
    transcripcion_completa = ""
    segmentos_totales = []

    for idx, (fragmento, inicio_fragmento) in enumerate(zip(fragmentos, tiempos_inicio)):
        fragmento_filename = f"temp_fragmento_{idx}.wav"
        try:
            fragmento.export(fragmento_filename, format="wav")  # Exportamos el fragmento a un archivo temporal

            # Transcribir sin especificar 'language' para detección automática
            result = model.transcribe(fragmento_filename, fp16=False, language=idioma_entrada)

            # Iterar sobre los segmentos transcritos
            for segment in result['segments']:
                # Ajustar los tiempos de inicio y fin al tiempo global del audio
                segment_start = segment['start'] + inicio_fragmento
                segment_end = segment['end'] + inicio_fragmento
                segment_text = segment['text']

                # Agregar el segmento a la lista total de segmentos
                segmentos_totales.append({
                    'start': segment_start,
                    'end': segment_end,
                    'text': segment_text,
                })

                transcripcion_completa += segment_text + " "

        except Exception as e:
            logger.error(f"Error al procesar el fragmento {idx}: {e}")
        finally:
            if os.path.exists(fragmento_filename):
                os.remove(fragmento_filename)  # Asegurar la eliminación del archivo temporal

        # Actualizar la barra de progreso
        progress = ((idx + 1) / len(fragmentos)) * 100
        progress_bar["value"] = progress
        ventana.update_idletasks()

    # Calcular estadísticas
    palabras_totales = len(transcripcion_completa.split())
    inaudibles_totales = transcripcion_completa.count('[inaudible]')

    return {
        "filename": os.path.basename(audio_file),
        "archivo": audio_file,
        "transcripcion": transcripcion_completa,
        "num_chunks": len(fragmentos),
        "inaudibles": inaudibles_totales,
        "palabras": palabras_totales,
        "segmentos": segmentos_totales
    }


def format_time(seconds):
    return time.strftime('%H:%M:%S', time.gmtime(seconds))


def iniciar_transcripcion(
    lista_archivos,
    text_area,
    archivo_procesando,
    lista_archivos_paths,
    progress_bar,
    ventana,
    boton_transcribir,
    combobox_idioma_entrada,
):
    """
    Función principal para manejar la transcripción de audio usando Whisper.
    Procesa los archivos de audio seleccionados en la interfaz, actualiza la barra de progreso
    y muestra la transcripción con los idiomas detectados.
    """

    global transcripcion_en_curso
    seleccion = lista_archivos.curselection()

    if not seleccion:
        messagebox.showwarning("Advertencia", "Por favor, seleccione al menos un archivo para transcribir.")
        return

    archivos_seleccionados = [lista_archivos.get(i) for i in seleccion]
    total_archivos = len(archivos_seleccionados)

    transcripcion_en_curso = True
    boton_transcribir.config(text="Detener Transcripción")
    progress_bar.pack(pady=5, padx=60, fill=tk.X)
    idioma_entrada = idiomas.get(combobox_idioma_entrada.get())

    for index, archivo in enumerate(archivos_seleccionados):

        if not transcripcion_en_curso:
            break
        audio_file = next(key for key, value in lista_archivos_paths.items() if value == archivo)

        archivo_procesando.set(f"Procesando: {archivo} ({index + 1}/{total_archivos})")
        logger.info(f"Procesando archivo: {audio_file}")

        try:
            progress_bar["value"] = 0
            ventana.update_idletasks()

            # Procesar el archivo por fragmentos y obtener la transcripción y los idiomas detectados
            resultado_wisper_M = procesar_audio_por_fragmentos_whisper(
                audio_file, model_whisper, progress_bar, ventana, archivo_procesando, idioma_entrada)

            if resultado_wisper_M is None:
                messagebox.showwarning("Advertencia", "Se detuvo la transcripción.")
                break

            # Construir el texto transcrito con tiempos
            texto_transcrito_con_tiempos = ""
            for segment in resultado_wisper_M['segmentos']:
                start_time = format_time(segment['start'])
                end_time = format_time(segment['end'])
                texto_transcrito_con_tiempos += f"[{start_time}-{end_time}]: {segment['text']}\n"

            # Agregar información de idiomas detectados al texto transcrito
            nuevo_texto = f"Transcripción {archivo}:\n\n{texto_transcrito_con_tiempos}\nPalabras: {resultado_wisper_M['palabras']}\nInaudibles: {resultado_wisper_M['inaudibles']}\n\n"

            text_area.insert(tk.END, nuevo_texto)
            text_area.see(tk.END)

            # Actualizar barra de progreso para cada archivo
            progress_bar["value"] = ((index + 1) / total_archivos) * 100
            ventana.update_idletasks()

        except Exception as e:
            logger.error(f"Error al procesar el archivo {archivo}: {e}")
            messagebox.showerror("Error", f"Error al procesar el archivo {archivo}: {e}")

    # Limpiar el estado de la interfaz una vez finalizada la transcripción
    archivo_procesando.set("")

    if transcripcion_en_curso:
        messagebox.showinfo("Información", f"Transcripción completa para {total_archivos} archivo(s).")

    # Restaurar el estado inicial de los botones y la barra de progreso
    transcripcion_en_curso = False
    boton_transcribir.config(text="Transcribir")
    progress_bar.pack_forget()
    progress_bar["value"] = 0
    archivo_procesando.set("")
