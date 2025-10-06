from __future__ import annotations
import json
import logging
from pathlib import Path
from os import getenv as get_env
from dotenv import load_dotenv

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    url_for,
)

from lang import LANG
from API.entry import ExoplanetEntry
from API.analyse import calculateDisposition as model_calculateDisposition

load_dotenv()
ROOT_DIR = Path(__file__).resolve().parent
MODEL_DIR = ROOT_DIR / "model"

app = Flask(
    __name__,
    static_folder="static",
    template_folder="templates",
)
# Sets up base logging for easier debugging in dev and prod
# Configura el logging base para facilitar la depuración en dev y prod

# Logging básico
logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.INFO)

# i18n disponible en plantillas
# Opción 1: objeto global (por compatibilidad)
app.jinja_env.globals.update(lang=LANG)
# Exposes the dynamic language helper directly to templates
# Expone el asistente de idioma dinámico directamente a las plantillas

# Opción 2: snapshot por request (recomendado: usar {{ t.* }} )
@app.context_processor
def inject_lang():
    # Provides a per-request snapshot so templates can dereference strings quickly
    # Proporciona un snapshot por solicitud para que las plantillas resuelvan cadenas rápido
    return {"t": LANG.as_dict(), "lang_code": LANG.code}

class NumLike:
    """
    Acepta int/float/str (con coma o punto) o dict {"value": ...}
    y devuelve float estandarizado.
    """
    __slots__ = ("value",)

    def __init__(self, value):
        if value is None:
            raise ValueError("None no es numérico")
        if isinstance(value, (int, float)):
            self.value = float(value)
        elif isinstance(value, str):
            self.value = float(value.replace(",", "."))
        elif isinstance(value, dict) and "value" in value:
            v = value["value"]
            if isinstance(v, str):
                v = v.replace(",", ".")
            self.value = float(v)
        else:
            raise ValueError(f"Valor numérico inválido: {value!r}")

    def __repr__(self):
        return f"NumLike({self.value})"


def _to_float_or_none(x):
    if x is None:
        return None
    try:
        return NumLike(x).value
    except Exception:
        return None


def _canonicalize_keys(d: dict) -> dict:
    """
    Normaliza nombres del frontend a los usados por el modelo:
      - insolation_flux → insolation
      - star_* → stellar_*
    """
    if not isinstance(d, dict):
        return {}
    out = {}
    for k, v in d.items():
        nk = k
        if k == "insolation_flux":
            nk = "insolation"
        elif k.startswith("star_"):
            nk = "stellar_" + k[len("star_"):]
        out[nk] = v
    return out


def normalize_payload_dual_numeric(payload: dict) -> dict:
    """
    Convierte campos numéricos (10.5, "10,5" o {"value":10.5}) a float.
    Ignora 'disposition' si viene del cliente.
    """
    # Ensures numeric fields are floats regardless of input representation
    # Garantiza que los campos numéricos sean float sin importar su representación
    numeric_fields = {
        # Órbita / tránsito
        "orbital_period",
        "transit_epoch",
        "transit_duration",
        "transit_depth",
        "transit_snr",
        "impact_param",
        "eccentricity",
        "semi_major_axis",
        # Planeta
        "planet_radius",
        "equilibrium_temp",
        "insolation",  # (mapeado desde insolation_flux)
        # Estrella
        "stellar_radius",
        "stellar_mass",
        "stellar_temp",
        "stellar_logg",
        "stellar_metallicity",
        "stellar_density",
    }

    clean = {}
    for k, v in (payload or {}).items():
        if k == "disposition":
            continue
        if k in numeric_fields:
            clean[k] = _to_float_or_none(v)
        else:
            clean[k] = v
    return clean


