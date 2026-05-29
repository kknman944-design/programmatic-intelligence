#!/usr/bin/env python3
"""
Train LightGBM model on DV360 historical data.
Output: cpv_predictor.pkl, scaler.pkl
"""

import os
from pathlib import Path

import pandas as pd
import numpy as np
import duckdb
import joblib
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import lightgbm as lgb


def main():
    """Train and save model."""
    
    # Paths
    repo_root = Path(__file__).parent.parent
    db_path = repo_root / 'benchmark.duckdb'
    models_dir = repo_root / 'models'
    models_dir.mkdir(exist_ok=True)
    
    print("[*] Loading data from DuckDB...")
    conn = duckdb.connect(str(db_path))
    
    # Load fact table
    df = conn.execute('SELECT * FROM fact_daily').df()
    conn.close()
    
    if len(df) == 0:
        print("[!] No data found. Run: python etl/ingest.py first.")
        return
    
    print(f"[+] Loaded {len(df)} rows")
    
    # Prepare features
    feature_cols = [
        'impressions', 'measurable_impr', 'viewable_impr', 'clicks',
        'complete_views', 'starts', 'ctr', 'vr', 'cr', 'viewability_pct'
    ]
    
    # Clean data
    df_clean = df[feature_cols + ['cpv', 'cpm']].copy()
    df_clean = df_clean.replace([np.inf, -np.inf], np.nan)
    df_clean = df_clean.dropna()
    
    print(f"[+] Clean data: {len(df_clean)} rows")
    
    if len(df_clean) < 10:
        print("[!] Not enough data for training.")
        return
    
    X = df_clean[feature_cols].values
    y = df_clean['cpv'].values  # Predict CPV
    
    # Normalize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)
    
    print(f"[*] Training LightGBM...")
    
    # Train model
    model = lgb.LGBMRegressor(
        n_estimators=100,
        learning_rate=0.05,
        num_leaves=31,
        random_state=42,
        verbose=-1
    )
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        early_stopping_rounds=10
    )
    
    # Evaluate
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    
    print(f"[+] Model evaluation:")
    print(f"    R²: {r2:.3f}")
    print(f"    MAE: {mae:.3f}")
    print(f"    RMSE: {rmse:.3f}")
    
    # Save model and scaler
    model_path = models_dir / 'cpv_predictor.pkl'
    scaler_path = models_dir / 'scaler.pkl'
    
    joblib.dump(model, model_path)
    joblib.dump(scaler, scaler_path)
    
    print(f"[\u2713] Model saved: {model_path}")
    print(f"[\u2713] Scaler saved: {scaler_path}")


if __name__ == '__main__':
    main()
