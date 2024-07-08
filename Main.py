import tkinter as tk
from Interfaz import crear_interfaz, centrar_ventana
from Config import detectar_y_configurar_proxy
from Reproductor import pygame


def main():
    # Configurar el proxy automáticamente al inicio
    proxy_configurado = detectar_y_configurar_proxy()

    # Inicializar pygame mixer
    pygame.mixer.init()

    ventana = tk.Tk()
    ventana.title("Transcriptor")
    ventana.iconbitmap("icono.ico")

    crear_interfaz(ventana)

    # Centrar la ventana en la pantalla
    centrar_ventana(ventana)

    if proxy_configurado:
        tk.messagebox.showinfo("Proxy", "Proxy configurado automáticamente.")
    else:
        tk.messagebox.showinfo("Proxy", "No se requiere proxy o no se pudo configurar.")

    # Ejecutar la aplicación
    ventana.mainloop()


if __name__ == "__main__":
    main()
