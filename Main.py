import tkinter as tk
from tkinter import messagebox
from Interfaz import crear_interfaz, centrar_ventana
from Config import detectar_y_configurar_proxy, check_dependencies, logger, resource_path
from Funcionalidad import cargar_modelo_whisper
from Reproductor import pygame


def main():
    try:
        detectar_y_configurar_proxy()
        cargar_modelo_whisper()
        pygame.mixer.init()
        ventana = tk.Tk()
        ventana.title("AudioText")
        icon_path = resource_path("icons/icono.ico")
        ventana.iconbitmap(icon_path)
        crear_interfaz(ventana)
        centrar_ventana(ventana)

        # Ejecutar la aplicación
        ventana.mainloop()

    except Exception as e:
        messagebox.showerror("Error", f"Se produjo un error: {str(e)}")


if __name__ == "__main__":
    main()