def read_json_from_model(filename: str, default=None):
    """Lee JSON desde /model/<filename>. Si falla, retorna default o error."""
    try:
        with open(MODEL_DIR / filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return default if default is not None else {"__error__": str(e), "__file__": filename}


def _make_entry_or_dict(payload: dict):
    """
    Intenta construir ExoplanetEntry; si no, devuelve dict para que el
    modelo acepte dicts directamente.
    """
    # Tries common constructors to maximize compatibility with the model
    # Prueba constructores comunes para maximizar compatibilidad con el modelo
    # Caso 1: .from_dict
    try:
        from_dict = getattr(ExoplanetEntry, "from_dict", None)
        if callable(from_dict):
            return ExoplanetEntry.from_dict(payload)
    except Exception:
        pass

    # Caso 2: constructor con kwargs
    try:
        return ExoplanetEntry(**payload)  # type: ignore[arg-type]
    except Exception:
        pass

    # Caso 3: constructor con un solo dict
    try:
        return ExoplanetEntry(payload)  # type: ignore[call-arg]
    except Exception:
        pass

    # Último recurso
    return payload


def _coerce_model_output(out):
    """
    Convierte lo que devuelva el modelo a:
      {"disposition": <str>, "confidence": <float opcional>}
    Soporta str, dict, (label, prob), objetos con attrs, numpy types.
    """
    # Normalizes heterogeneous outputs into one JSON shape for the frontend
    # Normaliza salidas heterogéneas en una estructura JSON única para el frontend
    try:
        import numpy as np
        np_types = (np.generic,)
    except Exception:
        np_types = tuple()

    if isinstance(out, str):
        return {"disposition": out}

    if isinstance(out, dict):
        if "disposition" in out:
            res = {"disposition": str(out["disposition"])}
            if "confidence" in out:
                try:
                    res["confidence"] = float(out["confidence"])
                except Exception:
                    pass
            return res
        for k in ("label", "class", "pred", "prediction"):
            if k in out:
                disp = out[k]
                conf = out.get("prob") or out.get("probability") or out.get("score")
                res = {"disposition": str(disp)}
                if isinstance(conf, (int, float, *np_types)):
                    res["confidence"] = float(conf)
                return res

    if isinstance(out, (tuple, list)) and len(out) >= 1:
        disp = out[0]
        conf = out[1] if len(out) > 1 else None
        res = {"disposition": str(disp)}
        if isinstance(conf, (int, float, *np_types)):
            res["confidence"] = float(conf)
        return res

    for attr in ("disposition", "label", "prediction", "pred"):
        if hasattr(out, attr):
            disp = getattr(out, attr)
            conf = None
            for cattr in ("confidence", "prob", "probability", "score"):
                if hasattr(out, cattr):
                    conf = getattr(out, cattr)
                    break
            res = {"disposition": str(disp)}
            if isinstance(conf, (int, float, *np_types)):
                res["confidence"] = float(conf)
            return res

    if isinstance(out, np_types):
        return {"disposition": str(out)}

    return {"disposition": str(out)}


@app.route("/")
def indexPage():
    return render_template("index.html")


@app.route("/data")
def dataPage():
    # Loads model metadata so the page can display columns and thresholds
    # Carga metadatos del modelo para que la página muestre columnas y umbrales
    columns_used = read_json_from_model("columns_used.json", default=[])
    thresholds = read_json_from_model("thresholds.json", default={})
    return render_template("data.html", columns_used=columns_used, thresholds=thresholds)


@app.route("/precision")
def precisionPage():
    metrics = read_json_from_model("metrics.json", default={})
    return render_template("precision.html", metrics=metrics)


@app.route("/thresholds")
def thresholdsPage():
    thresholds = read_json_from_model("thresholds.json", default={})
    return render_template("thresholds.html", thresholds=thresholds)


@app.route("/endpoints")
def endpoints():
    ep = {
        "indexPage": url_for("indexPage"),
        # Se oculta calculateDisposition a petición: solo páginas navegables
        "precisionPage": url_for("precisionPage"),
        "dataPage": url_for("dataPage"),
        "thresholdsPage": url_for("thresholdsPage"),
    }
    return render_template("endpoints.html", endpoints_map=ep)

REQUIRED_MIN_KEYS = {"orbital_period", "transit_duration", "transit_depth"}

@app.route("/api/health")
def health():
    # Reports presence of model artifacts and current language for diagnostics
    # Reporta presencia de artefactos del modelo e idioma actual para diagnóstico
    meta = {
        "has_model_pkl": (MODEL_DIR / "model_lgb.pkl").exists(),
        "has_columns": (MODEL_DIR / "columns_used.json").exists(),
        "has_thresholds": (MODEL_DIR / "thresholds.json").exists(),
        "has_metrics": (MODEL_DIR / "metrics.json").exists(),
        "lang_loaded": getattr(LANG, "langs", []),
        "lang_code": LANG.code,
    }
    return jsonify(meta), 200


@app.route("/api/calculateDisposition", methods=["POST"])
def calculateDisposition():
    """
    Recibe JSON con parámetros y devuelve:
      {"disposition": "...", "confidence": opcional, "__received_keys__": [...]}
    """
    # Validates, normalizes, calls the model, and coerces output for the UI
    # Valida, normaliza, llama al modelo y adapta la salida para la interfaz
    try:
        if not request.is_json:
            return jsonify(error="Content-Type must be application/json"), 400

        raw = request.get_json(silent=True)
        if not isinstance(raw, dict):
            return jsonify(error="Payload must be a JSON object"), 400

        # 1) Normaliza números
        payload = normalize_payload_dual_numeric(raw)

        # 2) Normaliza nombres
        payload = _canonicalize_keys(payload)

        # 3) Validación mínima para evitar “predicción por defecto”
        present = {k for k in REQUIRED_MIN_KEYS if payload.get(k) is not None}
        if len(present) < 2:
            msg = "Insuficientes parámetros: envía al menos dos de orbital_period, transit_duration, transit_depth"
            return jsonify(error=msg), 400

        app.logger.info(f"[calc] payload_in={payload}")

        # 4) Construye entrada o usa dict
        entry_or_dict = _make_entry_or_dict(payload)

        # 5) Llama al modelo
        out = None
        try:
            out = model_calculateDisposition(entry_or_dict)  # objeto
        except TypeError:
            out = model_calculateDisposition(payload)        # dict

        app.logger.info(f"[calc] model_raw={type(out).__name__} -> {out}")

        # 6) Normaliza salida
        result = _coerce_model_output(out)
        result["__received_keys__"] = sorted([k for k in payload.keys() if payload[k] is not None])

        app.logger.info(f"[calc] result={result}")

        if "disposition" in result:
            return jsonify(result), 200

        return jsonify(error="Model returned unexpected result (after coercion)"), 500

    except Exception as e:
        app.logger.exception("calc error")
        return jsonify(error=str(e)), 500


if __name__ == "__main__":
    # Reads runtime config from environment and starts the Flask server
    # Lee configuración de ejecución del entorno e inicia el servidor Flask
    port = int(get_env("PORT", "2727"))
    debug = get_env("FLASK_DEBUG", "1") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
