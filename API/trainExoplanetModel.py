import os
import sys
import json
import warnings
warnings.filterwarnings("ignore")

from typing import List, Tuple, Optional
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.metrics import (
    precision_recall_curve, 
    average_precision_score, 
    roc_auc_score,
    classification_report,
    confusion_matrix
)
from sklearn.preprocessing import LabelEncoder
import lightgbm as lgb
import joblib

from API.data import (
    readAndCreateData,
    getDataType,
    DatasetType
)
from API.entry import Disposition, ExoplanetEntry, ExoplanetData

# =========================
# Feature Engineering
# =========================
def entry_to_features(entry: ExoplanetEntry, dataset_type: DatasetType) -> dict:
    """
    Converts an ExoplanetEntry to a feature dictionary for the model.
    """
    def safe_value(quantity):
        """Safely extract the value from a Quantity object."""
        try:
            if quantity is None:
                return None
            if hasattr(quantity, 'value'):
                return quantity.value
            return None
        except:
            return None
    
    # Main features
    features = {
        "orbital_period": safe_value(entry.orbital_period),
        "transit_epoch": safe_value(entry.transit_epoch),
        "transit_duration": safe_value(entry.transit_duration),
        "transit_depth": safe_value(entry.transit_depth),
        "planet_radius": safe_value(entry.planet_radius),
        "equilibrium_temp": safe_value(entry.equilibrium_temp),
        "insolation": safe_value(entry.insolation),
        "stellar_temp": safe_value(entry.stellar_temp),
        "stellar_logg": safe_value(entry.stellar_logg),
        "stellar_radius": safe_value(entry.stellar_radius),
    }
    
    # Derived features
    td = features["transit_duration"]
    dep = features["transit_depth"]
    
    # Depth/Duration ratio
    features["depth_over_duration"] = (dep/td) if (dep is not None and td and td > 0) else None
    
    # Logarithmic features
    features["log_depth"] = np.log10(dep) if (dep is not None and dep > 0) else None
    features["log_duration"] = np.log10(td) if (td is not None and td > 0) else None
    features["log_orbital_period"] = np.log10(features["orbital_period"]) if (features["orbital_period"] is not None and features["orbital_period"] > 0) else None
    
    # Additional derived features
    if features["planet_radius"] is not None and features["planet_radius"] > 0:
        features["log_planet_radius"] = np.log10(features["planet_radius"])
    else:
        features["log_planet_radius"] = None
    
    # Missing value indicators
    for key in list(features.keys()):
        val = features[key]
        features[f"isnan_{key}"] = 1 if (val is None or (isinstance(val, float) and np.isnan(val))) else 0
    
    # Dataset type as categorical feature
    features["dataset"] = dataset_type.name if dataset_type else "UNKNOWN"
    
    # Score if available (only KOI)
    features["score"] = entry.score if hasattr(entry, 'score') else None
    
    return features

# =========================
# Load and process data
# =========================
def load_and_process_csv(csv_path: str) -> Tuple[List[dict], List[int], DatasetType]:
    """
    Loads a CSV and processes entries, returning features and labels.
    """
    print(f"\n[INFO] Loading data from: {csv_path}")
    
    # Load raw data
    exoplanet_data: ExoplanetData = readAndCreateData(csv_path)
    if not exoplanet_data.entries:
        print(f"[ERROR] Could not load data from {csv_path}")
        return [], [], None
    
    # Print dataset type
    print(f"[INFO] Detected dataset type: {exoplanet_data.dataset_type}")
    

    if exoplanet_data.dataset_type == DatasetType.UNKNOWN:
        print(f"[ERROR] Unsupported dataset type: {exoplanet_data.dataset_type}")
        return [], [], None
    
    
    # Process entries
    features_list = []
    labels_list = []
    skipped = 0
    
    for i, entry in enumerate(exoplanet_data):
        try:            
            # Check if we have a valid disposition
            if entry.disposition is None:
                skipped += 1
                continue
            
            # Only use entries with clear disposition for training
            if entry.disposition in [Disposition.CANDIDATE, Disposition.CONFIRMED]:
                label = 1  # Positive (real planet)
            elif entry.disposition == Disposition.FALSE_POSITIVE:
                label = 0  # Negative (false positive)
            else:
                # Skip ambiguous cases for training
                skipped += 1
                continue
            
            # Extract features
            features = entry_to_features(entry, exoplanet_data.dataset_type)
            
            features_list.append(features)
            labels_list.append(label)
            
        except Exception as e:
            skipped += 1
            if i < 5:  # Show only first few errors
                print(f"[WARN] Error processing entry {i}: {e}")
            continue
    
    print(f"[INFO] Processed {len(features_list)} valid entries, {skipped} skipped")
    
    return features_list, labels_list, exoplanet_data.dataset_type

