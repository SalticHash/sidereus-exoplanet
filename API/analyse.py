# analyse.py
import numpy as np
import pandas as pd
import joblib, json
import os

from API.entry import ExoplanetEntry, Disposition

# Load model and thresholds from files
_MODEL = None
_THR = None
_COLUMNS = None

def _load_model_and_thresholds():
    """Loads the model and thresholds from saved files."""
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

    # Derived features
    td  = row["transit_duration"]
    dep = row["transit_depth"]
    row["depth_over_duration"] = (dep/td) if (dep is not None and td and td > 0) else None
    row["log_depth"]           = np.log10(dep) if (dep is not None and dep > 0) else None
    row["log_duration"]        = np.log10(td)  if (td  is not None and td  > 0) else None
    row["log_orbital_period"]  = np.log10(row["orbital_period"]) if (row["orbital_period"] is not None and row["orbital_period"] > 0) else None
    row["log_planet_radius"]   = np.log10(row["planet_radius"]) if (row["planet_radius"] is not None and row["planet_radius"] > 0) else None

    # Missing value indicators
    for k in list(row.keys()):
        val = row[k]
        row[f"isnan_{k}"] = 1 if (val is None or (isinstance(val, float) and np.isnan(val))) else 0

    # Score if available
    row["score"] = entry.score if hasattr(entry, 'score') and entry.score is not None else None
    
    # Datasets as one-hot encoding (same format as during training)
    row["dataset_K2"] = 0
    row["dataset_KOI"] = 0
    row["dataset_TOI"] = 0
    row["dataset_UNKNOWN"] = 1  # Default to UNKNOWN
    
    return row

def calculateDisposition(entry: ExoplanetEntry) -> Disposition:
    """
    Calculates the exoplanet disposition based on the trained model and precision thresholds.
    """
    try:
        model, thr, columns_used = _load_model_and_thresholds()
    except Exception as e:
        print(f"[WARN] Model not available: {e}")
        return Disposition.AMBIGUOUS_CANDIDATE

    try:
        # Convert entry into a format the model can use
        entry_row = _entry_to_row(entry)
        
        # Create DataFrame with the correct columns
        x_dict = {}
        for col in columns_used:
            if col in entry_row:
                x_dict[col] = [entry_row[col]]
            else:
                # If column is missing, use default value
                x_dict[col] = [0 if col.startswith('isnan_') or col.startswith('dataset_') else -999]
        
        x = pd.DataFrame(x_dict)
        
        # Replace None with -999 (same value used during training)
        x = x.fillna(-999)

        # Make prediction
        prob = float(model.predict_proba(x)[:, 1][0])
    except Exception as e:
        print(f"[WARN] Prediction failed: {e}")
        import traceback
        traceback.print_exc()
        return Disposition.AMBIGUOUS_CANDIDATE

    if np.isnan(prob):
        return Disposition.AMBIGUOUS_CANDIDATE

    tau_low  = float(thr["tau_low"])
    tau_high = float(thr["tau_high"])

    if prob >= tau_high:
        return Disposition.CANDIDATE
    if prob <= tau_low:
        return Disposition.FALSE_POSITIVE
    return Disposition.AMBIGUOUS_CANDIDATE


# ====================================
# Quick Example
# ====================================
if __name__ == "__main__":
    from entry import Quantity
    
    # Manually create an example entry
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

    # Classification using the model
    disposition = calculateDisposition(example_entry)

    # Display the resulting disposition
    print(f"The exoplanet disposition is: {disposition}")
