from pathlib import Path
from os import listdir

try:
    import tomllib  # Py>=3.11
    _use_tomllib = True
except Exception:
    import tomli     # Py<3.11
    _use_tomllib = False


class LanguageDict(dict):
    def __init__(self, path=None, default_code: str = "en"):
        base = Path(__file__).resolve().parent
        p = Path(path) if path else (base / "static" / "lang")
        self._lang_dir = p if p.is_absolute() else (base / p)
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
                        txt = file_path.read_text(encoding="utf-8")  # str
                        if _use_tomllib:
                            doc = tomllib.loads(txt)                 # str -> dict
                        else:
                            doc = tomli.loads(txt)                   # str -> dict
                        data[file_path.stem] = doc
                    except Exception as e:
                        print(f"[WARN] Cannot load / No se pudo cargar {file_path.name}: {e}")

        super().__init__(data)

    def as_dict(self) -> dict:
        return dict(self)

    def set_code(self, lang_code: str):
        if lang_code:
            self.code = lang_code.split("-")[0].lower()

    def detect_from_request(self, request, fallback: str = "en"):
        header = request.headers.get("Accept-Language", "") or ""
        code = header.split(",")[0].split("-")[0].strip().lower() or fallback
        self.set_code(code)

    def get_text(self, key: str, default: str = "") -> str:
        cur = self.get(self.code, {})
        for part in key.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                return default
        return cur if isinstance(cur, str) else default

    def available_languages(self):
        return list(self.keys())


LANG = LanguageDict(path="static/lang", default_code="en")
