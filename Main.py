import tkinter as tk
import Interfaz as ui
from googletrans import LANGUAGES
import Funcionalidad as func


def main():
    # Configurar el proxy automáticamente al inicio
    proxy_configurado = func.detectar_y_configurar_proxy()
    ventana = tk.Tk()
    ventana.title("Transcriptor de Audio a Texto")

    idiomas = {v.capitalize(): k for k, v in LANGUAGES.items()}
    ui.crear_interfaz(ventana, idiomas)

    # Centrar la ventana en la pantalla
    ui.centrar_ventana(ventana)

    if proxy_configurado:
        tk.messagebox.showinfo("Proxy", "Proxy configurado automáticamente.")
    else:
        tk.messagebox.showinfo("Proxy", "No se requiere proxy o no se pudo configurar.")
    # Ejecutar la aplicación
    ventana.mainloop()

    # Mostrar el estado del proxy al iniciar


if __name__ == "__main__":
    main()
