from __future__ import annotations
import os
import json
import csv
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Union

# pandas was checked as optional
# Se comprobó pandas como opcional
try:
    import pandas as pd  # type: ignore
    _HAS_PANDAS = True
except Exception:
    _HAS_PANDAS = False

# Entry types were imported
# Se importaron los tipos de entrada
from API.entry import (
    ExoplanetEntry,
    Quantity,
    DatasetType,
    Disposition,
)


def getJsonFile(path: str) -> Optional[Union[Dict[str, Any], List[Any]]]:
    # JSON file was read
    # Se leyó el archivo JSON
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def saveJsonFile(path: str, data: Union[Dict[str, Any], List[Any]]) -> None:
    # JSON file was saved
    # Se guardó el archivo JSON
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _read_csv_with_pandas(path: str) -> List[Dict[str, Any]]:
    # CSV was read using pandas
    # Se leyó el CSV usando pandas
    df = pd.read_csv(path, engine="python", comment="#")
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    df = df.where(pd.notnull(df), None)
    return df.to_dict(orient="records")

def _read_csv_with_stdlib(path: str) -> List[Dict[str, Any]]:
    # CSV was read using stdlib
    # Se leyó el CSV con la biblioteca estándar
    rows: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(line for line in f if not line.lstrip().startswith("#"))
        if reader.fieldnames:
            reader.fieldnames = [c.strip().lower().replace(" ", "_") for c in reader.fieldnames]
        for r in reader:
            rows.append({k: (v if v != "" else None) for k, v in r.items()})
    return rows

def loadDataCSV(path: str) -> List[Dict[str, Any]]:
    # CSV data was loaded
    # Se cargaron los datos CSV
    if not os.path.exists(path):
        return []
    try:
        return _read_csv_with_pandas(path) if _HAS_PANDAS else _read_csv_with_stdlib(path)
    except Exception:
        # Fallback was used
        # Se usó el método alternativo
        return _read_csv_with_stdlib(path)


def _num(x: Any) -> Optional[float]:
    # Value was converted to float
    # Se convirtió el valor a float
    if x is None:
        return None
    try:
        s = str(x).strip().replace(",", "")
        return float(s)
    except Exception:
        return None

def _first(row: Dict[str, Any], keys: Sequence[str]) -> Any:
    # First valid key was found
    # Se encontró la primera clave válida
    for k in keys:
        if k in row and row[k] not in (None, ""):
            return row[k]
    return None

def _Q(row: Dict[str, Any], keys: Sequence[str], units: Optional[str]) -> Quantity:
    # Quantity object was created
    # Se creó el objeto Quantity
    return Quantity.from_value(_num(_first(row, keys)), units)

def _normalize_disposition(text: Optional[str]) -> Optional[Disposition]:
    """Normalize text into Disposition enum."""
    # Text disposition was normalized
    # Se normalizó el texto de la disposición
    if not text:
        return None
    t = str(text).strip().upper()
    if "CONFIRM" in t or t == "KP":
        return Disposition.CONFIRMED
    if "FALSE" in t or t == "FP":
        return Disposition.FALSE_POSITIVE
    if "CAND" in t or t == "PC":
        return Disposition.CANDIDATE
    if "AMB" in t or "APC" in t:
        return Disposition.AMBIGUOUS_CANDIDATE
    return None


def createEntryFromKOI(row: Dict[str, Any]) -> ExoplanetEntry:
    # KOI entry was created
    # Se creó la entrada KOI
    dispo = _normalize_disposition(_first(row, ["koi_disposition", "koi_pdisposition", "disposition"]))
    return ExoplanetEntry(
        id=_first(row, ["kepid", "kic", "rowid"]),
        name=_first(row, ["kepoi_name", "kepler_name"]),
        disposition=dispo,
        score=_num(_first(row, ["koi_score"])),
        ra=_num(_first(row, ["ra", "ra_str"])),
        dec=_num(_first(row, ["dec", "dec_str"])),
        orbital_period=_Q(row, ["koi_period", "orbital_period"], "days"),
        transit_epoch=_Q(row, ["koi_time0bk", "transit_epoch"], "BJD"),
        transit_duration=_Q(row, ["koi_duration", "transit_duration"], "hours"),
        transit_depth=_Q(row, ["koi_depth", "transit_depth"], "ppm"),
        planet_radius=_Q(row, ["koi_prad", "planet_radius"], "R_Earth"),
        equilibrium_temp=_Q(row, ["koi_teq", "equilibrium_temp"], "K"),
        insolation=_Q(row, ["insol", "insolation"], "Earth flux"),
        stellar_temp=_Q(row, ["koi_steff", "teff", "stellar_temp"], "K"),
        stellar_logg=_Q(row, ["koi_slogg", "logg", "stellar_logg"], "cm/s^2"),
        stellar_radius=_Q(row, ["koi_srad", "radius", "stellar_radius"], "R_Sun"),
        created=_first(row, ["koi_tce_delivname", "created"]),
        updated=_first(row, ["rowupdate", "updated"]),
    )

