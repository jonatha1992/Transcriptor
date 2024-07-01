import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import speech_recognition as sr
import threading

# Inicializar el reconocedor
recognizer = sr.Recognizer()

# Variable global para controlar el estado de la transcripción
transcripcion_activa = False


# Función para transcribir archivos WAV
def transcribir_archivo(audio_path):
    try:
        with sr.AudioFile(audio_path) as source:
            audio = recognizer.record(source)
            text = recognizer.recognize_google(audio, language="es-ES")
            return text
    except sr.UnknownValueError:
        return "Audio no claro / inaudible."
    except sr.RequestError as e:
        return f"Error en el servicio de reconocimiento: {e}"
    except Exception as e:
        return f"Error al procesar el archivo: {e}"


# Función para seleccionar archivos WAV
def seleccionar_archivos():
    file_paths = filedialog.askopenfilenames(
        filetypes=[("Archivos WAV", "*.wav")], title="Seleccionar archivos WAV"
    )
    archivos_no_agregados = []
    if file_paths:
        for file_path in file_paths:
            file_name = os.path.basename(file_path)
            if file_name not in lista_archivos.get(0, tk.END):
                lista_archivos.insert(tk.END, file_name)
                lista_archivos_paths[file_path] = file_name
            else:
                archivos_no_agregados.append(file_name)
        if archivos_no_agregados:
            messagebox.showwarning(
                "Archivos Duplicados",
                f"Los siguientes archivos ya estaban en la lista y no se añadieron nuevamente:\n{', '.join(archivos_no_agregados)}",
            )


# Función para iniciar la transcripción en un hilo separado
def iniciar_transcripcion_thread():
    global transcripcion_activa
    if transcripcion_activa:
        transcripcion_activa = False
        boton_transcribir.config(text="Iniciar Transcripción")
    else:
        transcripcion_activa = True
        boton_transcribir.config(text="Detener Transcripción")
        progress_bar["value"] = 0
        progress_bar.pack(
            pady=10, padx=60, fill=tk.X
        )  # Hacer visible la barra de progreso
        threading.Thread(target=iniciar_transcripcion).start()


# Función para iniciar la transcripción
def iniciar_transcripcion():
    global transcripcion_activa
    archivos = lista_archivos.get(0, tk.END)
    if not archivos:
        messagebox.showwarning("Advertencia", "Seleccione al menos un archivo WAV.")
        return

    transcripcion_total = ""
    text_area.delete("1.0", tk.END)

    progress_bar["maximum"] = len(archivos)
    for i, archivo in enumerate(archivos):
        if not transcripcion_activa:
            break
        audio_file = next(
            key for key, value in lista_archivos_paths.items() if value == archivo
        )
        archivo_procesando.set(f"Procesando: {archivo}")
        print(f"Procesando archivo: {audio_file}")
        transcripcion = transcribir_archivo(audio_file)

        # Agregar la transcripción al texto total
        transcripcion_total += f"Transcripción de {archivo}:\n{transcripcion}\n\n"
        text_area.insert(tk.END, f"Transcripción de {archivo}:\n{transcripcion}\n\n")

        progress_bar["value"] = i + 1
        ventana.update_idletasks()

    archivo_procesando.set("")
    if transcripcion_activa:
        messagebox.showinfo("Información", "Transcripción completa.")
        boton_transcribir.config(text="Iniciar Transcripción")
        transcripcion_activa = False
        progress_bar.pack_forget()  # Ocultar la barra de progreso
        progress_bar["value"] = 0

    global transcripcion_resultado
    transcripcion_resultado = transcripcion_total


# Función para exportar la transcripción a un archivo de texto
def exportar_transcripcion():
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
        print(f"Transcripción guardada en {output_file}.")


# Función para centrar la ventana en la pantalla
def centrar_ventana(ventana):
    ventana.update_idletasks()
    ancho_ventana = ventana.winfo_width()
    alto_ventana = ventana.winfo_height()
    ancho_pantalla = ventana.winfo_screenwidth()
    alto_pantalla = ventana.winfo_screenheight()
    x = (ancho_pantalla // 2) - (ancho_ventana // 2)
    y = (alto_pantalla // 2) - (alto_ventana // 2)
    ventana.geometry(f"{ancho_ventana}x{alto_ventana}+{x}+{y}")
