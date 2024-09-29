import tkinter as tk
from tkinter import messagebox
from interfaz import crear_interfaz, centrar_ventana
from config import *
from reproductor import pygame
# from password_window import PasswordWindow


def main():
    try:
        pygame.mixer.init()
        ventana = tk.Tk()
        ventana.title("AudioText")
        icon_path = resource_path("icons/icono.ico")
        ventana.iconbitmap(icon_path)
        crear_interfaz(ventana)
        centrar_ventana(ventana)

        # ventana.withdraw()  # Oculta la ventana principal
        # PasswordWindow(ventana)  # Crea la ventana de contraseña

        # Ejecutar la aplicación
        ventana.mainloop()

    except Exception as e:
        messagebox.showerror("Error", f"Se produjo un error: {str(e)}")


if __name__ == "__main__":
    main()
