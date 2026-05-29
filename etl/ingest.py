#!/usr/bin/env python3
"""
DV360 Data Ingestion Pipeline
Normalizes YouTube and Non-YouTube CSVs into canonical DuckDB fact table.
"""

import os
import sys
import hashlib
from datetime import datetime
from pathlib import Path

import pandas as pd
import duckdb


def get_row_hash(row_dict: dict) -> str:
    """Generate unique hash for row (for deduplication)."""
    row_str = '|'.join(str(v) for v in sorted(row_dict.values()))
    return hashlib.md5(row_str.encode()).hexdigest()


def parse_youtube(df: pd.DataFrame) -> pd.DataFrame:
    """
    Parse YouTube export (01_YT_Raw_DV360.csv).
    Maps DV360 columns to canonical schema.
    """
    df_out = pd.DataFrame()
    
    # Basic mappings
    df_out['date_start'] = pd.to_datetime(df['Start Date'])
    df_out['date_end'] = pd.to_datetime(df['End Date'])
    df_out['channel'] = 'YouTube'
    df_out['period'] = df['Month']
    
    df_out['advertiser_id'] = df['Advertiser ID'].astype('int64')
    df_out['advertiser'] = df['Advertiser']
    df_out['partner_id'] = df['Partner ID'].astype('int64')
    df_out['partner'] = df['Partner']
    df_out['io_id'] = df['Insertion Order ID'].astype('int64')
    df_out['io_name'] = df['Insertion Order']
    df_out['li_id'] = df['Line Item ID'].astype('int64')
    df_out['li_name'] = df['Line Item']
    
    # Creative (YouTube may not have explicit Creative ID/Name)
    df_out['creative_id'] = 0  # Placeholder for YouTube
    df_out['creative_name'] = 'YouTube'  # Placeholder
    df_out['placement_position'] = None
    
    df_out['device_type'] = df['Device Type']
    df_out['currency'] = df['Advertiser Currency']
    
    # Metrics
    df_out['impressions'] = df['Impressions'].astype('int64')
    df_out['measurable_impr'] = df['Active View: Measurable Impressions'].astype('int64')
    df_out['viewable_impr'] = df['Active View: Viewable Impressions'].astype('int64')
    df_out['clicks'] = df['Clicks'].astype('int64')
    df_out['complete_views'] = df['Complete Views (Video)'].astype('int64')
    df_out['starts'] = df['Complete Views (Video)'].astype('int64')  # Proxy for YouTube
    
    # Cost (remove commas if present)
    df_out['cost'] = df['Media Cost (Advertiser Currency)'].astype(str).str.replace(',', '').astype('float')
    
    # Calculate KPIs
    df_out['cpm'] = (df_out['cost'] / (df_out['impressions'] / 1000.0)).round(2)
    df_out['vcpm'] = (df_out['cost'] / (df_out['viewable_impr'] / 1000.0)).round(2)
    df_out['cpv'] = (df_out['cost'] / df_out['complete_views']).round(2)
    df_out['cpc'] = (df_out['cost'] / df_out['clicks']).round(2)
    df_out['ctr'] = (df_out['clicks'] / df_out['impressions']).round(4)
    df_out['vr'] = (df_out['complete_views'] / df_out['impressions']).round(4)
    df_out['cr'] = (df_out['complete_views'] / df_out['starts']).round(4)
    df_out['viewability_pct'] = (df_out['viewable_impr'] / df_out['measurable_impr'] * 100).round(2)
    
    df_out['source_report'] = '01_YT_Raw_DV360'
    df_out['source_row_id'] = df_out.apply(lambda row: get_row_hash(row.to_dict()), axis=1)
    df_out['loaded_at'] = datetime.now()
    
    # Fill NaN in calculated fields with 0
    df_out = df_out.fillna(0)
    
    return df_out


