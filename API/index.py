from lang import LANG
from API.data import getJsonFile, loadDataCSV
from API.entry import ExoplanetEntry
from API.analyse import calculateDisposition
from os.path import join as join_path
from os import listdir as list_files, getenv as get_env
from dotenv import load_dotenv
from requests import get as fetch, ConnectionError

from flask import Flask, render_template, request, jsonify

import traceback

load_dotenv()
APOD_API_KEY = get_env("APOD_API_KEY") or "DEMO_KEY"
# Loads API key from environment or uses a safe default
# Carga la clave de API del entorno o usa un valor seguro por defecto

app = Flask(__name__)
app.jinja_env.globals.update(lang=LANG)
# Makes the language dictionary accessible in Jinja templates
# Hace accesible el diccionario de idioma en las plantillas Jinja


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
    if isinstance(x, (int, float)):
        return True
    if isinstance(x, str):
        try:
            float(x.replace(",", "."))
            return True
        except ValueError:
            return False
    return False


def normalize_payload_dual_numeric(obj):
    """Convierte números simples o dicts tipo {'value': ...} a objetos NumLike."""
    # Converts incoming numeric fields into NumLike objects for consistency
    # Convierte campos numéricos entrantes en objetos NumLike para consistencia
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


@app.route("/")
def index():
    """Renderiza la interfaz principal con los tabs y el JS local."""
    return render_template("index.html")


@app.route("/api/")
def api_home():
    """Alias opcional para /api/."""
    return render_template("index.html")


@app.route("/api/endpoints")
def endpoints():
    return jsonify({
        "GET": [
            "/api/endpoints",
            "/api/thresholds",
            "/api/metrics",
            "/api/examples/",
            "/api/examples/<filename>",
            "/data/",
            "/data/<filename>"
        ],
        "POST": [
            "/api/calculateDisposition"
        ]
    })


@app.route("/api/metrics")
def metricsPage():
    return jsonPage("model/metrics.json")


@app.route("/api/thresholds")
def thresholdsPage():
    return jsonPage("model/thresholds.json")


@app.route("/api/calculateDisposition", methods=["POST"], endpoint="calculateDisposition")
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

    # Converts JSON payload into ExoplanetEntry for classification
    # Convierte el JSON recibido en una instancia ExoplanetEntry para clasificar
    try:
        data = normalize_payload_dual_numeric(data)
        entry = ExoplanetEntry.from_dict(data)
    except (KeyError, ValueError, TypeError, AttributeError) as e:
        print("!! Entry building error:", repr(e))
        print(traceback.format_exc())
        return jsonify({"error": f"Invalid payload for ExoplanetEntry: {e}"}), 422
    except Exception as e:
        print("!! Unexpected error while building entry:", repr(e))
        print(traceback.format_exc())
        return jsonify({"error": f"Internal error (entry): {type(e).__name__}"}), 500

    # Runs the main classifier to predict the planet's disposition
    # Ejecuta el clasificador principal para predecir la disposición del planeta
    try:
        result = calculateDisposition(entry)
    except AttributeError as e:
        print("!! AttributeError in calculateDisposition:", repr(e))
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
        print(traceback.format_exc())
        return jsonify({"error": f"Internal error (output): {type(e).__name__}"}), 500


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


def jsonPage(path: str):
    key = request.args.get("key")
    data = getJsonFile(path)
    if data is None:
        return error("File not found", 404)
    if key is not None and isinstance(data, dict):
        return jsonify({key: data.get(key)})
    return jsonify(data)


def csvPage(path: str):
    data = loadDataCSV(path)
    if data is None:
        return error("File not found", 404)
    return jsonify(data)


@app.errorhandler(404)
def page_not_found(_event):
    return error("Page not found, It's nowhere to be seen", 404)


def error(text, statuscode=400):
    req = {"text": text, "statuscode": statuscode}
    # Renders a simple error page with message and code
    # Renderiza una página de error simple con mensaje y código
    return render_template("error.html", req=req), statuscode


if __name__ == "__main__":
    # Starts local development server on port 2727
    # Inicia el servidor local de desarrollo en el puerto 2727
    app.run(port=2727, debug=True)
