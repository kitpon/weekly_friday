# Weekly Friday Thai Equity Dashboard
**UOB Kay Hian Securities**

A quantitative, institutional-grade weekly market review dashboard for Thai equities (SET). It provides an in-depth picture of the trading week running from **Friday open through Thursday close**, including sector performance (Weekly & YTD), benchmark comparisons, constituent movers (SET50, SET100, SET Top 20), turnover distribution, and foreign NVDR flows.

The dashboard compiles everything into a single, standalone `index.html` file with the **UOBKH logo** and complete JSON dataset embedded. It can be opened directly in any browser or deployed onto GitHub Pages with zero external server dependencies.

---

## How to Run the Script

### Quick Start (Default Run)
Open PowerShell and run:

```powershell
cd C:\Users\kitpo\OneDrive\claw_workspace\UOBKH\weekly_friday
python build_weekly_dashboard.py
```

This will automatically:
1. Connect to the default database: `C:\Users\kitpo\OneDrive\claw_workspace\Database_main\set_stocks.duckdb`.
2. Extract the last **12 trading weeks** (Friday–Thursday cycles) plus current WTD.
3. Compute all 7 required modules (Sector Weekly & YTD rankings, SET50, SET100, SET Top 20, Sector Turnover breakdown, NVDR flow).
4. Embed the `UOBKH_logo.png` (base64) and dataset into `index.html`.

---

## Command-Line Parameters

The builder script accepts three optional arguments:

| Parameter | Type | Default Value | Description |
| :--- | :--- | :--- | :--- |
| `--db` | String (Path) | `C:\Users\kitpo\OneDrive\claw_workspace\Database_main\set_stocks.duckdb` | Path to the DuckDB historical database file. |
| `--weeks` | Integer | `12` | Number of historical Friday–Thursday weekly cycles to include in the sidebar. |
| `--out` | String (Path) | `index.html` (in current folder) | Target file path for the output HTML dashboard. |

### Usage Examples

#### 1. Include More or Fewer Weeks
To build with 20 historical weeks instead of the default 12:
```powershell
python build_weekly_dashboard.py --weeks 20
```

#### 2. Specify a Custom Output Path
To output to a specific report file or directory:
```powershell
python build_weekly_dashboard.py --out "weekly_report_20261001.html"
```

#### 3. Use an Alternative Database File
If using a backup or office copy of DuckDB:
```powershell
python build_weekly_dashboard.py --db "C:\Users\kitpo\OneDrive\claw_workspace\Database_main\set_stocks.duckdb" --weeks 8 --out "index.html"
```

---

## How to View the Dashboard

Once generated, double-click `index.html` or launch it directly in your browser:

```powershell
Start-Process index.html
```

You can also run the automated verification test at any time:
```powershell
python test_dashboard.py
```

---

## Dashboard Features & Modules

### 1. Executive Overview (Snapshot)
- **SET Index KPI Strip**: SET Level, Weekly Change (pts & %), YTD Return (%), Total Weekly Turnover (Bn THB & daily average), Total Foreign NVDR Net Flow (M THB), and Market Breadth (Advancing, Declining, Unchanged common stocks).
- **Sector Leaders**: Proportional bar chart comparing Top 7 and Bottom 7 sector performers of the week.
- **SET50 Gainers & Losers**: Top 5 weekly advancers and decliners in the blue-chip index.
- **Turnover & Foreign Accumulation Leaders**: Largest turnover sector and top foreign net inflow sector.

### 2. Sector Performance Ranking (Weekly & YTD)
- **Weekly Ranking (Friday–Thursday)**:
  - All 27 official SET sectors ranked from #1 to #27 by weekly % return.
  - Baseline: Thursday close of previous week (capturing the full 5-day cycle: Fri, Mon, Tue, Wed, Thu).
  - Pinned SET Index benchmark row for immediate relative performance evaluation.
  - Columns: Sector Symbol, English Name, Thai Name, Industry Group, Prior Close, Week Close, Weekly Chg, Weekly %Chg (with color-coded visual mini-bar), Weekly Turnover (M฿), Market Share (%), and NVDR Net Flow (M฿).
- **Year-to-Date Ranking (YTD)**:
  - All 27 sectors ranked by return relative to 2025 year-end close (`2025-12-30`).
  - Columns: Sector Symbol, English Name, Thai Name, Industry Group, 2025 Close, Current Close, YTD %Chg, Alpha vs SET Index (+/- spread), and Weekly %Chg.
- **Comprehensive Matrix**:
  - Integrated view combining Weekly Return, YTD Return, Alpha vs SET, Trading Value, Market Share %, NVDR Net Flow, and Foreign Participation Rate.

