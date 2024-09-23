import io
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
from Config import *
from pydub import AudioSegment
from Config import logger
from tkinter import messagebox, filedialog
import numpy as np


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


# def traducir_texto(texto, idioma_salida):
#     try:
#         if check_proxy() == "Proxy configurado:":
#             proxy_config = {
#                 "http": "http://proxy.psa.gob.ar:3128",
#                 "https": "http://proxy.psa.gob.ar:3128",
#             }
#             translator = Translator(proxies=proxy_config)
#         else:
#             translator = Translator()

#         traduccion = translator.translate(texto, dest=idioma_salida)
#         if traduccion:
#             logger.info(f"Texto traducido: {traduccion.text}")
#             return traduccion.text
#         else:
#             logger.error("La traducción devolvió un resultado vacío.")
#             return f"Error al traducir el texto."
#     except Exception as e:
#         logger.error(f"Error al traducir texto: {e}")
#         return f"Error al traducir texto: {e}"


def traducir_texto(texto, idioma_salida):
    try:
        proxy = obtener_configuracion_proxy_windows()
        print(proxy)
        if proxy:
            os.environ['http_proxy'] = f"http://{proxy}"
            os.environ['https_proxy'] = f"http://{proxy}"
            translator = Translator(proxies={'http': f"http://{proxy}", 'https': f"http://{proxy}"})
        else:
            translator = Translator()

        logger.info(f"Intentando traducir texto de longitud {len(texto)} a {idioma_salida}")

        # Verificar si el idioma de salida es válido
        if idioma_salida not in LANGUAGES.values():
            logger.error(f"Idioma de salida no válido: {idioma_salida}")
            return f"Error: Idioma de salida no válido ({idioma_salida})"

        traduccion = translator.translate(texto, dest=idioma_salida)
        if traduccion and traduccion.text:
            logger.info("Traducción exitosa")
            return traduccion.text
        else:
            logger.error("La traducción devolvió un resultado vacío")
            return "Error: No se pudo obtener una traducción."
    except AttributeError as e:
        logger.error(f"Error de atributo al traducir: {str(e)}")
        return f"Error de configuración en la traducción: {str(e)}"
    except Exception as e:
        logger.error(f"Error detallado al traducir texto: {str(e)}")
        return f"Error al traducir texto: {str(e)}"


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
    checkBox,
):

    global transcripcion_en_curso

    try:
        seleccion = lista_archivos.curselection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Por favor, seleccione al menos un archivo para transcribir.")
            return

        archivos_seleccionados = [lista_archivos.get(i) for i in seleccion]
        total_archivos = len(archivos_seleccionados)

        idioma_salida = idiomas[combobox_idioma_salida.get()]

        transcripcion_en_curso = True
        boton_transcribir.config(text="Detener Transcripción")
        progress_bar.pack(pady=5, padx=60, fill=tk.X)

        for index, archivo in enumerate(archivos_seleccionados):

            if not transcripcion_en_curso:
                break
            audio_file = next(key for key, value in lista_archivos_paths.items() if value == archivo)

            archivo_procesando.set(f"Procesando: {archivo} ({index + 1}/{total_archivos})")
            logger.info(f"Procesando archivo: {audio_file}")

            try:
                progress_bar["value"] = 0
                ventana.update_idletasks()

                resultado_wisper_M = procesar_audio_whisper_por_fragmentos(
                    audio_file, model_whisper, progress_bar, ventana, archivo_procesando)

                if resultado_wisper_M is None:
                    messagebox.showwarning("Advertencia", "Se detuvo la transcripción.")
                    break

                Traducir = checkBox.get()
                if Traducir:
                    resultado_wisper_M['transcripcion'] = traducir_texto(resultado_wisper_M['transcripcion'], idioma_salida)

                if transcripcion_en_curso:
                    texto_transcrito = ajustar_texto_sencillo(resultado_wisper_M['transcripcion'])
                    nuevo_texto = f"Transcripción {archivo}: \n{texto_transcrito} \n\nPalabras: {resultado_wisper_M['palabras']} \nInaudibles: {resultado_wisper_M['inaudibles']}\n\n"
                    text_area.insert(tk.END, nuevo_texto)
                    text_area.see(tk.END)

                progress_bar["value"] = ((index + 1) / total_archivos) * 100
                ventana.update_idletasks()

            except Exception as e:
                logger.error(f"Error al procesar el archivo {archivo}: {e}")
                messagebox.showerror("Error", f"Error al procesar el archivo {archivo}: {e}")

        archivo_procesando.set("")

        if transcripcion_en_curso:
            messagebox.showinfo("Información", f"Transcripción completa para {total_archivos} archivo(s).")

    except Exception as e:
        logger.error(f"Error durante la transcripción: {e}")
        messagebox.showerror("Error", f"Ocurrió un error durante la transcripción: {e}")

    finally:
        transcripcion_en_curso = False
        boton_transcribir.config(text="Transcribir")
        progress_bar.pack_forget()
        progress_bar["value"] = 0
        archivo_procesando.set("")


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
    combobox_idioma_salida,
    checkBox,
    combobox_modelo
):
    global transcripcion_activa, transcripcion_en_curso, model_whisper
    from Reproductor import reproductor

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
                transcripcion_resultado,
                progress_bar,
                ventana,
                boton_transcribir,
                combobox_idioma_salida,
                checkBox,
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
