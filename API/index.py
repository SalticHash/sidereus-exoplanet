# app.py — Backend API + SPA (sin Jinja), con uploads CSV e i18n snapshot
from __future__ import annotations

import os
import traceback
from os import listdir as list_files
from os.path import join as join_path

from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

from lang import LANG
from API.data import getJsonFile, loadDataCSV
from API.entry import ExoplanetEntry
from API.analyse import calculateDisposition

# ------------------------------------------------------------------------------
# Config
# ------------------------------------------------------------------------------
load_dotenv()

# Flask app
# Nota: no usamos plantillas; React/Vite se sirve como SPA en producción.
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}, r"/data/*": {"origins": "*"}})

# Directorio del build de React
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend", "dist")

# --- Dual numeric adapter (scalar with dict-like .get('value')) ---
class NumLike:
    __slots__ = ("value",)

    def __init__(self, value):
        if isinstance(value, (int, float)):
            self.value = float(value)
        elif isinstance(value, str):
            self.value = float(value.replace(",", "."))
        else:
            raise TypeError(f"NumLike requires int/float/str numeric, got {type(value).__name__}")

    def get(self, key, default=None):
        return self.value if key in ("value", "val", "v") else default

    def __float__(self): return float(self.value)
    def __int__(self): return int(self.value)
    def __repr__(self): return f"NumLike({self.value!r})"
    def __str__(self): return str(self.value)

    # Basic arithmetic support
    def __add__(self, other): return float(self) + float(other)
    def __radd__(self, other): return float(other) + float(self)
    def __sub__(self, other): return float(self) - float(other)
    def __rsub__(self, other): return float(other) - float(self)
    def __mul__(self, other): return float(self) * float(other)
    def __rmul__(self, other): return float(other) * float(self)
    def __truediv__(self, other): return float(self) / float(other)
    def __rtruediv__(self, other): return float(other) / float(self)
    def __lt__(self, other): return float(self) < float(other)
    def __le__(self, other): return float(self) <= float(other)
    def __gt__(self, other): return float(self) > float(other)
    def __ge__(self, other): return float(self) >= float(other)
    def __eq__(self, other):
        try:
            return float(self) == float(other)
        except Exception:
            return False

def _is_numeric_scalar(x):
    if isinstance(x, (int, float)): return True
    if isinstance(x, str):
        try:
            float(x.replace(",", "."))
            return True
        except ValueError:
            return False
    return False