### 3. Sector Turnover Breakdown & NVDR Flow
- **Breakdown of Trading Value by Sector (Friday–Thursday)**:
  - Visual **Market Share Distribution Bar** showcasing relative turnover share across top sectors.
  - Table ranked by weekly turnover (M THB), % share of market, proportional graphical bar, average daily turnover, active stock count, and weekly % change.
- **NVDR (Net Buy / Sell) by Sector (Friday–Thursday)**:
  - Summary cards for Total Net Inflow Sectors vs Total Net Outflow Sectors.
  - Table ranked by NVDR Net Flow (M THB), displaying NVDR Buy, NVDR Sell, NVDR Net, Top Inflow Stock, and Top Outflow Stock for each sector.

### 4. SET50 Ranking Performance
- All 50 constituents of the SET50 index ranked by weekly % performance.
- Interactive filter pills: **All (50)** | **Gainers** | **Losers**.
- Instant search input (by symbol, company name, or sector).
- Interactive columns: Symbol, Company Name, Sector, Prior Close, Week Close, Weekly %Chg, YTD %Chg, Weekly Intraday Range Bar (Low–High), Turnover (M฿), % Market Share, NVDR Net (M฿), and Market Cap (Bn฿).

### 5. SET100 Ranking Performance
- All 100 constituents of the SET100 index ranked by weekly % performance.
- Interactive filter pills: **All (100)** | **Gainers** | **Losers** + **Sector Dropdown Filter**.
- Instant search input.
- Interactive sortable columns matching SET50.

### 6. SET Top 20 Performance
- Evaluates all active common equities listed on SET (excluding warrants, preferred shares, and derivative warrants).
- Side-by-side comparative panels:
  1. **Top 20 Gainers** (Weekly %)
  2. **Top 20 Losers** (Weekly %)
  3. **Top 20 by Turnover** (Weekly Trading Value)
- Liquidity filter toggle: **Liquid Names Only (Turnover ≥ 5 M฿)** vs **All Traded Common Stocks**.

### 7. Historical Week Switching
- Left sidebar lists the last 12 trading weeks (Friday–Thursday cycles) plus the current in-progress week (WTD).
- Each week button displays the date range, status badge (`Closed` or `In Progress`), SET Index return, and an advancing/declining breadth bar.
- Clicking any week instantly re-renders the entire dashboard for that historical period with zero page reload.

---

## Design System & Theme

Referenced directly from `UOBKH/daily_market_movement`:
- **Dark Grey**: `#3F4C54` (Headers, active tabs, primary ink)
- **Vino**: `#760E3A` (Accent headers, active sidebar borders, negative impact)
- **Red**: `#C33B32` (Decliners, negative return, net outflow)
- **Gold**: `#A89983` (Secondary accents, benchmark highlights)
- **Steel Grey**: `#DBE0E4` (Borders, neutral tracks, unch breadth)
- **Up Green**: `#1E7A5F` (Advancers, positive return, net inflow)
- **Backgrounds**: `#FFFFFF` and `#F5F7F8` (Crisp light institutional theme)
- **Branding**: Official UOBKH logo embedded on top left header.

---

## Methodology & Calculation Rules

| Metric | Formula / Rule |
| :--- | :--- |
| **Weekly Period** | Trading days from Friday open through Thursday close (normally 5 trading days). |
| **Weekly Return** | `((Close_Thu / Close_Prior_Thu) - 1) * 100`. Prior Thursday close ensures Friday's full move is captured. |
| **YTD Return** | `((Close_As_Of / Close_2025_12_30) - 1) * 100`. |
| **Alpha vs SET** | `Sector_YTD_Return - SET_Index_YTD_Return`. |
| **Sector Turnover** | Sum of `daily_stocks.value` across all common stock constituents during `period_dates`. |
| **NVDR Net** | Sum of `daily_stocks.nvdr_net` (or `nvdr_buy - nvdr_sell`) during `period_dates`. |
| **Common Equity Universe** | Filtered to exclude market indices (`.%`), warrants (`-W*`), preferred shares (`-P`), foreign shares (`-F`), and derivative warrants (`[0-9]{2}[CP][0-9]{4}`). |

---

## Project Structure

```
C:\Users\kitpo\OneDrive\claw_workspace\UOBKH\weekly_friday\
├── build_weekly_dashboard.py   # Python extraction, processing & build script
├── template.html               # Modular HTML/CSS/JS frontend template
├── index.html                  # Generated standalone dashboard (data + logo embedded)
├── test_dashboard.py           # Integrity test & data verification suite
├── instruction.txt             # Original user requirements
├── UOBKH_logo.png              # Official UOB Kay Hian logo
└── README.md                   # This documentation
```
