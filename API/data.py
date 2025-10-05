from os.path import exists as file_exists
from pandas import read_csv, DataFrame

from json import load as load_json
from API.entry import ExoplanetEntry, ExoplanetData, Quantity, Disposition, DatasetType
from API.mathUtils import parseNum
    
    
# I/O
def readRawCSV(path, tsv: bool = False, skip_bad_lines: bool = False) -> DataFrame:
    """Reads a CSV to a DataFrame"""
    return read_csv(
        path,
        sep='\t' if tsv else None,
        engine="python",
        comment="#",
        na_values=["", "NA", "NaN"],
        encoding_errors="ignore",
        on_bad_lines="skip" if skip_bad_lines else "error"
    )


def loadDataCSV(path) -> list[dict]:
    """
    Returns the data of the CSV in a list of dicts
    This data is unparsed and will need to be passed through a createDataFrom function.
    """

    if not file_exists(path):
        print(f"Error: El archivo {path} no existe.")
        return None
    
    # Get DataFrame csv
    df: DataFrame = None
    try:
        df = readRawCSV(path)
    except Exception as e:
        print(f"Error al leer el archivo CSV (no TSV): {e}")
        try:
            df = readRawCSV(path, tsv=True, skip_bad_lines=True)
        except Exception as e2:
            print(f"Error al leer el archivo CSV (con TSV): {e2}")
            return None
    
    # Strip column headers
    df.columns = [c.strip() for c in df.columns]
    
    data: list[dict] = df.to_dict("records")
    
    if not data:
        print("Advertencia: El archivo CSV está vacío o no tiene datos válidos.")
        return None
        
    return data


# Parse disposition from string
def getDispositionFromTOI(disposition: str) -> Disposition:
    # candidates (PC)
    # false positives (FP)
    # ambiguous planetary candidates (APC)
    # known planets (KP, previously identified)
    match disposition:
        case "PC": return Disposition.CANDIDATE
        case "APC": return Disposition.AMBIGUOUS_CANDIDATE
        case "FP": return Disposition.FALSE_POSITIVE
        case "KP": return Disposition.CONFIRMED

def getDispositionFromKOI(disposition: str) -> Disposition:
    match disposition:
        case "CANDIDATE": return Disposition.CANDIDATE
        case "FALSE POSITIVE": return Disposition.FALSE_POSITIVE
        case "CONFIRMED": return Disposition.CONFIRMED

def getDispositionFromK2(disposition: str) -> Disposition:
    match disposition:
        case "CANDIDATE": return Disposition.CANDIDATE
        case "FALSE POSITIVE": return Disposition.FALSE_POSITIVE
        case "CONFIRMED": return Disposition.CONFIRMED


# Entry parsers, they get an entry as dict and unify into compatible ExoplanetEntry
# K2 contains additional information, may consider updating ExoplanetEntry
def createEntryFromTOI(dataEntry: dict) -> ExoplanetEntry:
    """Parses a data entry dict from a TOI dataset into an ExoplanetEntry"""
    return ExoplanetEntry(
        id=dataEntry.get("tid"),
        name=dataEntry.get("toi"),
        disposition=getDispositionFromTOI(dataEntry.get("tfopwg_disp")),
        ra=float(dataEntry["ra"]) if dataEntry.get("ra") else None,
        dec=float(dataEntry["dec"]) if dataEntry.get("dec") else None,

        orbital_period=Quantity(
            value=parseNum(dataEntry.get("pl_orbper")),
            err_upper=parseNum(dataEntry.get("pl_orbpererr1")),
            err_lower=parseNum(dataEntry.get("pl_orbpererr2")),
            units="days",
        ),
        transit_epoch=Quantity(
            value=parseNum(dataEntry.get("pl_tranmid")),
            err_upper=parseNum(dataEntry.get("pl_tranmiderr1")),
            err_lower=parseNum(dataEntry.get("pl_tranmiderr2")),
            units="BJD",
        ),
        transit_duration=Quantity(
            value=parseNum(dataEntry.get("pl_trandurh")),
            err_upper=parseNum(dataEntry.get("pl_trandurherr1")),
            err_lower=parseNum(dataEntry.get("pl_trandurherr2")),
            units="hours",
        ),
        transit_depth=Quantity(
            value=parseNum(dataEntry.get("pl_trandep")),
            err_upper=parseNum(dataEntry.get("pl_trandeperr1")),
            err_lower=parseNum(dataEntry.get("pl_trandeperr2")),
            units="ppm",
        ),
        planet_radius=Quantity(
            value=parseNum(dataEntry.get("pl_rade")),
            err_upper=parseNum(dataEntry.get("pl_radeerr1")),
            err_lower=parseNum(dataEntry.get("pl_radeerr2")),
            units="R_Earth",
        ),
        equilibrium_temp=Quantity(
            value=parseNum(dataEntry.get("pl_eqt")),
            err_upper=parseNum(dataEntry.get("pl_eqterr1")),
            err_lower=parseNum(dataEntry.get("pl_eqterr2")),
            units="K",
        ),
        insolation=Quantity(
            value=parseNum(dataEntry.get("pl_insol")),
            err_upper=parseNum(dataEntry.get("pl_insolerr1")),
            err_lower=parseNum(dataEntry.get("pl_insolerr2")),
            units="Earth flux",
        ),

        stellar_temp=Quantity(
            value=parseNum(dataEntry.get("st_teff")),
            err_upper=parseNum(dataEntry.get("st_tefferr1")),
            err_lower=parseNum(dataEntry.get("st_tefferr2")),
            units="K",
        ),
        stellar_logg=Quantity(
            value=parseNum(dataEntry.get("st_logg")),
            err_upper=parseNum(dataEntry.get("st_loggerr1")),
            err_lower=parseNum(dataEntry.get("st_loggerr2")),
            units="cm/s^2",
        ),
        stellar_radius=Quantity(
            value=parseNum(dataEntry.get("st_rad")),
            err_upper=parseNum(dataEntry.get("st_raderr1")),
            err_lower=parseNum(dataEntry.get("st_raderr2")),
            units="R_Sun",
        ),

        created=dataEntry.get("toi_created"),
        updated=dataEntry.get("rowupdate"),
    )

