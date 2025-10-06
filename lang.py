import sys
import json
from pathlib import Path
from os import listdir

# Try tomllib (Py>=3.11) / Usa tomllib (Py>=3.11)
try:
    import tomllib  # stdlib
    _load_toml = lambda b: tomllib.loads(b)
except Exception:
    # Fallback to tomli / Recurso a tomli
    import tomli
    _load_toml = lambda b: tomli.loads(b)

class LanguageDict(dict):
    """
    Load all TOML language files from a folder
    Carga todos los archivos TOML de idioma desde una carpeta
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

        # Ensure folder exists / Verifica existencia de carpeta
        if not lang_dir.exists():
            print(f"[WARN] Language folder not found / Carpeta no encontrada: {lang_dir}")
            super().__init__({})
            return

        data = {}
        # Load each TOML file / Carga cada archivo TOML
        for filename in listdir(lang_dir):
            file_path = lang_dir / filename
            ext = file_path.suffix.lower()
            if ext in (".toml", ".tom") and file_path.is_file():
                try:
                    raw = file_path.read_bytes()
                    doc = _load_toml(raw)
                    # Flatten 1-level tables if you store nested / Aplana un nivel si usas tablas
                    # Aquí asumimos claves simples k=v / We assume simple k=v keys
                    data[file_path.stem] = doc
                except Exception as e:
                    print(f"[WARN] Cannot load / No se pudo cargar {file_path.name}: {e}")

        super().__init__(data)

    def get_text(self, lang_code: str, key: str, default: str = "") -> str:
        """
        Return translated text / Devuelve el texto traducido
        """
        node = self.get(lang_code, {})
        # Support nested keys "a.b.c" / Soporta claves anidadas "a.b.c"
        cur = node
        for part in key.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                return default
        return cur if isinstance(cur, str) else default

    def available_languages(self):
        """
        List available languages / Lista los idiomas disponibles
        """
        return list(self.keys())

def detect_browser_language(request) -> str:
    """
    Detect browser language / Detecta idioma del navegador
    Example / Ejemplo: 'es-ES,es;q=0.9,en;q=0.8' → 'es'
    """
    header = request.headers.get("Accept-Language", "")
    if not header:
        return "en"
    lang = header.split(",")[0].split("-")[0].strip().lower()
    return lang or "en"

LANG = LanguageDict(path="static/lang")

# Info print / Mensaje informativo
if LANG:
    print(f"[INFO] Loaded languages / Idiomas cargados: {', '.join(LANG.available_languages())}")
else:
    print("[WARN] No languages loaded / No se cargaron idiomas")
