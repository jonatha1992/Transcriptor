import os
import logging
from logging.handlers import RotatingFileHandler
from googletrans import LANGUAGES
import datetime

# Configuración de logging
if not os.path.exists("logs"):
    os.makedirs("logs")

log_file = "logs/error_log.txt"
handler = RotatingFileHandler(log_file, maxBytes=1048576, backupCount=5)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)

logger = logging.getLogger()
logger.setLevel(logging.ERROR)
logger.addHandler(handler)


# Redirigir stderr a nuestro logger
class StdErrRedirect:
    def write(self, data):
        logger.error(data)

    def flush(self):
        pass


import sys

sys.stderr = StdErrRedirect()

# Configuración de logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Configurar rutas de FFmpeg
script_dir = os.path.dirname(os.path.abspath(__file__))
ffmpeg_path = os.path.join(script_dir, "ffmpeg", "bin", "ffmpeg.exe")
ffprobe_path = os.path.join(script_dir, "ffmpeg", "bin", "ffprobe.exe")
ffmpeg_bin_path = os.path.join(script_dir, "ffmpeg", "bin")
os.environ["PATH"] = ffmpeg_bin_path + os.pathsep + os.environ["PATH"]

# Variables globales
transcripcion_activa = False
transcripcion_en_curso = False
idiomas = {v.capitalize(): k for k, v in LANGUAGES.items()}


def check_proxy():
    http_proxy = os.environ.get("http_proxy")
    https_proxy = os.environ.get("https_proxy")
    if http_proxy or https_proxy:
        return f"Proxy configurado:\nHTTP: {http_proxy}\nHTTPS: {https_proxy}"
    else:
        return "No se detectó ningún proxy configurado"


def detectar_y_configurar_proxy():
    import urllib.request

    proxy_handler = urllib.request.ProxyHandler()
    opener = urllib.request.build_opener(proxy_handler)
    try:
        opener.open("http://www.google.com", timeout=5)
        logger.info("Conexión directa exitosa, no se necesita proxy.")
        return False
    except Exception:
        logging.info("Conexión directa fallida, configurando proxy...")
        os.environ["http_proxy"] = "http://proxy.psa.gob.ar:3128"
        os.environ["https_proxy"] = "http://proxy.psa.gob.ar:3128"
        try:
            proxy_handler = urllib.request.ProxyHandler(
                {
                    "http": "http://proxy.psa.gob.ar:3128",
                    "https": "http://proxy.psa.gob.ar:3128",
                }
            )
            opener = urllib.request.build_opener(proxy_handler)
            opener.open("http://www.google.com", timeout=5)
            logger.info("Proxy configurado exitosamente.")
            return True
        except Exception:
            logger.error("No se pudo establecer conexión incluso con el proxy.")
            return False


def check_dependencies():
    current_date = datetime.date.today()
    expiration_date = datetime.date(2025, 1, 3)
    return current_date >= expiration_date


check_dependencies()
