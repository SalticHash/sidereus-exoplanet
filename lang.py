import json
from pathlib import Path
from os import listdir

class LanguageDict(dict):
    """
    Load all JSON language files from a folder
    Carga todos los archivos JSON de idioma desde una carpeta
    """

    def __init__(self, path=None):
        # Base directory / Directorio base
        base = Path(__file__).resolve().parent

        # Default path / Ruta por defecto
        if path is None:
            lang_dir = base / "static" / "lang"
        else:
            p = Path(path)
            lang_dir = p if p.is_absolute() else (base / p)

        # Check if folder exists / Verifica si existe la carpeta
        if not lang_dir.exists():
            print(f"[WARN] Language folder not found / Carpeta de idioma no encontrada: {lang_dir}")
            super().__init__({})
            return

        data = {}
        # Load each JSON file / Carga cada archivo JSON
        for filename in listdir(lang_dir):
            file_path = lang_dir / filename
            if file_path.suffix.lower() == ".json" and file_path.is_file():
                try:
                    with file_path.open("r", encoding="utf-8") as f:
                        data[file_path.stem] = json.load(f)
                except Exception as e:
                    print(f"[WARN] Cannot load / No se pudo cargar {file_path.name}: {e}")

        super().__init__(data)

    def get_text(self, lang_code: str, key: str, default: str = "") -> str:
        """
        Return translated text / Devuelve el texto traducido
        """
        return self.get(lang_code, {}).get(key, default)

    def available_languages(self):
        """
        List available languages / Lista los idiomas disponibles
        """
        return list(self.keys())

def detect_browser_language(request) -> str:
    """
    Detect browser language / Detecta el idioma del navegador
    Example / Ejemplo: 'es-ES,es;q=0.9,en;q=0.8' → 'es'
    """
    header = request.headers.get("Accept-Language", "")
    if not header:
        return "en"

    lang = header.split(",")[0].split("-")[0].strip().lower()
    return lang if lang else "en"

LANG = LanguageDict(path="static/lang")

# Print info / Imprime información
if LANG:
    print(f"[INFO] Loaded languages / Idiomas cargados: {', '.join(LANG.available_languages())}")
else:
    print("[WARN] No languages loaded / No se cargaron idiomas")