def createEntryFromKOI(dataEntry: dict) -> ExoplanetEntry:
    """Parses a data entry dict from a KOI dataset into an ExoplanetEntry"""
    return ExoplanetEntry(
        id=dataEntry.get("kepid"),
        name=dataEntry.get("kepoi_name") or dataEntry.get("kepler_name"),
        disposition=getDispositionFromKOI(dataEntry.get("koi_disposition") or dataEntry.get("koi_pdisposition")),
        score=parseNum(dataEntry.get("koi_score")),
        ra=float(dataEntry["ra"]) if dataEntry.get("ra") else None,
        dec=float(dataEntry["dec"]) if dataEntry.get("dec") else None,

        orbital_period=Quantity(
            value=parseNum(dataEntry.get("koi_period")),
            err_upper=parseNum(dataEntry.get("koi_period_err1")),
            err_lower=parseNum(dataEntry.get("koi_period_err2")),
            units="days",
        ),
        transit_epoch=Quantity(
            value=parseNum(dataEntry.get("koi_time0bk")),
            err_upper=parseNum(dataEntry.get("koi_time0bk_err1")),
            err_lower=parseNum(dataEntry.get("koi_time0bk_err2")),
            units="BKJD",
        ),
        transit_duration=Quantity(
            value=parseNum(dataEntry.get("koi_duration")),
            err_upper=parseNum(dataEntry.get("koi_duration_err1")),
            err_lower=parseNum(dataEntry.get("koi_duration_err2")),
            units="hours",
        ),
        transit_depth=Quantity(
            value=parseNum(dataEntry.get("koi_depth")),
            err_upper=parseNum(dataEntry.get("koi_depth_err1")),
            err_lower=parseNum(dataEntry.get("koi_depth_err2")),
            units="ppm",
        ),
        planet_radius=Quantity(
            value=parseNum(dataEntry.get("koi_prad")),
            err_upper=parseNum(dataEntry.get("koi_prad_err1")),
            err_lower=parseNum(dataEntry.get("koi_prad_err2")),
            units="R_Earth",
        ),
        equilibrium_temp=Quantity(
            value=parseNum(dataEntry.get("koi_teq")),
            err_upper=parseNum(dataEntry.get("koi_teq_err1")),
            err_lower=parseNum(dataEntry.get("koi_teq_err2")),
            units="K",
        ),
        insolation=Quantity(
            value=parseNum(dataEntry.get("koi_insol")),
            err_upper=parseNum(dataEntry.get("koi_insol_err1")),
            err_lower=parseNum(dataEntry.get("koi_insol_err2")),
            units="Earth flux",
        ),

        stellar_temp=Quantity(
            value=parseNum(dataEntry.get("koi_steff")),
            err_upper=parseNum(dataEntry.get("koi_steff_err1")),
            err_lower=parseNum(dataEntry.get("koi_steff_err2")),
            units="K",
        ),
        stellar_logg=Quantity(
            value=parseNum(dataEntry.get("koi_slogg")),
            err_upper=parseNum(dataEntry.get("koi_slogg_err1")),
            err_lower=parseNum(dataEntry.get("koi_slogg_err2")),
            units="cm/s^2",
        ),
        stellar_radius=Quantity(
            value=parseNum(dataEntry.get("koi_srad")),
            err_upper=parseNum(dataEntry.get("koi_srad_err1")),
            err_lower=parseNum(dataEntry.get("koi_srad_err2")),
            units="R_Sun",
        ),

        # Metadata
        created=None,  # no direct field in KOI
        updated=dataEntry.get("koi_tce_delivname"),
    )

