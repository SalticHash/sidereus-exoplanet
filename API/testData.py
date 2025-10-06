import warnings
warnings.filterwarnings("ignore")

import os
import numpy as np
import pandas as pd  
from lightkurve import search_lightcurve    
from astropy import units as u
from tsfresh import extract_features
from tsfresh.feature_extraction import EfficientFCParameters
from sklearn.model_selection import GroupKFold
from sklearn.metrics import roc_auc_score, precision_recall_curve
import lightgbm as lgb

from API.analyse import calculateDisposition
from API.data import readAndCreateData, createEntryFromTOI, createEntryFromKOI, createEntryFromK2  
from API.entry import ExoplanetEntry, ExoplanetData, Quantity
from API.data import getDataType, DatasetType  


def load_and_process_data(csv_path):
    # Data was loaded from CSV
    # Se cargaron los datos desde el CSV
    exoplantetData: ExoplanetData = readAndCreateData(csv_path) 
    
    # Data was verified
    # Se verificaron los datos
    if len(exoplantetData.entries) == 0:
        print("Failed to load the data.")
        return []
    if exoplantetData.dataset_type == DatasetType.UNKNOWN:
        print("Unsupported dataset type.")
        return []
    
    exoplanets = []
    
    # Entries were processed
    # Se procesaron las entradas
    for entry in exoplantetData:
        disposition = calculateDisposition(entry)  
        exoplanets.append((entry, disposition)) 
    
    return exoplanets


# Paths were defined
# Se definieron las rutas
csv_path_koi = 'data/KOI.csv'
csv_path_toi = 'data/TOI.csv'
csv_path_k2 = 'data/K2.csv'

# KOI dataset was processed
# Se procesó el conjunto de datos KOI
exoplanet_entries_koi = load_and_process_data(csv_path_koi)
for entry, disposition in exoplanet_entries_koi:
    print(f"KOI Exoplanet: {entry}, Disposition: {disposition}")

# TOI dataset was processed
# Se procesó el conjunto de datos TOI
exoplanet_entries_toi = load_and_process_data(csv_path_toi)
for entry, disposition in exoplanet_entries_toi:
    print(f"TOI Exoplanet: {entry}, Disposition: {disposition}")

# K2 dataset was processed
# Se procesó el conjunto de datos K2
exoplanet_entries_k2 = load_and_process_data(csv_path_k2)
for entry, disposition in exoplanet_entries_k2:
    print(f"K2 Exoplanet: {entry}, Disposition: {disposition}")
