import random
import shutil
import tempfile
from tkinter import messagebox
import whisper
import os
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
import io
from contextlib import redirect_stdout, redirect_stderr
import sys


def redirect_ffmpeg_output():
    if sys.platform == 'win32':
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        return {'startupinfo': si, 'creationflags': subprocess.CREATE_NO_WINDOW}
    return {}

# Sobrescribir la función _run de whisper.audio


def custom_run(cmd, **kwargs):
    kwargs.update(redirect_ffmpeg_output())
    return subprocess.run(cmd, **kwargs)


whisper.audio._run = custom_run


def convertir_a_wav(audio_path):
    try:
        logger.info(f"Intentando convertir: {audio_path}")
        audio_format = audio_path.split(".")[-1]
        logger.info(f"Formato de audio detectado: {audio_format}")
        output_path = audio_path.replace(audio_format, "wav")

        if os.path.exists(output_path):
            logger.info(f"El archivo WAV ya existe: {output_path}")
            return output_path

        command = [ffmpeg_path, "-i", audio_path, output_path]

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            **redirect_ffmpeg_output()
        )

        stdout, stderr = process.communicate()

        if process.returncode != 0:
            logger.error(f"FFmpeg error: {stderr.decode('utf-8')}")
            raise subprocess.CalledProcessError(process.returncode, command, stderr)

        logger.info(f"Archivo convertido a WAV: {output_path}")
        return output_path
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg proceso devolvió un error: {e.stderr.decode('utf-8')}")
        raise
    except FileNotFoundError as e:
        logger.error(f"FFmpeg no encontrado: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error al convertir archivo a WAV: {str(e)}")
        raise


def obtener_duracion_audio(ruta_archivo):
    try:
        audio = File(ruta_archivo)
        if audio is not None and hasattr(audio.info, 'length'):
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

    try:
        result = subprocess.run(
            [ffprobe_path, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", ruta_archivo],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            **redirect_ffmpeg_output()
        )
        return int(float(result.stdout))
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
    inaudibles = palabras.count('[inaudible]')
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

        with io.StringIO() as buf, redirect_stdout(buf), redirect_stderr(buf):
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
    var_idioma_entrada,
    var_idioma_salida,
    combobox_idioma_entrada,
    combobox_idioma_salida,
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
                var_idioma_entrada,
                var_idioma_salida,
                combobox_idioma_entrada,
                combobox_idioma_salida,
            ),
            daemon=True,
        ).start()


def actualizar_progreso_simple(progress_bar, ventana, archivo_procesando, audio_file, filename):
    global transcripcion_activa
    duracion = obtener_duracion_audio(audio_file)
    tiempo_estimado = duracion * 1.2
    intervalo = tiempo_estimado / 100

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
        with io.StringIO() as buf, redirect_stdout(buf), redirect_stderr(buf):
            result = model.transcribe(audio_file, fp16=False)

        transcripcion_completa = result['text']

        hilo_progreso.join()
        ventana.after(0, lambda: progress_bar.config(value=100))
        ventana.after(0, lambda f=filename: archivo_procesando.set(f"Completado: {f}"))

        palabras_totales = len(transcripcion_completa.split())
        # inaudibles_totales = transcripcion_completa.count('[inaudible]')

        return {
            "filename": filename,
            "archivo": audio_file,
            "transcripcion": transcripcion_completa,
            "num_chunks": 1,
            # "duracion de transcripción": inaudibles_totales,
            "palabras": palabras_totales
        }

    except Exception as e:
        logger.error(f"Error al procesar el archivo de audio {audio_file}: {e}")
        return None


def dividir_audio_por_fragmentos(audio_path, duracion_fragmento_s=30):
    audio = AudioSegment.from_file(audio_path)
    fragmentos = []
    tiempos_inicio = []

    duracion_fragmento_ms = duracion_fragmento_s * 1000

    for i in range(0, len(audio), duracion_fragmento_ms):
        fragmento = audio[i:i + duracion_fragmento_ms]
        fragmentos.append(fragmento)
        tiempos_inicio.append(i / 1000.0)

    return fragmentos, tiempos_inicio


def format_time(seconds):
    return time.strftime('%H:%M:%S', time.gmtime(seconds))


def eliminar_archivo_con_reintento(ruta_archivo, max_intentos=5, retraso_base=0.1):
    for intento in range(max_intentos):
        try:
            os.unlink(ruta_archivo)
            return True
        except PermissionError:
            if intento < max_intentos - 1:
                time.sleep(retraso_base * (2 ** intento) + random.uniform(0, 0.1))
            else:
                logger.warning(f"No se pudo eliminar el archivo temporal: {ruta_archivo}")
                return False


