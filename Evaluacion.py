from tkinter import messagebox
from tkinter import filedialog
from tkinter import ttk
import csv
import os
import speech_recognition as sr
from pydub import AudioSegment
from pydub.silence import split_on_silence
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import io
from Config import logger, ffmpeg_path, ffprobe_path

# Inicializar el reconocedor
recognizer = sr.Recognizer()

# Configuración de AudioSegment
AudioSegment.converter = ffmpeg_path
AudioSegment.ffmpeg = ffmpeg_path
AudioSegment.ffprobe = ffprobe_path


def mejorar_audio(audio, highpass_cutoff=300):
    try:
        audio = audio.set_channels(1)  # Convertir a mono
        audio = audio.high_pass_filter(highpass_cutoff)
        audio = audio.normalize()
        return audio
    except Exception as e:
        logger.error(f"Error en mejorar_audio: {e}")
        return audio


def contar_palabras_y_inaudibles(texto):
    palabras = texto.split()
    inaudibles = palabras.count("[inaudible]")
    palabras_sin_inaudibles = len(palabras) - inaudibles
    return palabras_sin_inaudibles, inaudibles


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


def evaluar_parametros(audio_file, idioma_entrada, text_area, progress_bar, ventana):
    resultados = []

    # Definir rangos de parámetros para evaluar
    highpass_cutoff_values = [80, 150, 300]
    min_silence_len_values = [200, 500, 800]
    silence_thresh_values = [-20, -25, -30]  # Estos valores se ajustarán a audio.dBFS

    audio = AudioSegment.from_file(audio_file)
    silence_thresh_base = audio.dBFS

    for highpass_cutoff in highpass_cutoff_values:
        for min_silence_len in min_silence_len_values:
            for silence_thresh in silence_thresh_values:
                # Procesar audio con parámetros actuales
                filtered_audio = mejorar_audio(audio, highpass_cutoff)
                chunks = split_on_silence(
                    filtered_audio,
                    min_silence_len=min_silence_len,
                    silence_thresh=silence_thresh_base + silence_thresh,
                    keep_silence=100
                )

                # Transcribir los chunks
                transcripcion_completa = []
                for i, chunk in enumerate(chunks):
                    _, texto = transcribir_chunk(recognizer, chunk, idioma_entrada, i)
                    transcripcion_completa.append(texto)

                # Unir todos los textos transcritos en una sola cadena
                transcripcion_final = " ".join(transcripcion_completa).strip()

                # Contar palabras y [inaudible] en la transcripción final
                palabras_sin_inaudibles, inaudibles = contar_palabras_y_inaudibles(transcripcion_final)

                # Guardar el resultado y parámetros
                resultados.append({
                    "highpass_cutoff": highpass_cutoff,
                    "min_silence_len": min_silence_len,
                    "silence_thresh": silence_thresh,
                    "transcripcion": transcripcion_final,
                    "num_chunks": len(chunks),
                    "palabras_sin_inaudibles": palabras_sin_inaudibles,
                    "inaudibles": inaudibles
                })

                # Mostrar resultados parciales
                text_area.insert(tk.END, f"Evaluación con: highpass_cutoff={highpass_cutoff}, "
                                         f"min_silence_len={min_silence_len}, "
                                         f"silence_thresh={silence_thresh_base + silence_thresh}\n")
                text_area.insert(tk.END, f"Transcripción:\n{transcripcion_final}\n\n")
                text_area.insert(tk.END, f"Cantidad de palabras reconocidas (sin [inaudible]): {palabras_sin_inaudibles}\n")
                text_area.insert(tk.END, f"Cantidad de [inaudible]: {inaudibles}\n\n")
                text_area.see(tk.END)

                progress_bar["value"] += 1
                ventana.update_idletasks()

    return resultados


def guardar_resultados_csv(resultados, filename="resultados_evaluacion.csv"):
    keys = resultados[0].keys()
    with open(filename, 'w', newline='') as output_file:
        dict_writer = csv.DictWriter(output_file, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(resultados)


def on_click_evaluar():
    audio_file = filedialog.askopenfilename(filetypes=[("Audio Files", "*.wav *.mp3 *.ogg *.flac")])
    if not audio_file:
        return

    progress_bar["maximum"] = 27  # Número de combinaciones de parámetros a evaluar
    text_area.delete("1.0", tk.END)
    resultados = evaluar_parametros(audio_file, "es-ES", text_area, progress_bar, ventana)
    guardar_resultados_csv(resultados)
    messagebox.showinfo("Evaluación Completa", "La evaluación de parámetros ha finalizado.")


# Crear ventana principal
ventana = tk.Tk()
ventana.title("Evaluación de Parámetros de Transcripción")

# Crear área de texto para mostrar resultados
text_area = tk.Text(ventana, wrap="word", height=20, width=80)
text_area.pack(pady=10)

# Crear barra de progreso
progress_bar = ttk.Progressbar(ventana, orient="horizontal", mode="determinate")
progress_bar.pack(fill=tk.X, padx=10, pady=5)

# Crear botón para iniciar la evaluación de parámetros
boton_evaluar = tk.Button(ventana, text="Evaluar Parámetros", command=on_click_evaluar)
boton_evaluar.pack(pady=10)

# Ejecutar el bucle principal de la interfaz
ventana.mainloop()