def createEntryFromTOI(row: Dict[str, Any]) -> ExoplanetEntry:
    # TOI entry was created
    # Se creó la entrada TOI
    dispo = _normalize_disposition(_first(row, ["tfopwg_disp", "tfopwg_disposition", "disposition"]))
    return ExoplanetEntry(
        id=_first(row, ["tid", "ticid", "tic_id", "tic"]),
        name=_first(row, ["toi", "toi_name", "name"]),
        disposition=dispo,
        ra=_num(_first(row, ["ra", "ra_deg"])),
        dec=_num(_first(row, ["dec", "dec_deg"])),
        orbital_period=_Q(row, ["orbital_period", "period", "pl_orbper"], "days"),
        transit_epoch=_Q(row, ["transit_epoch", "epoch_bjd"], "BJD"),
        transit_duration=_Q(row, ["transit_duration", "duration_hours"], "hours"),
        transit_depth=_Q(row, ["transit_depth", "depth_ppm"], "ppm"),
        planet_radius=_Q(row, ["planet_radius", "planetradius_earth"], "R_Earth"),
        equilibrium_temp=_Q(row, ["equilibrium_temp", "teq_k"], "K"),
        insolation=_Q(row, ["insolation", "sinc_earth"], "Earth flux"),
        stellar_temp=_Q(row, ["stellar_temp", "stellarteff_k"], "K"),
        stellar_logg=_Q(row, ["stellar_logg", "stellarlogg_cgs"], "cm/s^2"),
        stellar_radius=_Q(row, ["stellar_radius", "stellarradius_rsun"], "R_Sun"),
        created=_first(row, ["toi_created", "created"]),
        updated=_first(row, ["rowupdate", "updated"]),
    )

def createEntryFromK2(row: Dict[str, Any]) -> ExoplanetEntry:
    # K2 entry was created
    # Se creó la entrada K2
    dispo = _normalize_disposition(_first(row, ["disposition"]))
    return ExoplanetEntry(
        id=_first(row, ["epic_id", "k2id", "id"]),
        name=_first(row, ["name"]),
        disposition=dispo,
        ra=_num(_first(row, ["ra"])),
        dec=_num(_first(row, ["dec"])),
        orbital_period=_Q(row, ["period", "orbital_period"], "days"),
        transit_epoch=_Q(row, ["epoch_bjd", "transit_epoch"], "BJD"),
        transit_duration=_Q(row, ["duration_hours", "transit_duration"], "hours"),
        transit_depth=_Q(row, ["depth_ppm", "transit_depth"], "ppm"),
        planet_radius=_Q(row, ["prad_re", "planet_radius"], "R_Earth"),
        equilibrium_temp=_Q(row, ["teq_k", "equilibrium_temp"], "K"),
        insolation=_Q(row, ["insolation", "sinc_earth"], "Earth flux"),
        stellar_temp=_Q(row, ["teff_k", "stellar_temp"], "K"),
        stellar_logg=_Q(row, ["logg_cgs", "stellar_logg"], "cm/s^2"),
        stellar_radius=_Q(row, ["rstar_rsun", "stellar_radius"], "R_Sun"),
    )

@dataclass
class ExoplanetData:
    # Exoplanet data container was defined
    # Se definió el contenedor de datos de exoplanetas
    entries: List[ExoplanetEntry] = field(default_factory=list)
    dataset_type: DatasetType = DatasetType.UNKNOWN

    def __iter__(self):
        # Iterable behavior was implemented
        # Se implementó el comportamiento iterable
        return iter(self.entries)


def getDataType(name_or_path: str) -> DatasetType:
    # Dataset type was detected
    # Se detectó el tipo de dataset
    base = os.path.basename(name_or_path).upper()
    if "KOI" in base or "KEPLER" in base:
        return DatasetType.KOI
    if "TOI" in base or "TESS" in base:
        return DatasetType.TOI
    if "K2" in base:
        return DatasetType.K2
    return DatasetType.UNKNOWN

def _build_entries(rows: List[Dict[str, Any]], ds: DatasetType) -> List[ExoplanetEntry]:
    # Entries were built from rows
    # Se construyeron las entradas a partir de filas
    maker = createEntryFromKOI if ds == DatasetType.KOI else (
            createEntryFromTOI if ds == DatasetType.TOI else createEntryFromK2)
    out: List[ExoplanetEntry] = []
    for r in rows:
        try:
            out.append(maker(r))
        except Exception:
            # Faulty row was skipped
            # Se omitió una fila defectuosa
            continue
    return out


def createDataFrom(path: str) -> ExoplanetData:
    # Data was created from file
    # Se crearon los datos desde el archivo
    rows = loadDataCSV(path)
    ds = getDataType(path)
    entries = _build_entries(rows, ds)
    return ExoplanetData(entries, ds)

def readAndCreateData(input_path: str, *, as_dict: bool = False):
    """Reads KOI/TOI/K2 CSVs and returns ExoplanetData."""
    # Data was read and processed
    # Se leyeron y procesaron los datos
    if os.path.isdir(input_path):
        all_entries: List[ExoplanetEntry] = []
        ds_seen: set[DatasetType] = set()
        for name in sorted(os.listdir(input_path)):
            if not name.lower().endswith(".csv"):
                continue
            file_path = os.path.join(input_path, name)
            ds = getDataType(file_path)
            rows = loadDataCSV(file_path)
            all_entries.extend(_build_entries(rows, ds))
            ds_seen.add(ds)
        ds_final = next(iter(ds_seen)) if len(ds_seen) == 1 else DatasetType.UNKNOWN
        data_obj = ExoplanetData(all_entries, ds_final)
    else:
        data_obj = createDataFrom(input_path)

    if as_dict:
        # Dictionary format was returned
        # Se devolvió en formato diccionario
        return {
            "entries": [e.__dict__ for e in data_obj.entries],
            "dataset_type": data_obj.dataset_type.name,
        }
    # Data object was returned
    # Se devolvió el objeto de datos
    return data_obj
