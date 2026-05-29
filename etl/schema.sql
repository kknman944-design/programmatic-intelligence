-- Canonical Fact Table: DV360 YouTube + Non-YouTube
-- Normalized schema for benchmark reporting

CREATE TABLE IF NOT EXISTS fact_daily (
  -- Date/Period
  date_start DATE,
  date_end DATE,
  channel TEXT,  -- 'YouTube' or 'Non-YouTube'
  period TEXT,   -- YYYY/MM or YYYY/QQ
  
  -- Org Hierarchy
  advertiser_id BIGINT,
  advertiser TEXT,
  partner_id BIGINT,
  partner TEXT,
  io_id BIGINT,
  io_name TEXT,
  li_id BIGINT,
  li_name TEXT,
  
  -- Creative & Placement
  creative_id BIGINT,
  creative_name TEXT,
  placement_position TEXT,
  
  -- Dimensions
  device_type TEXT,
  currency TEXT,
  
  -- Core Metrics
  impressions BIGINT,
  measurable_impr BIGINT,
  viewable_impr BIGINT,
  clicks BIGINT,
  complete_views BIGINT,
  starts BIGINT,
  cost DECIMAL(15, 2),
  
  -- Calculated KPIs
  cpm DECIMAL(10, 2),
  vcpm DECIMAL(10, 2),
  cpv DECIMAL(10, 2),
  cpc DECIMAL(10, 2),
  ctr DECIMAL(5, 4),
  vr DECIMAL(5, 4),
  cr DECIMAL(5, 4),
  viewability_pct DECIMAL(5, 2),
  
  -- Audit
  source_report TEXT,
  source_row_id TEXT,
  loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  PRIMARY KEY (date_start, channel, io_id, li_id, creative_id, device_type)
);

-- Dimension Tables (for future optimization)

CREATE TABLE IF NOT EXISTS dim_advertiser (
  advertiser_id BIGINT PRIMARY KEY,
  advertiser TEXT,
  partner_id BIGINT,
  partner TEXT
);

CREATE TABLE IF NOT EXISTS dim_creative (
  creative_id BIGINT PRIMARY KEY,
  creative_name TEXT,
  placement_position TEXT
);

CREATE TABLE IF NOT EXISTS dim_device (
  device_type TEXT PRIMARY KEY
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_fact_date ON fact_daily(date_start, date_end);
CREATE INDEX IF NOT EXISTS idx_fact_channel ON fact_daily(channel);
CREATE INDEX IF NOT EXISTS idx_fact_advertiser ON fact_daily(advertiser_id);
CREATE INDEX IF NOT EXISTS idx_fact_io ON fact_daily(io_id);
CREATE INDEX IF NOT EXISTS idx_fact_li ON fact_daily(li_id);
CREATE INDEX IF NOT EXISTS idx_fact_creative ON fact_daily(creative_id);
