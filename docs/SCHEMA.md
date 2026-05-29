# Data Schema & Mapping

## YouTube vs Non-YouTube Reconciliation

### YouTube (01_YT_Raw_DV360.csv)
**Source columns** → **Canonical columns**
- `Advertiser` → `advertiser`
- `Advertiser ID` → `advertiser_id`
- `Insertion Order` → `io_name`
- `Insertion Order ID` → `io_id`
- `Line Item` → `li_name`
- `Line Item ID` → `li_id`
- `Device Type` → `device_type` (Connected TV, Desktop, Smart Phone, Tablet)
- `Month` → `period` (YYYY/MM)
- `Start Date` → `date_start`
- `End Date` → `date_end`
- `Active View: Measurable Impressions` → `measurable_impr`
- `Active View: Viewable Impressions` → `viewable_impr`
- `Impressions` → `impressions`
- `Clicks` → `clicks`
- `Complete Views (Video)` → `complete_views`
- `TrueView: Views` → `trueview_views` (reference only)
- `Media Cost (Advertiser Currency)` → `cost`
- `Advertiser Currency` → `currency`
- `Partner` → `partner`
- `Partner ID` → `partner_id`
- **No quartile metrics** (removed per spec)

### Non-YouTube (02_NonYT_Raw_DV360.csv)
**Source columns** → **Canonical columns**
- All YouTube mappings above
- `Creative` → `creative_name`
- `Creative ID` → `creative_id`
- `Position in Content` → `placement_position` (In-Article, Interstitial, etc.)
- `Starts (Video)` → `starts` (for video completions)
- **No quartile metrics** (removed per spec)

## Canonical Fact Table (DuckDB)

```sql
CREATE TABLE fact_daily (
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
  placement_position TEXT,  -- In-Article, Interstitial, etc.
  
  -- Dimensions
  device_type TEXT,  -- Connected TV, Desktop, Smart Phone, Tablet
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
  cpm DECIMAL(10, 2),        -- Cost / Impressions * 1000
  vcpm DECIMAL(10, 2),       -- Cost / Viewable Impr * 1000
  cpv DECIMAL(10, 2),        -- Cost / Complete Views
  cpc DECIMAL(10, 2),        -- Cost / Clicks
  ctr DECIMAL(5, 4),         -- Clicks / Impressions
  vr DECIMAL(5, 4),          -- Complete Views / Impressions
  cr DECIMAL(5, 4),          -- Complete Views / Starts (if starts > 0)
  viewability_pct DECIMAL(5, 2),  -- Viewable / Measurable * 100
  
  -- Audit
  source_report TEXT,  -- '01_YT_Raw_DV360' or '02_NonYT_Raw_DV360'
  source_row_id TEXT,  -- Original row hash for dedupe
  loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  PRIMARY KEY (date_start, channel, io_id, li_id, creative_id, device_type)
);
```

## Extensibility

### Adding New Dimensions
1. Add column to `fact_daily` table
2. Update `ingest.py` mapping in `parse_youtube()` and `parse_nonyt()`
3. Update dashboard filters in `docs/js/app.js`
4. No schema migration needed (DuckDB is flexible)

### Example: Add "Region" or "Country"
```sql
ALTER TABLE fact_daily ADD COLUMN country TEXT;
ALTER TABLE fact_daily ADD COLUMN region TEXT;
```

Then update ETL to extract & populate from DV360 exports.

## Notes
- **Quartile views removed** per spec (First-Quartile, Midpoint, Third-Quartile are not tracked)
- **Starts metric** (Non-YT) used to calculate Completion Rate
- **Currency handling**: Store both cost and currency; convert to USD in dashboard if needed
- **Date aggregation**: YouTube = Month-level; Non-YT = Quarter-level → normalize to month/quarter in dashboard
