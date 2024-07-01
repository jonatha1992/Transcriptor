import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import Funcionalidad as func


def crear_interfaz(ventana, idiomas):
    archivo_procesando = tk.StringVar()
    lista_archivos_paths = {}
    transcripcion_resultado = ""

    main_frame = tk.Frame(ventana)
    main_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

    label_titulo = tk.Label(
        main_frame, text="Transcriptor de Audio a Texto", font=("Helvetica", 16)
    )
    label_titulo.pack(side=tk.TOP, pady=5)

    # Frame para el listbox
    frame_listbox = tk.Frame(main_frame)
    frame_listbox.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=2)

    # Etiqueta para el listbox
    label_listbox = tk.Label(frame_listbox, text="Lista de archivos")
    label_listbox.pack(side=tk.TOP)

    # Listbox con scrollbar
    scrollbar_listbox = tk.Scrollbar(frame_listbox, orient=tk.VERTICAL)
    lista_archivos = tk.Listbox(
        frame_listbox,
        selectmode=tk.SINGLE,
        width=40,
        height=20,
        yscrollcommand=scrollbar_listbox.set,
    )
    lista_archivos.pack(side=tk.LEFT, fill=tk.BOTH)
    scrollbar_listbox.pack(side=tk.RIGHT, fill=tk.Y)
    scrollbar_listbox.config(command=lista_archivos.yview)

    # Frame para el Text widget y su scrollbar
    frame_text = tk.Frame(main_frame)
    frame_text.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=2)

    # Etiqueta para el Text area
    label_text_area = tk.Label(frame_text, text="Transcripción")
    label_text_area.pack(side=tk.TOP)

    # Text widget con scrollbar
    scrollbar_text = tk.Scrollbar(frame_text, orient=tk.VERTICAL)
    text_area = tk.Text(
        frame_text, height=25, width=81, yscrollcommand=scrollbar_text.set
    )
    text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar_text.pack(side=tk.RIGHT, fill=tk.Y)
    scrollbar_text.config(command=text_area.yview)

    # Frame para la barra de progreso
    frame_progress = tk.Frame(ventana)
    frame_progress.pack(fill=tk.X, padx=30, pady=0)

    progress_label = tk.Label(frame_progress, textvariable=archivo_procesando)
    progress_label.pack(pady=5)

    progress_bar = ttk.Progressbar(
        frame_progress, orient="horizontal", mode="determinate"
    )
    progress_bar.pack_forget()

    # Frame para los ComboBox de idiomas
    frame_idioma_entrada = tk.Frame(ventana)
    frame_idioma_entrada.pack(side=tk.TOP, pady=5)

    label_idioma_entrada = tk.Label(frame_idioma_entrada, text=" Idioma de Entrada:")
    label_idioma_entrada.pack(side=tk.LEFT, padx=10)

    combobox_idioma_entrada = ttk.Combobox(
        frame_idioma_entrada, values=list(idiomas.keys()), state="readonly"
    )
    combobox_idioma_entrada.set("Spanish")  # Valor por defecto
    combobox_idioma_entrada.pack(side=tk.LEFT, padx=10)

    frame_idioma_salida = tk.Frame(ventana)
    frame_idioma_salida.pack(side=tk.TOP, pady=5)

    label_idioma_salida = tk.Label(frame_idioma_salida, text="Idioma de Salida:")
    label_idioma_salida.pack(side=tk.LEFT, padx=10)

    combobox_idioma_salida = ttk.Combobox(
        frame_idioma_salida, values=list(idiomas.keys()), state="readonly"
    )
    combobox_idioma_salida.set("Spanish")  # Valor por defecto
    combobox_idioma_salida.pack(side=tk.LEFT, padx=10)

    # Frame para los botones
    frame_botones = tk.Frame(ventana)
    frame_botones.pack(side=tk.TOP, pady=10)

    boton_seleccionar = tk.Button(
        frame_botones,
        text="Seleccionar Archivos",
        command=lambda: func.seleccionar_archivos(lista_archivos, lista_archivos_paths),
    )
    boton_seleccionar.pack(side=tk.LEFT, padx=30)

    boton_transcribir = tk.Button(
        frame_botones,
        text="Iniciar Transcripción",
        command=lambda: func.iniciar_transcripcion_thread(
            lista_archivos,
            text_area,
            archivo_procesando,
            lista_archivos_paths,
            transcripcion_resultado,
            progress_bar,
            ventana,
            boton_transcribir,
            combobox_idioma_entrada,
            combobox_idioma_salida,
        ),
    )
    boton_transcribir.pack(side=tk.LEFT, padx=5)

    boton_exportar = tk.Button(
        frame_botones,
        text="Exportar",
        command=lambda: func.exportar_transcripcion(text_area.get("1.0", tk.END)),
    )
    boton_exportar.pack(side=tk.LEFT, padx=5)

    boton_limpiar = tk.Button(
        frame_botones,
        text="Limpiar",
        command=lambda: func.limpiar(lista_archivos, text_area),
    )
    boton_limpiar.pack(side=tk.LEFT, padx=20)

    # Frame para el label de créditos
    frame_creditos = tk.Frame(ventana)
    frame_creditos.pack(side=tk.BOTTOM, pady=5)

    label_creditos = tk.Label(frame_creditos, text="Producido por Correa Jonathan")
    label_creditos.pack()

    # Devolver variables necesarias para funcionalidad
    return {
        "lista_archivos": lista_archivos,
        "text_area": text_area,
        "progress_bar": progress_bar,
        "combobox_idioma_entrada": combobox_idioma_entrada,
        "combobox_idioma_salida": combobox_idioma_salida,
        "boton_transcribir": boton_transcribir,
        "archivo_procesando": archivo_procesando,
        "lista_archivos_paths": lista_archivos_paths,
        "transcripcion_resultado": transcripcion_resultado,
    }


def centrar_ventana(ventana):
    ventana.update_idletasks()
    ancho_ventana = ventana.winfo_width()
    alto_ventana = ventana.winfo_height()
    ancho_pantalla = ventana.winfo_screenwidth()
    alto_pantalla = ventana.winfo_screenheight()
    x = (ancho_pantalla // 2) - (ancho_ventana // 2)
    y = (alto_pantalla // 2) - (alto_ventana // 2)
    ventana.geometry(f"{ancho_ventana}x{alto_ventana}+{x}+{y}")
