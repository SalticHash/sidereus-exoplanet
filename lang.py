import sys
from pathlib import Path
from os import listdir

# Try tomllib (Py>=3.11) / Usa tomllib (Py>=3.11)
try:
    import tomllib  # stdlib
    _load_toml = lambda b: tomllib.loads(b)
except Exception:  # Py<3.11 fallback / Recurso para Py<3.11
    import tomli
    _load_toml = lambda b: tomli.loads(b)

class LanguageDict(dict):
    """
    Load TOML language files from folder
    Carga archivos de idioma TOML desde carpeta
    """

    def __init__(self, path=None, default_code: str = "en"):
        # Base directory / Directorio base
        base = Path(__file__).resolve().parent

        # Default path (relative to this file) / Ruta por defecto (relativa a este archivo)
        if path is None:
            self._lang_dir = base / "static" / "lang"
        else:
            p = Path(path)
            self._lang_dir = p if p.is_absolute() else (base / p)

        # Active language code / Código de idioma activo
        self.code = (default_code or "en").lower()

        data = {}
        if not self._lang_dir.exists():
            print(f"[WARN] Language folder not found / Carpeta no encontrada: {self._lang_dir}")
        else:
            for filename in listdir(self._lang_dir):
                file_path = self._lang_dir / filename
                ext = file_path.suffix.lower()
                if file_path.is_file() and ext in (".toml", ".tom"):
                    try:
                        raw = file_path.read_bytes()
                        doc = _load_toml(raw)  # dict
                        data[file_path.stem] = doc
                    except Exception as e:
                        print(f"[WARN] Cannot load / No se pudo cargar {file_path.name}: {e}")

        super().__init__(data)

        if self:
            print(f"[INFO] Loaded languages / Idiomas cargados: {', '.join(self.keys())}")
        else:
            print("[WARN] No languages loaded / No se cargaron idiomas")

    def as_dict(self) -> dict:
        """Return all languages dict / Devuelve todos los idiomas"""
        return dict(self)

    def set_code(self, lang_code: str):
        """Set active language code / Establece el idioma activo"""
        if not lang_code:
            return
        self.code = lang_code.split("-")[0].lower()

    def detect_from_request(self, request, fallback: str = "en"):
        """Detect from Accept-Language / Detecta desde Accept-Language"""
        header = request.headers.get("Accept-Language", "") or ""
        code = header.split(",")[0].split("-")[0].strip().lower() or fallback
        self.set_code(code)

    def get_text(self, key: str, default: str = "") -> str:
        """
        Return translated text for active code
        Devuelve texto traducido para el idioma activo
        """
        cur = self.get(self.code, {})
        for part in key.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                return default
        return cur if isinstance(cur, str) else default

    def available_languages(self):
        """List available languages / Lista idiomas disponibles"""
        return list(self.keys())

LANG = LanguageDict(path="static/lang", default_code="en")
