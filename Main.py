import tkinter as tk
import Interfaz as ui
from googletrans import LANGUAGES


def main():
    ventana = tk.Tk()
    ventana.title("Transcriptor de Audio a Texto")

    idiomas = {v.capitalize(): k for k, v in LANGUAGES.items()}
    ui.crear_interfaz(ventana, idiomas)

    # Centrar la ventana en la pantalla
    ui.centrar_ventana(ventana)

    # Ejecutar la aplicación
    ventana.mainloop()


if __name__ == "__main__":
    main()
