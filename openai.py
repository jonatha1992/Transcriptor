import os
import torch
import torchaudio
from transformers import WhisperForConditionalGeneration, WhisperProcessor
from pydub import AudioSegment
from pydub.silence import split_on_silence
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import io
from Config import logger, ffmpeg_path, ffprobe_path
import warnings

# Suprimir advertencias específicas
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# Configurar ffmpeg
AudioSegment.converter = ffmpeg_path
AudioSegment.ffmpeg = ffmpeg_path
AudioSegment.ffprobe = ffprobe_path

# Cargar el modelo y el procesador Whisper
model = WhisperForConditionalGeneration.from_pretrained("openai/whisper-small")
processor = WhisperProcessor.from_pretrained("openai/whisper-small")


def mejorar_audio(audio, highpass_cutoff=300):
    try:
        audio = audio.set_channels(1)  # Convertir a mono
        audio = audio.high_pass_filter(highpass_cutoff)
        audio = audio.normalize()
        return audio
    except Exception as e:
        logger.error(f"Error en mejorar_audio: {e}")
        return audio


def transcribir_chunk(audio_chunk, indice):
    try:
        if len(audio_chunk) == 0:
            return indice, "[chunk vacío]"

        # Convertir el chunk a un archivo WAV en memoria
        buffer = io.BytesIO()
        audio_chunk.export(buffer, format="wav")
        buffer.seek(0)

        # Cargar el audio con torchaudio
        waveform, sample_rate = torchaudio.load(buffer)

        # Asegurarse de que el audio esté a 16000 Hz
        if sample_rate != 16000:
            resampler = torchaudio.transforms.Resample(orig_freq=sample_rate, new_freq=16000)
            waveform = resampler(waveform)

        # Asegurarse de que el tensor tenga la forma correcta
        if waveform.dim() == 2 and waveform.size(0) > 1:
            waveform = waveform.mean(dim=0, keepdim=True)

        logger.info(f"Tamaño del tensor después de la manipulación: {waveform.shape}")

        # Procesar el audio con el procesador de Whisper
        inputs = processor(waveform.squeeze().numpy(), sampling_rate=16000, return_tensors="pt")
        input_features = inputs.input_features

        # Obtener los IDs de los decodificadores forzados para el idioma español
        forced_decoder_ids = processor.get_decoder_prompt_ids(language="es", task="translate")
        attention_mask = torch.ones(input_features.shape[:2], dtype=torch.long)

        # Generar la transcripción traducida al español
        with torch.no_grad():
            generated_tokens = model.generate(
                input_features,
                attention_mask=attention_mask,
                forced_decoder_ids=forced_decoder_ids
            )

        # Decodificar la transcripción
        transcription = processor.batch_decode(generated_tokens, skip_special_tokens=True)
        texto = transcription[0]

    except Exception as e:
        texto = f"[error: {str(e)}]"
        logger.error(f"Error al procesar chunk {indice}: {e}")

    return indice, texto


def contar_palabras_y_errores(texto):
    palabras = texto.split()
    errores = sum(1 for palabra in palabras if palabra.startswith("[error:"))
    palabras_validas = len(palabras) - errores
    return palabras_validas, errores


def evaluar_parametros(audio_file, text_area, progress_bar, ventana):
    resultados = []

    # Definir rangos de parámetros para evaluar
    highpass_cutoff_values = [80, 150, 300]
    min_silence_len_values = [200, 500, 800]
    silence_thresh_values = [-20, -25, -30]  # Estos valores se ajustarán a audio.dBFS

    try:
        audio = AudioSegment.from_file(audio_file)
    except Exception as e:
        logger.error(f"Error al cargar el archivo de audio: {e}")
        messagebox.showerror("Error", f"No se pudo cargar el archivo de audio: {e}")
        return []

    silence_thresh_base = audio.dBFS

    for highpass_cutoff in highpass_cutoff_values:
        for min_silence_len in min_silence_len_values:
            for silence_thresh in silence_thresh_values:
                try:
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

                    # Contar palabras válidas y errores en la transcripción final
                    palabras_validas, errores = contar_palabras_y_errores(transcripcion_final)

                    # Guardar el resultado y parámetros
                    resultados.append({
                        "highpass_cutoff": highpass_cutoff,
                        "min_silence_len": min_silence_len,
                        "silence_thresh": silence_thresh,
                        "transcripcion": transcripcion_final,
                        "num_chunks": len(chunks),
                        "palabras_validas": palabras_validas,
                        "errores": errores
                    })

                    # Mostrar resultados parciales
                    text_area.insert(tk.END, f"Evaluación con: highpass_cutoff={highpass_cutoff}, "
                                             f"min_silence_len={min_silence_len}, "
                                             f"silence_thresh={silence_thresh_base + silence_thresh}\n")
                    text_area.insert(tk.END, f"Transcripción:\n{transcripcion_final}\n\n")
                    text_area.insert(tk.END, f"Palabras válidas reconocidas: {palabras_validas}\n")
                    text_area.insert(tk.END, f"Errores de transcripción: {errores}\n\n")
                    text_area.see(tk.END)

                except Exception as e:
                    logger.error(f"Error en la evaluación de parámetros: {e}")
                    text_area.insert(tk.END, f"Error en la evaluación: {str(e)}\n\n")
                    text_area.see(tk.END)

                progress_bar["value"] += 1
                ventana.update_idletasks()

    return resultados


def guardar_resultados_csv(resultados, filename="resultados_evaluacion.csv"):
    import csv
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
