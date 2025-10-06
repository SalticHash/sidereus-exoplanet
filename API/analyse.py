# analyse.py
import numpy as np
import pandas as pd
import joblib, json
import os

from API.entry import ExoplanetEntry, Disposition

# Model and files were prepared
# Se prepararon el modelo y los archivos
_MODEL = None
_THR = None
_COLUMNS = None


def _load_model_and_thresholds():
    """Loads the model and thresholds from saved files."""
    # Model and config files were loaded
    # Se cargaron los archivos del modelo y configuración
    global _MODEL, _THR, _COLUMNS
    if _MODEL is None:
        if not os.path.exists("./model/model_lgb.pkl"):
            raise FileNotFoundError("Model file ./model/model_lgb.pkl not found. Train the model first.")
        if not os.path.exists("./model/thresholds.json"):
            raise FileNotFoundError("Threshold file ./model/thresholds.json not found. Train the model first.")
        if not os.path.exists("./model/columns_used.json"):
            raise FileNotFoundError("Columns file ./model/columns_used.json not found. Train the model first.")
        
        _MODEL = joblib.load("./model/model_lgb.pkl")
        with open("./model/thresholds.json") as f:
            _THR = json.load(f)
        with open("./model/columns_used.json") as f:
            _COLUMNS = json.load(f)
    return _MODEL, _THR, _COLUMNS


def _entry_to_row(entry: ExoplanetEntry) -> dict[str, float]:
    """Converts an ExoplanetEntry into a feature dictionary for the model."""
    # Entry data was converted into a row
    # Se convirtió la entrada en una fila

    def v(q):
        try:
            return None if q is None else q.value
        except Exception:
            return None

    row = {
        "orbital_period":    v(entry.orbital_period),
        "transit_epoch":     v(entry.transit_epoch),
        "transit_duration":  v(entry.transit_duration),
        "transit_depth":     v(entry.transit_depth),
        "planet_radius":     v(entry.planet_radius),
        "equilibrium_temp":  v(entry.equilibrium_temp),
        "insolation":        v(entry.insolation),
        "stellar_temp":      v(entry.stellar_temp),
        "stellar_logg":      v(entry.stellar_logg),
        "stellar_radius":    v(entry.stellar_radius),
    }

    # Extra features were calculated
    # Se calcularon características adicionales
    td  = row["transit_duration"]
    dep = row["transit_depth"]
    row["depth_over_duration"] = (dep/td) if (dep is not None and td and td > 0) else None
    row["log_depth"]           = np.log10(dep) if (dep is not None and dep > 0) else None
    row["log_duration"]        = np.log10(td)  if (td  is not None and td  > 0) else None
    row["log_orbital_period"]  = np.log10(row["orbital_period"]) if (row["orbital_period"] is not None and row["orbital_period"] > 0) else None
    row["log_planet_radius"]   = np.log10(row["planet_radius"]) if (row["planet_radius"] is not None and row["planet_radius"] > 0) else None

    # Missing value flags were added
    # Se agregaron indicadores de valores faltantes
    for k in list(row.keys()):
        val = row[k]
        row[f"isnan_{k}"] = 1 if (val is None or (isinstance(val, float) and np.isnan(val))) else 0

    # Score field was included
    # Se incluyó el campo de puntuación
    row["score"] = entry.score if hasattr(entry, 'score') and entry.score is not None else None
    
    # Dataset flags were initialized
    # Se inicializaron los indicadores del conjunto de datos
    row["dataset_K2"] = 0
    row["dataset_KOI"] = 0
    row["dataset_TOI"] = 0
    row["dataset_UNKNOWN"] = 1  # Default to UNKNOWN
    
    return row


def calculateDisposition(entry: ExoplanetEntry) -> Disposition:
    """Calculates the exoplanet disposition using the model."""
    # Model and thresholds were loaded
    # Se cargaron el modelo y los umbrales
    try:
        model, thr, columns_used = _load_model_and_thresholds()
    except Exception as e:
        print(f"[WARN] Model not available: {e}")
        return Disposition.AMBIGUOUS_CANDIDATE

    try:
        # Entry was converted for the model
        # Se convirtió la entrada para el modelo
        entry_row = _entry_to_row(entry)
        
        # DataFrame was created with required columns
        # Se creó el DataFrame con las columnas requeridas
        x_dict = {}
        for col in columns_used:
            if col in entry_row:
                x_dict[col] = [entry_row[col]]
            else:
                # Default value was set for missing columns
                # Se asignó valor por defecto a columnas faltantes
                x_dict[col] = [0 if col.startswith('isnan_') or col.startswith('dataset_') else -999]
        
        x = pd.DataFrame(x_dict)
        
        # Missing values were replaced
        # Se reemplazaron los valores faltantes
        x = x.fillna(-999)

        # Probability was predicted
        # Se predijo la probabilidad
        prob = float(model.predict_proba(x)[:, 1][0])
    except Exception as e:
        print(f"[WARN] Prediction failed: {e}")
        import traceback
        traceback.print_exc()
        return Disposition.AMBIGUOUS_CANDIDATE

    # Invalid probabilities were checked
    # Se verificaron probabilidades no válidas
    if np.isnan(prob):
        return Disposition.AMBIGUOUS_CANDIDATE

    # Thresholds were retrieved
    # Se recuperaron los umbrales
    tau_low  = float(thr["tau_low"])
    tau_high = float(thr["tau_high"])

    # Disposition result was decided
    # Se decidió el resultado de la disposición
    if prob >= tau_high:
        return Disposition.CANDIDATE
    if prob <= tau_low:
        return Disposition.FALSE_POSITIVE
    return Disposition.AMBIGUOUS_CANDIDATE



if __name__ == "__main__":
    from entry import Quantity
    
    # Example entry was created
    # Se creó una entrada de ejemplo
    example_entry = ExoplanetEntry(
        id="TEST001",
        name="Test Exoplanet",
        orbital_period=Quantity(value=365.25, units="days"),
        transit_epoch=Quantity(value=2451545.0, units="BJD"),
        transit_duration=Quantity(value=10.0, units="hours"),
        transit_depth=Quantity(value=100.0, units="ppm"),
        planet_radius=Quantity(value=1.0, units="R_Earth"),
        equilibrium_temp=Quantity(value=300.0, units="K"),
        insolation=Quantity(value=1.0, units="Earth flux"),
        stellar_temp=Quantity(value=5778, units="K"),
        stellar_logg=Quantity(value=4.4, units="cm/s^2"),
        stellar_radius=Quantity(value=1.0, units="R_Sun"),
    )

    # Disposition was calculated
    # Se calculó la disposición
    disposition = calculateDisposition(example_entry)

    # Result was displayed
    # Se mostró el resultado
    print(f"The exoplanet disposition is: {disposition}")
