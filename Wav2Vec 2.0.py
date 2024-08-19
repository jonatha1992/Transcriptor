import csv
import os
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
import torchaudio
import torch
from pydub import AudioSegment
from pydub.silence import split_on_silence
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import io
from Config import logger, ffmpeg_path, ffprobe_path

# Cargar el modelo y el procesador de Wav2Vec 2.0 entrenado para español
processor = Wav2Vec2Processor.from_pretrained("jonatasgrosman/wav2vec2-large-xlsr-53-spanish")
model = Wav2Vec2ForCTC.from_pretrained("jonatasgrosman/wav2vec2-large-xlsr-53-spanish")

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
        print(f"Error en mejorar_audio: {e}")
        return audio


def transcribir_chunk(audio_chunk, indice):
    try:
        # Convertir el fragmento de audio a tensor
        audio_tensor = torch.tensor(audio_chunk.get_array_of_samples(), dtype=torch.float32)
        audio_tensor = audio_tensor / 32768.0  # Normalizar el tensor

        # Asegurarse de que el audio esté a 16kHz
        if audio_chunk.frame_rate != 16000:
            resampled_tensor = torchaudio.transforms.Resample(orig_freq=audio_chunk.frame_rate, new_freq=16000)(audio_tensor)
        else:
            resampled_tensor = audio_tensor

        inputs = processor(resampled_tensor, sampling_rate=16000, return_tensors="pt", padding=True)
        with torch.no_grad():
            logits = model(inputs.input_values).logits

        predicted_ids = torch.argmax(logits, dim=-1)
        texto = processor.decode(predicted_ids[0])
        return indice, texto
    except Exception as e:
        print(f"Error al procesar chunk {indice}: {e}")
        return indice, f"[error: {str(e)}]"


def evaluar_parametros(audio_file, text_area, progress_bar, ventana):
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
                    _, texto = transcribir_chunk(chunk, i)
                    transcripcion_completa.append(texto)

                # Unir todos los textos transcritos en una sola cadena
                transcripcion_final = " ".join(transcripcion_completa).strip()

                # Contar palabras en la transcripción final
                num_palabras = len(transcripcion_final.split())

                # Guardar el resultado y parámetros
                resultados.append({
                    "highpass_cutoff": highpass_cutoff,
                    "min_silence_len": min_silence_len,
                    "silence_thresh": silence_thresh,
                    "transcripcion": transcripcion_final,
                    "num_chunks": len(chunks),
                    "num_palabras": num_palabras  # Añadir número de palabras al resultado
                })

                # Mostrar resultados parciales
                text_area.insert(tk.END, f"Evaluación con: highpass_cutoff={highpass_cutoff}, "
                                         f"min_silence_len={min_silence_len}, "
                                         f"silence_thresh={silence_thresh_base + silence_thresh}\n")
                text_area.insert(tk.END, f"Transcripción:\n{transcripcion_final}\n\n")
                text_area.insert(tk.END, f"Cantidad de palabras reconocidas: {num_palabras}\n\n")
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
    resultados = evaluar_parametros(audio_file, text_area, progress_bar, ventana)
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
