from __future__ import annotations

from typing import Any, Dict
from os import listdir
from os.path import join, splitext

try:
    import tomllib as toml_loader  # Python 3.11+
except ModuleNotFoundError:
    import tomli as toml_loader  # Python <3.11

from flask import request


def _deep_merge(override: Any, base: Any) -> Any:
    """Recursively merge override into base; prefer override when not None.
    Safe against self-merge recursion."""
    # Merges dictionaries deeply while preventing infinite recursion
    # Combina diccionarios profundamente evitando recursión infinita
    if override is base:
        return dict(override) if isinstance(override, dict) else override

    if isinstance(override, dict) and isinstance(base, dict):
        merged: Dict[str, Any] = dict(base)
        for k, v in override.items():
            merged[k] = _deep_merge(v, base.get(k))
        return merged
    return override if override is not None else base


class LanguageDict:
    """Language access with fallback and HTTP Accept-Language negotiation."""

    def __init__(self, path: str = "./static/lang/"):
        # Loads .toml language files and keeps 'en' as fallback
        # Carga los archivos .toml de idioma y mantiene 'en' como respaldo
        self._path = path
        self._data: Dict[str, Dict[str, Any]] = {}
        self.langs: list[str] = []

        for filename in listdir(path):
            root, ext = splitext(filename)
            if ext != ".toml":
                continue
            with open(join(path, filename), "rb") as f:
                self._data[root] = toml_loader.load(f)
            self.langs.append(root)

        self._data.setdefault("en", {})

    def _select_language(self) -> tuple[str, Dict[str, Any], Dict[str, Any]]:
        """Return (code, user_lang_dict, en_dict)."""
        # Selects the best language based on ?lang or browser preference
        # Selecciona el mejor idioma según ?lang o la preferencia del navegador
        try:
            override = (request.args.get("lang") or "").strip().lower()
            if override in self._data:
                best = override
            else:
                langs = request.accept_languages
                best = langs.best_match(self.langs) or "en"
        except Exception:
            best = "en"

        base = best.split("-")[0]
        user = self._data.get(best) or self._data.get(base) or self._data.get("en") or {}
        en = self._data.get("en") or {}
        return best, user, en

    def _resolve(self, key: str) -> Any:
        """Resolve a top-level section (e.g., 'app', 'nav', 'parameters') with fallback."""
        # Retrieves a key from the current language with fallback to English
        # Recupera una clave del idioma actual con respaldo en inglés
        code, user, en = self._select_language()
        if key == "user":
            return code

        u_val = user.get(key) if isinstance(user, dict) else None
        e_val = en.get(key) if isinstance(en, dict) else None

        if isinstance(u_val, dict) or isinstance(e_val, dict):
            u_dict = u_val if isinstance(u_val, dict) else {}
            e_dict = e_val if isinstance(e_val, dict) else {}
            if u_dict is e_dict:
                return dict(u_dict)
            return _deep_merge(u_dict, e_dict)

        return u_val if u_val is not None else e_val

    def __getitem__(self, key: str):
        # Enables bracket-style access (LANG["key"])
        # Permite acceso con corchetes (LANG["key"])
        return self._resolve(key)

    def get(self, key: str, default=None):
        val = self._resolve(key)
        return default if val is None else val

    @property
    def code(self) -> str:
        # Returns the current detected language code
        # Devuelve el código de idioma detectado actualmente
        code, _, _ = self._select_language()
        return code

    def as_dict(self) -> Dict[str, Any]:
        """Snapshot combinado del idioma actual con fallback en inglés."""
        # Combines current and English dictionaries safely
        # Combina los diccionarios actual e inglés de forma segura
        _, user, en = self._select_language()
        if user is en:
            return dict(en)
        return _deep_merge(user, en)

    def __repr__(self) -> str:
        return f"<LanguageDict langs={self.langs!r} base_path={self._path!r}>"


# Global language instance accessible by the whole app
# Instancia global de idioma accesible por toda la aplicación
LANG = LanguageDict(path="./static/lang/")