def createEntryFromK2(dataEntry: dict) -> ExoplanetEntry:
    """Parses a data entry dict from a K2/Exoplanet Archive dataset into an ExoplanetEntry"""
    return ExoplanetEntry(
        id=dataEntry.get("pl_name"),   # exoplanet name (preferred identifier)
        name=dataEntry.get("hostname"),  # host star name
        disposition=getDispositionFromK2(dataEntry.get("disposition")),
        ra=parseNum(dataEntry.get("ra")),
        dec=parseNum(dataEntry.get("dec")),

        # Planetary properties
        orbital_period=Quantity(
            value=parseNum(dataEntry.get("pl_orbper")),
            err_upper=parseNum(dataEntry.get("pl_orbpererr1")),
            err_lower=parseNum(dataEntry.get("pl_orbpererr2")),
            units="days",
        ),
        planet_radius=Quantity(
            value=parseNum(dataEntry.get("pl_rade")),
            err_upper=parseNum(dataEntry.get("pl_radeerr1")),
            err_lower=parseNum(dataEntry.get("pl_radeerr2")),
            units="R_Earth",
        ),
        equilibrium_temp=Quantity(
            value=parseNum(dataEntry.get("pl_eqt")),
            err_upper=parseNum(dataEntry.get("pl_eqterr1")),
            err_lower=parseNum(dataEntry.get("pl_eqterr2")),
            units="K",
        ),
        insolation=Quantity(
            value=parseNum(dataEntry.get("pl_insol")),
            err_upper=parseNum(dataEntry.get("pl_insolerr1")),
            err_lower=parseNum(dataEntry.get("pl_insolerr2")),
            units="Earth flux",
        ),

        # Stellar properties
        stellar_temp=Quantity(
            value=parseNum(dataEntry.get("st_teff")),
            err_upper=parseNum(dataEntry.get("st_tefferr1")),
            err_lower=parseNum(dataEntry.get("st_tefferr2")),
            units="K",
        ),
        stellar_logg=Quantity(
            value=parseNum(dataEntry.get("st_logg")),
            err_upper=parseNum(dataEntry.get("st_loggerr1")),
            err_lower=parseNum(dataEntry.get("st_loggerr2")),
            units="cm/s^2",
        ),
        stellar_radius=Quantity(
            value=parseNum(dataEntry.get("st_rad")),
            err_upper=parseNum(dataEntry.get("st_raderr1")),
            err_lower=parseNum(dataEntry.get("st_raderr2")),
            units="R_Sun",
        ),

        # Metadata
        created=dataEntry.get("pl_pubdate"),
        updated=dataEntry.get("rowupdate"),
    )


# Data parsing
def getDataType(data: list[dict]) -> DatasetType:
    keys = data[0].keys()
    
    if "kepid" in keys:
        return DatasetType.KOI
    if "toi" in keys:
        return DatasetType.TOI
    if "st_met" in keys:  # K2 doesnt have an "unique key" but the other ones don't have metallicity
        return DatasetType.K2
    return DatasetType.UNKNOWN

def createDataFrom(entryParser: callable, data: list[dict]) -> ExoplanetData:
    """Uses entry parser to parse data into an ExoplanetData"""
    datasetType: DatasetType = getDataType(data)
    
    entries = []
    for entry in data:
        parsedEntry: ExoplanetEntry = entryParser(entry)
        entries.append(parsedEntry)
    
    return ExoplanetData(datasetType, entries)

def readAndCreateData(path: str) -> ExoplanetData:
    """Read and parse data into ExoplanetData without specifying an entry parser."""
    data = loadDataCSV(path)
    
    if data is None:
        return None  # Si no se cargan datos, devolver None
    
    datasetType: DatasetType = getDataType(data)
    
    entryParser: callable = None
    match datasetType:
        case DatasetType.KOI:
            entryParser = createEntryFromKOI
        case DatasetType.TOI:
            entryParser = createEntryFromTOI
        case DatasetType.K2:
            entryParser = createEntryFromK2
        case DatasetType.UNKNOWN:
            entryParser = None
            
    if not entryParser:
        raise ValueError(
            f"An apropiate entry parser for DatasetType \"{datasetType}\" wasn't found.",
            f"Dataset keys: {data[0].keys()}"
        )
        
    return createDataFrom(entryParser, data)

def getJsonFile(path: str) -> dict | None:
    if not file_exists(path):
        return None
    with open(path, "r") as fp:
        return load_json(fp)