def iniciar_transcripcion(
        lista_archivos,
        text_area,
        archivo_procesando,
        lista_archivos_paths,
        progress_bar,
        ventana,
        boton_transcribir,
        var_idioma_entrada,
        var_idioma_salida,
        combobox_idioma_entrada,
        combobox_idioma_salida,
):
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

    idioma_entrada = idiomas_invertidos.get(combobox_idioma_entrada.get()) if var_idioma_entrada.get() else None
    idioma_salida = idiomas_invertidos.get(combobox_idioma_salida.get()) if var_idioma_salida.get() else None

    tiempo_inicio_total = time.time()

    for index, archivo in enumerate(archivos_seleccionados):
        if not transcripcion_en_curso:
            break
        audio_file = next(key for key, value in lista_archivos_paths.items() if value == archivo)

        archivo_procesando.set(f"Procesando: {archivo} ({index + 1}/{total_archivos})")
        logger.info(f"Procesando archivo: {audio_file}")

        try:
            progress_bar["value"] = 0
            ventana.update_idletasks()

            iniciar_transcripcion_whisper = time.time()
            resultado_wisper_M = procesar_audio_por_fragmentos_whisper(
                audio_file, model_whisper, progress_bar, ventana, archivo_procesando,
                idioma_entrada, idioma_salida)
            tiempo_transcripcion = format_time(time.time() - iniciar_transcripcion_whisper)

            nuevo_texto = f"Transcripción {archivo}:\n\n"
            for segment in resultado_wisper_M['segmentos']:
                start_time = format_time(segment['start'])
                end_time = format_time(segment['end'])
                nuevo_texto += f"[{start_time}-{end_time}]: {segment['text']}\n"

            nuevo_texto += f"\nPalabras: {resultado_wisper_M['palabras']}\n"
            nuevo_texto += f"Tiempo de transcripción: {tiempo_transcripcion} \n"
            nuevo_texto += f"Idioma usado para transcripción: {resultado_wisper_M['idioma_usado']}\n"

            if resultado_wisper_M['idiomas_detectados']:
                nuevo_texto += "Idiomas detectados:\n"
                for lang, count in resultado_wisper_M['idiomas_detectados'].items():
                    nuevo_texto += f"  - {idiomas.get(lang, lang)}: {count} fragmento(s)\n"
            nuevo_texto += "\n"

            text_area.insert(tk.END, nuevo_texto)
            text_area.see(tk.END)

            progress_bar["value"] = ((index + 1) / total_archivos) * 100
            ventana.update_idletasks()

        except Exception as e:
            logger.error(f"Error al procesar el archivo {archivo}: {str(e)}", exc_info=True)
            messagebox.showerror("Error", f"Error al procesar el archivo {archivo}: {str(e)}")

    archivo_procesando.set("")

    tiempo_total = format_time(time.time() - tiempo_inicio_total)

    if transcripcion_en_curso:
        mensaje = f"Transcripción completa para {total_archivos} archivo(s).\n"
        mensaje += f"Tiempo total de transcripción: {tiempo_total}."
        text_area.insert(tk.END, mensaje)
        text_area.see(tk.END)
        messagebox.showinfo("Información", mensaje)
        logger.info(mensaje)

    transcripcion_en_curso = False
    boton_transcribir.config(text="Transcribir")
    progress_bar.pack_forget()
    progress_bar["value"] = 0
    archivo_procesando.set("")


def procesar_audio_por_fragmentos_whisper(
        audio_file,
        model,
        progress_bar,
        ventana,
        archivo_procesando,
        idioma_entrada=None,
        idioma_salida=None):

    fragmentos, tiempos_inicio = dividir_audio_por_fragmentos(audio_file)
    transcripcion_completa = ""
    segmentos_totales = []
    filename = os.path.basename(audio_file)
    idiomas_detectados = {}

    # Determinar el idioma a usar para la transcripción
    idioma_transcripcion = idioma_salida or idioma_entrada or None

    for idx, (fragmento, inicio_fragmento) in enumerate(zip(fragmentos, tiempos_inicio)):
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_file_path = temp_file.name
            try:
                fragmento.export(temp_file_path, format="wav")

                with io.StringIO() as buf, redirect_stdout(buf), redirect_stderr(buf):
                    # Detectamos el idioma solo si no se especificó idioma de entrada
                    if idioma_entrada is None:
                        audio = whisper.load_audio(temp_file_path)
                        audio = whisper.pad_or_trim(audio)
                        mel = whisper.log_mel_spectrogram(audio).to(model.device)
                        _, probs = model.detect_language(mel)
                        detected_lang = max(probs, key=probs.get)
                        idiomas_detectados[detected_lang] = idiomas_detectados.get(detected_lang, 0) + 1

                    # Realizamos la transcripción
                    if idioma_transcripcion:
                        result = model.transcribe(temp_file_path, fp16=False, language=idioma_transcripcion)
                    else:
                        result = model.transcribe(temp_file_path, fp16=False)

                for segment in result['segments']:
                    segment_start = segment['start'] + inicio_fragmento
                    segment_end = segment['end'] + inicio_fragmento
                    segment_text = segment['text']

                    segmentos_totales.append({
                        'start': segment_start,
                        'end': segment_end,
                        'text': segment_text
                    })

                    transcripcion_completa += segment_text + " "

            except Exception as e:
                logger.error(f"Error al procesar el fragmento {idx} de {filename}: {e}")
            finally:
                if not eliminar_archivo_con_reintento(temp_file_path):
                    logger.warning(f"No se pudo eliminar el archivo temporal: {temp_file_path}")

        progress = ((idx + 1) / len(fragmentos)) * 100
        ventana.after(0, lambda p=progress: progress_bar.config(value=p))
        ventana.after(0, lambda f=filename, p=int(progress): archivo_procesando.set(f"Procesando: {f} - {p}% completado"))

    palabras_totales = len(transcripcion_completa.split())
    return {
        "filename": filename,
        "archivo": audio_file,
        "transcripcion": transcripcion_completa,
        "num_chunks": len(fragmentos),
        "palabras": palabras_totales,
        "segmentos": segmentos_totales,
        "idioma_usado": idiomas.get(idioma_transcripcion, "auto-detectado") if idioma_transcripcion else "auto-detectado",
        "idiomas_detectados": idiomas_detectados if idioma_entrada is None else {}
    }