# =========================
# Prepare data for the model
# =========================
def prepare_data_for_training(all_features: List[dict], all_labels: List[int]) -> Tuple[pd.DataFrame, np.ndarray]:
    """
    Converts feature and label lists into the appropriate format for training.
    """
    # Convert to DataFrame
    df = pd.DataFrame(all_features)
    
    # Handle categorical 'dataset' column
    if 'dataset' in df.columns:
        # One-hot encoding for dataset
        dataset_dummies = pd.get_dummies(df['dataset'], prefix='dataset')
        df = pd.concat([df.drop('dataset', axis=1), dataset_dummies], axis=1)
    
    # Fill NaN values with -999 (LightGBM can handle this as missing)
    df = df.fillna(-999)
    
    # Convert labels to array
    y = np.array(all_labels)
    
    print(f"\n[INFO] Final data shape: X={df.shape}, y={y.shape}")
    print(f"[INFO] Class distribution: {np.bincount(y)}")
    print(f"[INFO] Features used: {list(df.columns)}")
    
    return df, y

# =========================
# Model training
# =========================
def train_model(X: pd.DataFrame, y: np.ndarray, validate: bool = True) -> Tuple[lgb.LGBMClassifier, dict]:
    """
    Trains a LightGBM model with optional cross-validation.
    """
    print("\n[INFO] Starting model training...")
    
    # Optimized parameters for exoplanet detection
    params = {
        'objective': 'binary',
        'metric': 'auc',
        'boosting_type': 'gbdt',
        'num_leaves': 31,
        'learning_rate': 0.05,
        'feature_fraction': 0.9,
        'bagging_fraction': 0.8,
        'bagging_freq': 5,
        'verbose': -1,
        'min_child_samples': 20,
        'max_depth': -1,
        'reg_alpha': 0.1,
        'reg_lambda': 0.1,
        'n_estimators': 500,
        'random_state': 42,
        'class_weight': 'balanced'  # Important for unbalanced datasets
    }
    
    if validate:
        # Split into training and validation sets
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Train the model
        model = lgb.LGBMClassifier(**params)
        model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            eval_metric='auc',
            callbacks=[lgb.early_stopping(50), lgb.log_evaluation(100)]
        )
        
        # Evaluate on validation set
        y_pred_proba = model.predict_proba(X_val)[:, 1]
        y_pred = model.predict(X_val)
        
        metrics = {
            'auc': roc_auc_score(y_val, y_pred_proba),
            'avg_precision': average_precision_score(y_val, y_pred_proba),
            'val_size': len(y_val)
        }
        
        print(f"\n[VALIDATION RESULTS]")
        print(f"AUC-ROC: {metrics['auc']:.4f}")
        print(f"Average Precision: {metrics['avg_precision']:.4f}")
        print("\nClassification Report:")
        print(classification_report(y_val, y_pred, target_names=['False Positive', 'Real Planet']))
        
    else:
        # Train with all data
        model = lgb.LGBMClassifier(**params)
        model.fit(X, y)
        metrics = {}
    
    # Feature importance
    feature_importance = pd.DataFrame({
        'feature': X.columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print("\n[TOP 10 MOST IMPORTANT FEATURES]")
    print(feature_importance.head(10).to_string())
    
    return model, metrics

# =========================
# Calculate optimal thresholds
# =========================
def calculate_optimal_thresholds(model: lgb.LGBMClassifier, X: pd.DataFrame, y: np.ndarray) -> dict:
    """
    Calculates optimal thresholds for classification based on desired precision.
    """
    y_pred_proba = model.predict_proba(X)[:, 1]
    
    # Calculate precision-recall curve
    precisions, recalls, thresholds = precision_recall_curve(y, y_pred_proba)
    
    # Find threshold for high precision (few false positives)
    target_precision_high = 0.95
    idx_high = np.where(precisions >= target_precision_high)[0]
    if len(idx_high) > 0:
        tau_high = thresholds[idx_high[0]]
    else:
        tau_high = 0.9
    
    # Find threshold for high recall (few false negatives)
    target_recall_high = 0.95
    idx_low = np.where(recalls >= target_recall_high)[0]
    if len(idx_low) > 0:
        tau_low = thresholds[idx_low[-1]]
    else:
        tau_low = 0.1
    
    return {
        'tau_high': float(tau_high),
        'tau_low': float(tau_low),
        'tau_balanced': 0.5
    }

# =========================
# Main training function
# =========================
def main():
    """
    Main function that orchestrates the entire training process.
    """
    print("="*60)
    print("EXOPLANET DETECTION MODEL TRAINING")
    print("="*60)
    
    # CSV file paths
    csv_paths = {
        'KOI': './static/data/KOI.csv',
        'TOI': './static/data/TOI.csv',
        # 'K2': './static/data/K2.csv'
    }
    
    # Adjust paths if necessary
    for key in csv_paths:
        if not os.path.exists(csv_paths[key]):
            # Try alternative path
            alt_path = f'../static/data/{key}.csv'
            if os.path.exists(alt_path):
                csv_paths[key] = alt_path
            else:
                print(f"[WARN] {csv_paths[key]} not found, will be skipped")
                csv_paths[key] = None
    
    # Load and process all available datasets
    all_features = []
    all_labels = []
    
    for dataset_name, csv_path in csv_paths.items():
        if csv_path and os.path.exists(csv_path):
            features, labels, dataset_type = load_and_process_csv(csv_path)
            if features:
                all_features.extend(features)
                all_labels.extend(labels)
                print(f"[OK] {dataset_name}: {len(features)} samples loaded")
    
    if not all_features:
        print("[ERROR] No data could be loaded from any file")
        return
    
    # Prepare data for training
    X, y = prepare_data_for_training(all_features, all_labels)
    
    # Train model
    model, metrics = train_model(X, y, validate=True)
    
    # Calculate optimal thresholds
    thresholds = calculate_optimal_thresholds(model, X, y)
    print(f"\n[CALCULATED THRESHOLDS]")
    print(f"High threshold (high precision): {thresholds['tau_high']:.4f}")
    print(f"Low threshold (high recall): {thresholds['tau_low']:.4f}")
    
    # Create directory to save the model
    os.makedirs('./model', exist_ok=True)
    
    # Save model
    model_path = './model/model_lgb.pkl'
    joblib.dump(model, model_path)
    print(f"\n[OK] Model saved at: {model_path}")
    
    # Save thresholds
    thresholds_path = './model/thresholds.json'
    with open(thresholds_path, 'w') as f:
        json.dump(thresholds, f, indent=2)
    print(f"[OK] Thresholds saved at: {thresholds_path}")
    
    # Save used columns
    columns_path = './model/columns_used.json'
    with open(columns_path, 'w') as f:
        json.dump(list(X.columns), f, indent=2)
    print(f"[OK] Columns saved at: {columns_path}")
    
    # Save metrics
    if metrics:
        metrics_path = './model/metrics.json'
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        print(f"[OK] Metrics saved at: {metrics_path}")
    
    print("\n" + "="*60)
    print("TRAINING COMPLETED SUCCESSFULLY")
    print("="*60)

if __name__ == "__main__":
    main()
