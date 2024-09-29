import datetime
import hashlib
from tkinter import messagebox
from interfaz import centrar_ventana
import tkinter as tk

CLAVE_FIJA = "291292"


class PasswordWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Verificación")
        self.geometry("300x120")
        self.resizable(False, False)
        centrar_ventana(self)

        self.label = tk.Label(self, text="Ingrese la contraseña:")
        self.label.pack(pady=10)

        self.entry = tk.Entry(self, width=20)
        self.entry.pack(pady=5)
        self.entry.focus_set()

        self.button = tk.Button(self, text="Verificar", command=self.verificar)
        self.button.pack(pady=10)

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.transient(parent)
        self.grab_set()

    def verificar(self):
        hash_ingresado = self.entry.get()
        fecha_actual = datetime.datetime.now()

        fecha_caducidad = self.extraer_fecha_caducidad(hash_ingresado)

        if fecha_caducidad:
            if fecha_actual <= fecha_caducidad:
                self.destroy()
                self.parent.deiconify()
            else:
                messagebox.showerror("Error", "La contraseña ha caducado.")
                self.parent.quit()
        else:
            messagebox.showerror("Error", "la constreseña es inválida.")
            self.entry.delete(0, tk.END)

    def extraer_fecha_caducidad(self, hash_ingresado):
        fecha_prueba = datetime.datetime.now()

        for _ in range(3650):  # Probar hasta 10 años en el futuro
            combinacion = f"{fecha_prueba.strftime('%d/%m/%Y')}:{CLAVE_FIJA}"
            hash_prueba = hashlib.sha1(combinacion.encode()).hexdigest()
            hash_prueba = hash_prueba[:12]

            if hash_prueba == hash_ingresado:
                return fecha_prueba

            fecha_prueba += datetime.timedelta(days=1)

        return None  # No se encontró una fecha válida

    def on_closing(self):
        self.parent.quit()
