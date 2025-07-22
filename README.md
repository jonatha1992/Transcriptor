# AudioText - Transcriptor y Traductor de Audio

**AudioText** es una aplicación de escritorio desarrollada en Python que permite transcribir y traducir archivos de audio de manera eficiente y precisa. El sistema utiliza reconocimiento de voz avanzado y tecnologías de procesamiento de audio para convertir contenido hablado en texto.

## 🚀 Características Principales

- **Transcripción de Audio**: Convierte archivos de audio a texto usando Google Speech Recognition
- **Traducción Automática**: Traduce las transcripciones entre múltiples idiomas
- **Procesamiento Paralelo**: Utiliza múltiples hilos para procesar archivos grandes de manera eficiente
- **Mejoramiento de Audio**: Aplica filtros de audio para mejorar la calidad de la transcripción
- **Detección de Actividad de Voz (VAD)**: Segmenta automáticamente el audio basándose en silencios
- **Interfaz Gráfica Intuitiva**: GUI desarrollada con Tkinter para facilidad de uso
- **Exportación de Resultados**: Guarda las transcripciones en archivos de texto
- **Reproductor Integrado**: Reproduce archivos de audio directamente en la aplicación

## 📋 Idiomas Soportados

- Español (es-ES)
- Inglés (en-US)
- Francés (fr-FR)
- Alemán (de-DE)
- Italiano (it-IT)

## 🔧 Requisitos del Sistema

### Dependencias de Python
```
speech-recognition
pydub
googletrans
mutagen
numpy
scipy
tkinter
```

### Software Externo
- **FFmpeg**: Requerido para el procesamiento de audio
- **FFprobe**: Para análisis de archivos multimedia

## 📦 Instalación

1. Clona este repositorio:
```bash
git clone https://github.com/jonatha1992/Transcriptor.git
cd Transcriptor
```

2. Instala las dependencias:
```bash
pip install -r requirements.txt
```

3. Asegúrate de tener FFmpeg instalado en tu sistema:
   - **Windows**: Descarga desde [ffmpeg.org](https://ffmpeg.org/download.html)
   - **macOS**: `brew install ffmpeg`
   - **Linux**: `sudo apt-get install ffmpeg`

## 🎯 Uso

### Interfaz Gráfica

1. Ejecuta la aplicación:
```bash
python main.py
```

2. **Cargar Archivos**: Selecciona los archivos de audio que deseas transcribir
3. **Configurar Idiomas**: 
   - Selecciona el idioma de entrada del audio
   - Selecciona el idioma de salida para la traducción (opcional)
4. **Iniciar Transcripción**: Haz clic en "Transcribir" para comenzar el proceso
5. **Exportar Resultados**: Guarda la transcripción en un archivo de texto

### Características Avanzadas

- **Procesamiento por Lotes**: Selecciona múltiples archivos para transcribir en secuencia
- **Control de Progreso**: Barra de progreso visual durante el procesamiento
- **Detención de Proceso**: Posibilidad de detener la transcripción en cualquier momento
- **Conteo de Palabras**: Estadísticas automáticas de palabras reconocidas e inaudibles

## 🛠️ Arquitectura del Sistema

### Componentes Principales

- **`Funcionalidad.py`**: Motor principal de transcripción y procesamiento de audio
- **`Config.py`**: Configuraciones globales y parámetros del sistema
- **`Reproductor.py`**: Módulo de reproducción de archivos de audio
- **`procces_audio.py`**: Funciones específicas de procesamiento de audio

### Tecnologías Utilizadas

- **Reconocimiento de Voz**: Google Speech Recognition API
- **Procesamiento de Audio**: PyDub con FFmpeg
- **Filtrado Digital**: SciPy para mejoramiento de calidad
- **Traducción**: Google Translate API
- **Interfaz Gráfica**: Tkinter
- **Concurrencia**: ThreadPoolExecutor para procesamiento paralelo

## ⚙️ Configuración Avanzada

### Parámetros de Audio
- **Umbral de Energía**: Configurable para diferentes calidades de audio
- **Detección de Silencio**: Ajustable según las características del audio
- **Filtros de Frecuencia**: Optimizados para voz humana (300-3000 Hz)

### Optimización de Rendimiento
- **Procesamiento Multi-hilo**: Hasta 5 hilos simultáneos
- **Segmentación Inteligente**: División automática basada en VAD
- **Gestión de Memoria**: Procesamiento eficiente de archivos grandes

## 📊 Funcionalidades del Sistema

### Procesamiento de Audio
- Segmentación automática basada en detección de silencios
- Mejoramiento de calidad mediante filtros passa-banda
- Soporte para múltiples formatos de audio
- Procesamiento eficiente de archivos grandes

### Transcripción
- Reconocimiento de voz en tiempo real
- Manejo de errores y contenido inaudible
- Capitalización automática del texto
- Estadísticas de palabras reconocidas

### Traducción
- Traducción automática entre idiomas soportados
- Preservación del formato del texto
- Integración transparente con el flujo de transcripción

## 📈 Estado del Proyecto

- **Versión**: 1.0.0
- **Estado**: Estable
- **Último Update**: Octubre 2024
- **Desarrollador**: Correa Jonathan

## 🤝 Contribuir

Las contribuciones son bienvenidas. Para contribuir:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto está desarrollado por **Correa Jonathan** © 2024. 

## 🆘 Soporte

Si encuentras algún problema o necesitas ayuda:
- Abre un [issue](https://github.com/jonatha1992/Transcriptor/issues) en GitHub
- Revisa la documentación del código para detalles técnicos

---

**AudioText** - Transformando audio en texto de manera inteligente y eficiente.