# Normalize payload to support scalars and quantity-like dicts
def normalize_payload_dual_numeric(obj):
    if isinstance(obj, dict):
        keys = list(obj.keys())
        if len(keys) == 1 and keys[0] in ("value", "val", "v") and _is_numeric_scalar(obj[keys[0]]):
            return obj
        return {k: normalize_payload_dual_numeric(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [normalize_payload_dual_numeric(v) for v in obj]
    if _is_numeric_scalar(obj):
        try:
            return NumLike(obj)
        except Exception:
            return obj
    return obj

# ------------------------------------------------------------------------------
# API: discovery
# ------------------------------------------------------------------------------
@app.route("/api/endpoints")
def endpoints():
    return jsonify({
        "GET": [
            "/api/endpoints",
            "/api/thresholds",
            "/api/metrics",
            "/api/examples/",
            "/api/examples/<filename>",
            "/api/lang",
            "/api/data/uploads",
            "/api/data/uploads/<filename>",
            "/data/",
            "/data/<filename>"
        ],
        "POST": [
            "/api/calculateDisposition",
            "/api/upload/csv"
        ]
    })

# ------------------------------------------------------------------------------
# API: i18n snapshot (desde lang.py)
# ------------------------------------------------------------------------------
@app.route("/api/lang")
def lang_dict():
    return jsonify(LANG.as_dict())

# ------------------------------------------------------------------------------
# API: model data
# ------------------------------------------------------------------------------
@app.route("/api/metrics")
def metricsPage():
    return jsonPage("model/metrics.json")

@app.route("/api/thresholds")
def thresholdsPage():
    return jsonPage("model/thresholds.json")

# ------------------------------------------------------------------------------
# API: classification
# ------------------------------------------------------------------------------
@app.route("/api/calculateDisposition", methods=["POST"])
def calculateDispositionsPage():
    try:
        data = request.get_json(force=True, silent=False)
        if not isinstance(data, dict):
            return jsonify({"error": "Payload must be a JSON object"}), 400
        data.pop("disposition", None)
    except Exception as e:
        print("!! JSON parsing error:", repr(e))
        print(traceback.format_exc())
        return jsonify({"error": f"Invalid JSON: {type(e).__name__}"}), 400

    try:
        data = normalize_payload_dual_numeric(data)
        entry = ExoplanetEntry.from_dict(data)
    except (KeyError, ValueError, TypeError, AttributeError) as e:
        print("!! Entry building error:", repr(e))
        print("Payload received (normalized):", repr(data))
        print(traceback.format_exc())
        return jsonify({"error": f"Invalid payload for ExoplanetEntry: {e}"}), 422
    except Exception as e:
        print("!! Unexpected error while building entry:", repr(e))
        print(traceback.format_exc())
        return jsonify({"error": f"Internal error (entry): {type(e).__name__}"}), 500

    try:
        result = calculateDisposition(entry)
    except AttributeError as e:
        print("!! AttributeError in calculateDisposition:", repr(e))
        print("Entry used:", repr(entry))
        print(traceback.format_exc())
        return jsonify({"error": f"Internal error (classifier): {e}"}), 500
    except Exception as e:
        print("!! Unexpected error in calculateDisposition:", repr(e))
        print(traceback.format_exc())
        return jsonify({"error": f"Internal error (classifier): {type(e).__name__}"}), 500

    try:
        if result is None:
            return jsonify({"error": "Classifier returned no result"}), 500

        if hasattr(result, "name"):
            payload = {"disposition": result.name}
            conf = getattr(result, "confidence", None)
            if conf is not None:
                payload["confidence"] = conf
            return jsonify(payload), 200

        if isinstance(result, dict):
            label = result.get("label") or result.get("disposition") or result.get("name")
            if not label:
                return jsonify({"error": "Classifier response missing label/name"}), 500
            payload = {"disposition": label}
            if "confidence" in result:
                payload["confidence"] = result["confidence"]
            return jsonify(payload), 200

        if isinstance(result, str):
            return jsonify({"disposition": result}), 200

        return jsonify({"disposition": str(result)}), 200

    except Exception as e:
        print("!! Error normalizing classifier output:", repr(e))
        print("Raw classifier output:", repr(result))
        print(traceback.format_exc())
        return jsonify({"error": f"Internal error (output): {type(e).__name__}"}), 500

# ------------------------------------------------------------------------------
# API: examples & datasets (GET JSON/CSV)
# ------------------------------------------------------------------------------
@app.route("/api/examples/<path:filename>")
def examplesPage(filename):
    path = join_path("API/examples", filename)
    return jsonPage(path)

@app.route("/api/examples/")
def examplesList():
    return jsonify(list_files("API/examples"))

@app.route("/data/")
def dataList():
    return jsonify(list_files("data"))

@app.route("/data/<path:filename>")
def dataPage(filename):
    path = join_path("data", filename)
    return csvPage(path)

# ------------------------------------------------------------------------------
# API: uploads CSV (POST subir, GET listar/leer)
# ------------------------------------------------------------------------------
UPLOAD_DIR = os.path.join("data", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
_ALLOWED_EXT = {".csv"}
_MAX_BYTES = 25 * 1024 * 1024  # 25 MB

def _is_csv_name(name: str) -> bool:
    return os.path.splitext(name)[1].lower() in _ALLOWED_EXT

@app.route("/api/upload/csv", methods=["POST"])
def upload_csv():
    if request.content_length and request.content_length > _MAX_BYTES:
        return jsonify({"error": "File too large"}), 413
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    f = request.files["file"]
    if not f.filename:
        return jsonify({"error": "Empty filename"}), 400

    name = secure_filename(f.filename)
    if not _is_csv_name(name):
        return jsonify({"error": "Only .csv files are allowed"}), 415

    replace = (request.args.get("replace", "false").lower() == "true")
    dest = os.path.join(UPLOAD_DIR, name)
    if os.path.exists(dest) and not replace:
        return jsonify({"error": "File exists", "filename": name, "existing": True}), 409

    f.save(dest)

    # Vista previa (best effort)
    columns, rows, preview = [], None, []
    try:
        import pandas as pd
        df = pd.read_csv(dest, engine="python", comment="#")
        columns = list(df.columns)
        rows = int(df.shape[0])
        preview = df.head(20).to_dict(orient="records")
    except Exception:
        pass

    return jsonify({
        "ok": True,
        "filename": name,
        "path": f"data/uploads/{name}",
        "columns": columns,
        "rows": rows,
        "preview": preview
    }), 201

@app.route("/api/data/uploads", methods=["GET"])
def list_uploaded_csv():
    files = []
    for fname in os.listdir(UPLOAD_DIR):
        if _is_csv_name(fname):
            files.append(fname)
    files.sort()
    return jsonify(files)

@app.route("/api/data/uploads/<string:fname>", methods=["GET"])
def get_uploaded_csv(fname: str):
    fname = secure_filename(fname)
    if not _is_csv_name(fname):
        return jsonify({"error": "Invalid file"}), 400
    path = os.path.join(UPLOAD_DIR, fname)
    if not os.path.exists(path):
        return jsonify({"error": "Not found"}), 404
    try:
        data = loadDataCSV(path)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": f"Failed reading CSV: {e}"}), 500

# ------------------------------------------------------------------------------
# Helpers: file responses
# ------------------------------------------------------------------------------
def jsonPage(path: str):
    key: str | None = request.args.get('key')
    data = getJsonFile(path)
    if data is None:
        return error_json("File not found", 404)
    if key is not None:
        if isinstance(data, dict):
            return jsonify(data.get(key, None))
        return error_json("File is not a JSON object; cannot use ?key=", 400)
    return jsonify(data)

def csvPage(path: str):
    data = loadDataCSV(path)
    if data is None:
        return error_json("File not found", 404)
    return jsonify(data)

# ------------------------------------------------------------------------------
# Error handlers (JSON)
# ------------------------------------------------------------------------------
@app.errorhandler(404)
def page_not_found(_event):
    return error_json("Page not found", 404)

def error_json(text: str, statuscode: int = 400):
    return jsonify({"error": text, "status": statuscode}), statuscode

# ------------------------------------------------------------------------------
# SPA: servir build de React en producción
# ------------------------------------------------------------------------------
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_spa(path):
    # Deja /api/* y /data/* para la API
    if path.startswith("api/") or path.startswith("data/"):
        return page_not_found(None)
    # Sirve archivo del build si existe; si no, index.html
    file_path = os.path.join(FRONTEND_DIR, path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return send_from_directory(FRONTEND_DIR, path)
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return send_from_directory(FRONTEND_DIR, "index.html")
    return error_json("Frontend build not found. Run `npm run build` in ./frontend", 501)

# ------------------------------------------------------------------------------
# Dev entrypoint
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(port=2727, debug=True)
