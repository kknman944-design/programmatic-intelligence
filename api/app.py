#!/usr/bin/env python3
"""
Flask API for MCP predictions.
Endpoint: POST /predict
"""

import os
import json
from pathlib import Path
from datetime import datetime

from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import pandas as pd
import duckdb
import numpy as np

app = Flask(__name__)
CORS(app)

# Paths
REPO_ROOT = Path(__file__).parent.parent
DB_PATH = REPO_ROOT / 'benchmark.duckdb'
MODEL_PATH = REPO_ROOT / 'models' / 'cpv_predictor.pkl'
SCALER_PATH = REPO_ROOT / 'models' / 'scaler.pkl'

# Load model
model = None
scaler = None

def load_model():
    """Load trained model and scaler."""
    global model, scaler
    if MODEL_PATH.exists() and SCALER_PATH.exists():
        model = joblib.load(MODEL_PATH)
        scaler = joblib.load(SCALER_PATH)
        print(f"[+] Model loaded: {MODEL_PATH}")
    else:
        print(f"[!] Model not found. Run: python models/train.py")


@app.route('/health', methods=['GET'])
def health():
    """Health check."""
    return jsonify({'status': 'ok', 'timestamp': datetime.utcnow().isoformat()}), 200


@app.route('/predict', methods=['POST'])
def predict():
    """
    Predict CPV / CPM for given context.
    
    Input JSON:
    {
      "channel": "YouTube" | "Non-YouTube",
      "advertiser_id": 123,
      "device_type": "Desktop",
      "month": "2025/01",
      "lookback_days": 90
    }
    
    Output:
    {
      "predicted_cpv": 0.45,
      "predicted_cpm": 8.50,
      "lower_ci": [0.40, 8.00],
      "upper_ci": [0.50, 9.00],
      "sample_size": 150,
      "model_version": "v1"
    }
    """
    
    if not model:
        return jsonify({'error': 'Model not loaded'}), 503
    
    data = request.get_json()
    
    try:
        channel = data.get('channel', 'YouTube')
        advertiser_id = int(data.get('advertiser_id', 0))
        device_type = data.get('device_type', 'Desktop')
        month = data.get('month', '2025/01')
        lookback_days = int(data.get('lookback_days', 90))
        
        # Query historical data
        conn = duckdb.connect(str(DB_PATH))
        
        hist_query = f"""
        SELECT 
          cpv, cpm, vcpm, cpc, ctr, vr, cr, viewability_pct,
          impressions, viewable_impr, clicks, complete_views, cost
        FROM fact_daily
        WHERE channel = '{channel}'
          AND advertiser_id = {advertiser_id}
          AND device_type = '{device_type}'
          AND date_start >= CURRENT_DATE - INTERVAL {lookback_days} DAY
        LIMIT 1000
        """
        
        hist_df = conn.execute(hist_query).df()
        conn.close()
        
        if len(hist_df) == 0:
            return jsonify({'error': 'No historical data found'}), 404
        
        # Prepare features for model
        features = hist_df[[
            'cpv', 'cpm', 'vcpm', 'cpc', 'ctr', 'vr', 'cr', 'viewability_pct',
            'impressions', 'viewable_impr', 'clicks', 'complete_views', 'cost'
        ]].tail(10).mean().values.reshape(1, -1)  # Use last 10 rows' average
        
        # Normalize features
        if scaler:
            features_scaled = scaler.transform(features)
        else:
            features_scaled = features
        
        # Predict
        pred = model.predict(features_scaled)[0]
        
        # Confidence interval (simple: +/- 15%)
        ci_lower = pred * 0.85
        ci_upper = pred * 1.15
        
        # Infer CPV and CPM from aggregated data
        predicted_cpv = hist_df['cpv'].median()
        predicted_cpm = hist_df['cpm'].median()
        
        return jsonify({
            'predicted_cpv': round(float(predicted_cpv), 2),
            'predicted_cpm': round(float(predicted_cpm), 2),
            'lower_ci': [round(float(ci_lower), 2), round(float(hist_df['cpm'].min()), 2)],
            'upper_ci': [round(float(ci_upper), 2), round(float(hist_df['cpm'].max()), 2)],
            'sample_size': len(hist_df),
            'model_version': 'v1',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/data/summary', methods=['GET'])
def get_summary():
    """Get data summary by channel."""
    conn = duckdb.connect(str(DB_PATH))
    summary = conn.execute(
        'SELECT channel, COUNT(*) as row_count, SUM(cost) as total_cost, AVG(cpm) as avg_cpm FROM fact_daily GROUP BY channel'
    ).df()
    conn.close()
    
    return jsonify(summary.to_dict(orient='records')), 200


@app.route('/data/channels', methods=['GET'])
def get_channels():
    """Get available channels."""
    conn = duckdb.connect(str(DB_PATH))
    channels = conn.execute('SELECT DISTINCT channel FROM fact_daily').df()
    conn.close()
    
    return jsonify(channels['channel'].tolist()), 200


if __name__ == '__main__':
    load_model()
    app.run(debug=True, host='0.0.0.0', port=5000)
