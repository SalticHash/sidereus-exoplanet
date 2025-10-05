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
    """Recursively merge override into base; prefer override when not None."""
    # Performs a recursive merge between dictionaries, keeping override values
    # Realiza una fusión recursiva entre diccionarios, conservando los valores de override
    if isinstance(override, dict) and isinstance(base, dict):
        merged: Dict[str, Any] = dict(base)
        for k, v in override.items():
            merged[k] = _deep_merge(v, base.get(k))
        return merged
    return override if override is not None else base


class LanguageDict:
    """Language access with fallback and HTTP Accept-Language negotiation."""

    def __init__(self, path: str = "./static/lang/"):
        # Loads all language files and ensures English as fallback
        # Carga todos los archivos de idioma y asegura el inglés como respaldo
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
        try:
            langs = request.accept_languages
            best = langs.best_match(self.langs) or "en"
        except Exception:
            best = "en"

        base = best.split("-")[0]
        user = self._data.get(best) or self._data.get(base) or self._data.get("en") or {}
        en = self._data.get("en") or {}
        return best, user, en

    def _resolve(self, key: str) -> Any:
        """Resolve a key for current language with fallback."""
        code, user, en = self._select_language()

        if key == "user":
            return code

        u_val = user.get(key) if isinstance(user, dict) else None
        e_val = en.get(key) if isinstance(en, dict) else None

        if isinstance(u_val, dict) or isinstance(e_val, dict):
            u_dict = u_val if isinstance(u_val, dict) else {}
            e_dict = e_val if isinstance(e_val, dict) else {}
            return _deep_merge(u_dict, e_dict)

        return u_val if u_val is not None else e_val

    def as_dict(self) -> Dict[str, Any]:
        # Returns a combined snapshot of the current language and English
        # Devuelve una combinación de las traducciones actuales e inglés
        _, user, en = self._select_language()
        return _deep_merge(user, en)

    def __repr__(self) -> str:
        # Prints useful debug info about loaded languages
        # Muestra información útil de depuración sobre los idiomas cargados
        return f"<LanguageDict langs={self.langs!r} base_path={self._path!r}>"


# Global instance used by the app
# Instancia global utilizada por la aplicación
LANG = LanguageDict()
