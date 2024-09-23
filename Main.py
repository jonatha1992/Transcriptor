import tkinter as tk
from tkinter import messagebox
from Interfaz import crear_interfaz, centrar_ventana
from Config import *
from Reproductor import pygame


def main():
    try:
        obtener_configuracion_proxy_windows()
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
