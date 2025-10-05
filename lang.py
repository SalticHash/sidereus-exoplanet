# lang.py
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
    if isinstance(override, dict) and isinstance(base, dict):
        merged: Dict[str, Any] = dict(base)
        for k, v in override.items():
            merged[k] = _deep_merge(v, base.get(k))
        return merged
    return override if override is not None else base


class LanguageDict:
    """Language access for templates with Accept-Language negotiation and per-key fallback to 'en'."""

    def __init__(self, path: str = "./static/lang/"):
        self._path = path
        self._data: Dict[str, Dict[str, Any]] = {}
        self.langs: list[str] = []

        # Load all .toml files in the directory
        for filename in listdir(path):
            root, ext = splitext(filename)
            if ext != ".toml":
                continue
            with open(join(path, filename), "rb") as f:
                self._data[root] = toml_loader.load(f)
            self.langs.append(root)

        # Ensure global fallback exists
        self._data.setdefault("en", {})

    def _select_language(self) -> tuple[str, Dict[str, Any], Dict[str, Any]]:
        """Return (code, user_lang_dict, en_dict). Fallback to 'en' without request."""
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
        """Resolve a top-level key for current language with per-key fallback."""
        code, user, en = self._select_language()

        if key == "user":
            return code  # expose negotiated language code

        u_val = user.get(key) if isinstance(user, dict) else None
        e_val = en.get(key) if isinstance(en, dict) else None

        # Deep-merge dicts to allow key-level fallback
        if isinstance(u_val, dict) or isinstance(e_val, dict):
            u_dict = u_val if isinstance(u_val, dict) else {}
            e_dict = e_val if isinstance(e_val, dict) else {}
            return _deep_merge(u_dict, e_dict)

        return u_val if u_val is not None else e_val

    def __getattr__(self, key: str) -> Any:
        """Attribute-style access in templates."""
        value = self._resolve(key)
        return {} if value is None else value

    def __getitem__(self, key: str) -> Any:
        """Item-style access in templates."""
        value = self._resolve(key)
        return {} if value is None else value

    def as_dict(self) -> Dict[str, Any]:
        """Return merged user/en dictionary snapshot."""
        _, user, en = self._select_language()
        return _deep_merge(user, en)

    def __repr__(self) -> str:
        return f"<LanguageDict langs={self.langs!r} base_path={self._path!r}>"


# Global instance exposed to the app
LANG = LanguageDict()
