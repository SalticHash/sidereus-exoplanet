from __future__ import annotations
import json
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

# Detecta el idioma del navegador / Detect browser language
@app.before_request
def _set_lang():
    LANG.detect_from_request(request, fallback="en")

# Mezcla profunda / Deep merge
def _deep_merge(base: dict, override: dict) -> dict:
    out = dict(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out

# Inyecta idioma actual con defaults seguros / Inject current language with safe defaults
@app.context_processor
def inject_lang():
    all_langs = LANG.as_dict()
    cur = all_langs.get(LANG.code) or next(iter(all_langs.values()), {}) or {}
    defaults = {
        "app": {"title": "Sidereus Exoplanet"},
        "nav": {
            "home": "Home", "data": "Data", "precision": "Precision",
            "thresholds": "Thresholds", "about": "About",
        },
        "sections": {
            "prediction_title": "Prediction",
            "input_title": "Input",
            "results_title": "Results",
        },
    }
    t = _deep_merge(defaults, cur)
    return {"t": t, "T": all_langs, "lang_code": LANG.code}


class NumLike:
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
    numeric_fields = {
        "orbital_period", "transit_epoch", "transit_duration", "transit_depth",
        "transit_snr", "impact_param", "eccentricity", "semi_major_axis",
        "planet_radius", "equilibrium_temp", "insolation",
        "stellar_radius", "stellar_mass", "stellar_temp",
        "stellar_logg", "stellar_metallicity", "stellar_density",
    }
    clean = {}
    for k, v in (payload or {}).items():
        if k == "disposition":
            continue
        clean[k] = _to_float_or_none(v) if k in numeric_fields else v
    return clean


def read_json_from_model(filename: str, default=None):
    try:
        with open(MODEL_DIR / filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return default if default is not None else {"__error__": str(e), "__file__": filename}


def _make_entry_or_dict(payload: dict):
    try:
        from_dict = getattr(ExoplanetEntry, "from_dict", None)
        if callable(from_dict):
            return ExoplanetEntry.from_dict(payload)
    except Exception:
        pass
    try:
        return ExoplanetEntry(**payload)
    except Exception:
        pass
    try:
        return ExoplanetEntry(payload)
    except Exception:
        pass
    return payload


def _coerce_model_output(out):
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
        "precisionPage": url_for("precisionPage"),
        "dataPage": url_for("dataPage"),
        "thresholdsPage": url_for("thresholdsPage"),
    }
    return render_template("endpoints.html", endpoints_map=ep)


REQUIRED_MIN_KEYS = {"orbital_period", "transit_duration", "transit_depth"}


@app.route("/api/health")
def health():
    meta = {
        "has_model_pkl": (MODEL_DIR / "model_lgb.pkl").exists(),
        "has_columns": (MODEL_DIR / "columns_used.json").exists(),
        "has_thresholds": (MODEL_DIR / "thresholds.json").exists(),
        "has_metrics": (MODEL_DIR / "metrics.json").exists(),
        "lang_loaded": LANG.available_languages(),
        "lang_code": LANG.code,
    }
    return jsonify(meta), 200


@app.route("/api/calculateDisposition", methods=["POST"])
def calculateDisposition():
    try:
        if not request.is_json:
            return jsonify(error="Content-Type must be application/json"), 400

        raw = request.get_json(silent=True)
        if not isinstance(raw, dict):
            return jsonify(error="Payload must be a JSON object"), 400

        payload = normalize_payload_dual_numeric(raw)
        payload = _canonicalize_keys(payload)

        present = {k for k in REQUIRED_MIN_KEYS if payload.get(k) is not None}
        if len(present) < 2:
            msg = "Insuficientes parámetros: envía al menos dos de orbital_period, transit_duration, transit_depth"
            return jsonify(error=msg), 400

        entry_or_dict = _make_entry_or_dict(payload)
        out = None
        try:
            out = model_calculateDisposition(entry_or_dict)
        except TypeError:
            out = model_calculateDisposition(payload)

        result = _coerce_model_output(out)
        result["__received_keys__"] = sorted([k for k in payload.keys() if payload[k] is not None])

        if "disposition" in result:
            return jsonify(result), 200

        return jsonify(error="Model returned unexpected result"), 500

    except Exception as e:
        return jsonify(error=str(e)), 500


if __name__ == "__main__":
    port = int(get_env("PORT", "2727"))
    debug = get_env("FLASK_DEBUG", "1") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
