import tkinter as tk
from tkinter import messagebox
from Interfaz import crear_interfaz, centrar_ventana
from Config import detectar_y_configurar_proxy, check_dependencies, logger
from Reproductor import pygame
import os, sys


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def main():
    try:
        # Configurar el proxy automáticamente al inicio
        proxy_configurado = detectar_y_configurar_proxy()

        # Inicializar pygame mixer
        pygame.mixer.init()

        ventana = tk.Tk()
        ventana.title("AudioText")
        icon_path = resource_path("icons/icono.ico")
        ventana.iconbitmap(icon_path)
        crear_interfaz(ventana)

        # Centrar la ventana en la pantalla
        centrar_ventana(ventana)

        verificado = check_dependencies()
        if verificado:
            messagebox.showerror("Error", "Error en la verificación de dependencias.")
            logger.error("Error en la verificación de dependencias.")
            return
        else:
            messagebox.showinfo("Dependencias", "Dependencias verificadas.")
            logger.info("Dependencias verificadas.")

        # Ejecutar la aplicación
        ventana.mainloop()

    except Exception as e:
        messagebox.showerror("Error", f"Se produjo un error: {str(e)}")


if __name__ == "__main__":

    main()