def parse_nonyt(df: pd.DataFrame) -> pd.DataFrame:
    """
    Parse Non-YouTube export (02_NonYT_Raw_DV360.csv).
    Maps DV360 columns to canonical schema.
    """
    df_out = pd.DataFrame()
    
    # Basic mappings
    df_out['date_start'] = pd.to_datetime(df['Start Date'])
    df_out['date_end'] = pd.to_datetime(df['End Date'])
    df_out['channel'] = 'Non-YouTube'
    df_out['period'] = df['Month']
    
    df_out['advertiser_id'] = df['Advertiser ID'].astype('int64')
    df_out['advertiser'] = df['Advertiser']
    df_out['partner_id'] = df['Partner ID'].astype('int64')
    df_out['partner'] = df['Partner']
    df_out['io_id'] = df['Insertion Order ID'].astype('int64')
    df_out['io_name'] = df['Insertion Order']
    df_out['li_id'] = df['Line Item ID'].astype('int64')
    df_out['li_name'] = df['Line Item']
    
    df_out['creative_id'] = df['Creative ID'].astype('int64')
    df_out['creative_name'] = df['Creative']
    df_out['placement_position'] = df['Position in Content']
    
    df_out['device_type'] = df['Device Type']
    df_out['currency'] = df['Advertiser Currency']
    
    # Metrics
    df_out['impressions'] = df['Impressions'].astype('int64')
    df_out['measurable_impr'] = df['Active View: Measurable Impressions'].astype('int64')
    df_out['viewable_impr'] = df['Active View: Viewable Impressions'].astype('int64')
    df_out['clicks'] = df['Clicks'].astype('int64')
    df_out['complete_views'] = df['Complete Views (Video)'].astype('int64')
    df_out['starts'] = df['Starts (Video)'].astype('int64')
    
    # Cost (remove commas if present)
    df_out['cost'] = df['Media Cost (Advertiser Currency)'].astype(str).str.replace(',', '').astype('float')
    
    # Calculate KPIs
    df_out['cpm'] = (df_out['cost'] / (df_out['impressions'] / 1000.0)).round(2)
    df_out['vcpm'] = (df_out['cost'] / (df_out['viewable_impr'] / 1000.0)).round(2)
    df_out['cpv'] = (df_out['cost'] / df_out['complete_views']).round(2)
    df_out['cpc'] = (df_out['cost'] / df_out['clicks']).round(2)
    df_out['ctr'] = (df_out['clicks'] / df_out['impressions']).round(4)
    df_out['vr'] = (df_out['complete_views'] / df_out['impressions']).round(4)
    df_out['cr'] = (df_out['complete_views'] / df_out['starts']).round(4)
    df_out['viewability_pct'] = (df_out['viewable_impr'] / df_out['measurable_impr'] * 100).round(2)
    
    df_out['source_report'] = '02_NonYT_Raw_DV360'
    df_out['source_row_id'] = df_out.apply(lambda row: get_row_hash(row.to_dict()), axis=1)
    df_out['loaded_at'] = datetime.now()
    
    # Fill NaN in calculated fields with 0
    df_out = df_out.fillna(0)
    
    return df_out


def main():
    """
    Main ETL pipeline.
    Usage: python etl/ingest.py --youtube <path> --nonyt <path>
    """
    # Paths
    etl_dir = Path(__file__).parent
    repo_root = etl_dir.parent
    data_dir = repo_root / 'data'
    db_path = repo_root / 'benchmark.duckdb'
    
    # Ensure data dir exists
    data_dir.mkdir(exist_ok=True)
    
    # Initialize DuckDB
    conn = duckdb.connect(str(db_path))
    
    # Create schema
    schema_sql = (etl_dir / 'schema.sql').read_text()
    conn.execute(schema_sql)
    
    # Load YouTube data if available
    yt_file = data_dir / '01_YT_Raw_DV360.csv'
    if yt_file.exists():
        print(f"[*] Loading YouTube: {yt_file}")
        df_yt = pd.read_csv(yt_file)
        df_yt_norm = parse_youtube(df_yt)
        print(f"    Parsed {len(df_yt_norm)} rows")
        conn.execute('DELETE FROM fact_daily WHERE source_report = "01_YT_Raw_DV360"')
        conn.execute('INSERT INTO fact_daily SELECT * FROM df_yt_norm')
        print(f"    Inserted into fact_daily")
    else:
        print(f"[!] YouTube file not found: {yt_file}")
    
    # Load Non-YouTube data if available
    nonyt_file = data_dir / '02_NonYT_Raw_DV360.csv'
    if nonyt_file.exists():
        print(f"[*] Loading Non-YouTube: {nonyt_file}")
        df_nonyt = pd.read_csv(nonyt_file)
        df_nonyt_norm = parse_nonyt(df_nonyt)
        print(f"    Parsed {len(df_nonyt_norm)} rows")
        conn.execute('DELETE FROM fact_daily WHERE source_report = "02_NonYT_Raw_DV360"')
        conn.execute('INSERT INTO fact_daily SELECT * FROM df_nonyt_norm')
        print(f"    Inserted into fact_daily")
    else:
        print(f"[!] Non-YouTube file not found: {nonyt_file}")
    
    # Query summary
    summary = conn.execute(
        'SELECT channel, COUNT(*) as row_count, SUM(cost) as total_cost FROM fact_daily GROUP BY channel'
    ).df()
    print(f"\n[+] Summary:")
    print(summary)
    
    conn.close()
    print(f"[✓] ETL complete. Database: {db_path}")


if __name__ == '__main__':
    main()
