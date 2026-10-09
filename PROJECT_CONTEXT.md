# Project Context: Weekly Friday Thai Equity Dashboard
**Last Updated**: 2026-10-04  
**Workspace**: `C:\Users\kitpo\OneDrive\claw_workspace\UOBKH\weekly_friday`  
**Database Source**: `C:\Users\kitpo\OneDrive\claw_workspace\Database_main\set_stocks.duckdb` (~800 MB)  
**Style Reference**: `C:\Users\kitpo\OneDrive\claw_workspace\UOBKH\daily_market_movement`  
**Branding Logo**: `UOBKH_logo.png` (UOB Kay Hian)

---

## 1. Project Goal & Overview

Build an institutional-grade, quantitative web dashboard for **UOB Kay Hian Securities** that captures the complete **weekly picture of Thai equity (SET)**.

In institutional equity research, weekly reviews are published on **Friday morning**, covering the trading week that concludes on **Thursday close** (a 5-day cycle: Friday, Monday, Tuesday, Wednesday, Thursday). The dashboard pre-computes all performance, turnover, and foreign flow metrics across recent weekly cycles and compiles everything into a single, self-contained `index.html` file with embedded base64 branding and JSON datasets.

---

## 2. Core Functional Modules (The 7 Requirements)

| # | Requirement | Implementation & Location in Dashboard |
| :--- | :--- | :--- |
| **1** | **Sector performance ranking YTD** | Tab `Sector Ranking` &rarr; Sub-view `Year-to-Date Ranking (YTD)`: All 27 official SET sectors ranked from #1 to #27 by YTD return relative to 2025 year-end close (`2025-12-30`), with Alpha vs SET Index, visual progress bars, and English/Thai sector names. |
| **2** | **Sector performance ranking last week (Friday–Thursday)** | Tab `Sector Ranking` &rarr; Sub-view `Weekly Ranking (Fri–Thu)`: All 27 sectors ranked by weekly % return from previous Thursday close, with pinned `.SET` benchmark row, week high/low, turnover, and NVDR net flow. |
| **3** | **SET50 - ranking performance** | Tab `SET50 Ranking`: All 50 constituents ranked by weekly % return, with company name, sector, weekly range bar (Low–High), turnover (M฿), % market share, NVDR net flow (M฿), and market cap. Filterable by Gainers/Losers/Search. |
| **4** | **SET100 - ranking performance** | Tab `SET100 Ranking`: All 100 constituents ranked by weekly % return, sortable by any column, with sector dropdown filter and live search. |
| **5** | **SET - top 20 performance** | Tab `SET Top 20 Performance`: Common equities listed on SET (excluding warrants, preferred shares, and DWs). Shows **Top 20 Gainers**, **Top 20 Losers**, and **Top 20 by Turnover**, with liquidity filter (Turnover &ge; 5 M฿ vs All). |
| **6** | **Breakdown of trading value by sector (Friday–Thursday)** | Tab `Turnover & NVDR Flow` &rarr; **Breakdown of Trading Value**: Proportional market share distribution bar + ranked table with turnover in M฿, % market share, active stock count, and average daily turnover. |
| **7** | **NVDR (net buy/sell) by sector (Friday–Thursday)** | Tab `Turnover & NVDR Flow` &rarr; **NVDR Net Buy / Sell**: Ranked table of net foreign flows (M฿), buy vs sell volumes, foreign participation rate %, and top accumulated/distributed stock in each sector. |
| **+** | **Executive Overview Tab** | High-level summary snapshot with KPI cards, Top 7 and Bottom 7 sector movers bar chart, SET50 gainers/losers leaderboards, and market turnover/NVDR flow leaders. |
| **+** | **Historical Week Selector (Sidebar)** | Left sidebar lists the last 12 Friday–Thursday cycles plus current in-progress week (WTD). Clicking any week dynamically re-renders all 7 views instantly with zero page reload. |

---

## 3. Mathematical & Data Methodologies

1. **Weekly Cycle Definition**:
   - Trading days from **Friday morning through Thursday close** (typically 5 trading days: Fri, Mon, Tue, Wed, Thu).
   - **Weekly Return Formula**:
     $$\text{Weekly Return (\%)} = \left(\frac{\text{Close}_{\text{Thursday}}}{\text{Close}_{\text{Prior Thursday}}} - 1\right) \times 100$$
     *Using the prior Thursday close ensures that Friday's full price movement is incorporated into the week.*

2. **Year-to-Date (YTD) Return**:
   - Baseline date: **2025-12-30** (last trading day of 2025).
     $$\text{YTD Return (\%)} = \left(\frac{\text{Close}_{\text{As-Of Date}}}{\text{Close}_{2025-12-30}} - 1\right) \times 100$$
   - **Alpha vs SET**: $\text{Sector YTD Return} - \text{SET Index YTD Return}$.

3. **Sector Turnover & Market Share**:
   - Total value summed across all common stock constituents belonging to each sector during `period_dates`.
     $$\text{Market Share (\%)} = \frac{\text{Sector Value (M฿)}}{\text{Total Market Traded Value (M฿)}} \times 100$$

4. **NVDR Flow**:
   - $\text{NVDR Net} = \text{NVDR Buy} - \text{NVDR Sell}$ (in M฿).
   - Positive indicates net foreign institutional accumulation; negative indicates net foreign distribution.

5. **Common Equity Universe Filtering**:
   To prevent derivative warrants, warrants, and foreign unit boards from skewing equity ranking tables, the universe filters out:
   - Sector/Market Indices: `symbol NOT LIKE '.%'`
   - Warrants: `NOT regexp_matches(symbol, '-W[0-9]*$')`
   - Preferred Shares: `symbol NOT LIKE '%-P'`
   - Foreign Shares: `symbol NOT LIKE '%-F'`
   - Separate NVDR Tickers: `symbol NOT LIKE '%-R'`
   - Derivative Warrants (DW): `NOT regexp_matches(symbol, '[0-9]{2}[CP][0-9]{4}')`

6. **Suspended / Un-Traded Constituent Fallback**:
   - If a constituent of SET50 or SET100 is suspended (e.g. on `SP` like THCOM) or has no trades on `end_dt`, the builder queries `stock_metadata` and the latest known closing price on or before `end_dt`. This guarantees that SET50 always displays 50 constituents and SET100 always displays 100 constituents without dropping rows.

---

## 4. Sector Index & Metadata Mapping (27 Sectors)

| Symbol | English Name | Thai Name | Industry Group |
| :--- | :--- | :--- | :--- |
| `.AGRI` | Agribusiness | ธุรกิจการเกษตร | Agro & Food Industry |
| `.FOOD` | Food & Beverage | อาหารและเครื่องดื่ม | Agro & Food Industry |
| `.FASHION` | Fashion | แฟชั่น | Consumer Products |
| `.HOME` | Home & Office Products | ของใช้ในครัวเรือนและสำนักงาน | Consumer Products |
| `.PERSON` | Personal Products & Pharmaceuticals | ของใช้ส่วนตัวและเวชภัณฑ์ | Consumer Products |
| `.BANK` | Banking | ธนาคาร | Financials |
| `.FIN` | Finance & Securities | เงินทุนและหลักทรัพย์ | Financials |
| `.INSUR` | Insurance | ประกันภัยและประกันชีวิต | Financials |
| `.AUTO` | Automotive | ยานยนต์ | Industrials |
| `.CONMAT` | Construction Materials | วัสดุก่อสร้าง | Property & Construction |
| `.CONS` | Construction Services | บริการรับเหมาก่อสร้าง | Property & Construction |
| `.PAPER` | Paper & Printing Materials | กระดาษและวัสดุการพิมพ์ | Industrials |
| `.PKG` | Packaging | บรรจุภัณฑ์ | Industrials |
| `.STEEL` | Steel and Metal Products | เหล็กและผลิตภัณฑ์โลหะ | Industrials |
| `.PETRO` | Petrochemicals & Chemicals | ปิโตรเคมีและเคมีภัณฑ์ | Industrials |
| `.PROP` | Property Development | พัฒนาอสังหาริมทรัพย์ | Property & Construction |
| `.PF&REIT` | Property Fund & REITs | กองทุนรวมอสังหาริมทรัพย์และ REITs | Property & Construction |
| `.COMM` | Commerce | พาณิชย์ | Services |
| `.HELTH` | Health Care Services | บริการสุขภาพ | Services |
| `.MEDIA` | Media & Publishing | สื่อและสิ่งพิมพ์ | Services |
| `.PROF` | Professional Services | บริการเฉพาะกิจ | Services |
| `.TOURISM` | Tourism & Leisure | การท่องเที่ยวและสันทนาการ | Services |
| `.TRANS` | Transportation & Logistics | ขนส่งและโลจิสติกส์ | Services |
| `.ETRON` | Electronic Components | ชิ้นส่วนอิเล็กทรอนิกส์ | Technology |
| `.ICT` | Information & Communication Technology | เทคโนโลยีสารสนเทศและการสื่อสาร | Technology |
| `.ENERG` | Energy & Utilities | พลังงานและสาธารณูปโภค | Resources |
| `.IMM` | Industrial Materials & Machinery | วัสดุอุตสาหกรรมและเครื่องจักร | Industrials |

*Note: `.MINE` (Mining) is dormant on SET with no active listed common stocks.*

---

## 5. File Structure & Components

```
C:\Users\kitpo\OneDrive\claw_workspace\UOBKH\weekly_friday\
├── build_weekly_dashboard.py   # Primary Python builder (DuckDB extract -> JSON -> index.html)
├── template.html               # Frontend HTML/CSS/JS template with institutional UI
├── index.html                  # Standalone output dashboard (self-contained, 1.68 MB)
├── test_dashboard.py           # Verification test suite (asserts all 7 modules across all weeks)
├── instruction.txt             # Original user prompt specifications
├── UOBKH_logo.png              # Official UOB Kay Hian logo
├── README.md                   # User guide, parameter reference & run documentation
└── PROJECT_CONTEXT.md          # This context file (architecture, decisions & reference)
```

---

## 6. Design System & Palette

- **Dark Grey (`#3F4C54`)**: Table headers, active tab pill, primary text ink.
- **Vino (`#760E3A`)**: Accent headers, active sidebar week indicator, negative impact highlights.
- **Red (`#C33B32`)**: Price decliners, net foreign selling, negative performance.
- **Gold (`#A89983`)**: Benchmark highlight bars, secondary accent elements.
- **Steel Grey (`#DBE0E4`)**: Neutral borders, range bar tracks, unchanged breadth.
- **Up Green (`#1E7A5F`)**: Price gainers, net foreign buying, positive performance.
- **Light Background (`#FFFFFF` & `#F5F7F8`)**: Crisp institutional readability.
- **Typography**: `Inter` / `Segoe UI` for UI; `SF Mono` / `Cascadia Mono` for tabular numerics.

---

## 7. Execution Quick Reference

### Standard Build (Default: 12 Weeks)
```powershell
cd C:\Users\kitpo\OneDrive\claw_workspace\UOBKH\weekly_friday
python build_weekly_dashboard.py
```

### CLI Parameters
- `--db <path>`: Path to DuckDB file (default: `C:\Users\kitpo\OneDrive\claw_workspace\Database_main\set_stocks.duckdb`).
- `--weeks <int>`: Number of Friday–Thursday weekly cycles to compile (default: `12`).
- `--out <path>`: Output HTML destination (default: `index.html`).

### View Dashboard in Browser
```powershell
Start-Process index.html
```

### Run Integrity Test Suite
```powershell
python test_dashboard.py
```

---

## 8. Notes for Future Maintenance & Sessions

1. **Daily Scheduler Interaction**:
   - `Database_main\schedule_daily_update.py` runs every weekday morning at 07:00 AM to fetch official SETSMART data for the prior trading day.
   - When a new Thursday is completed, running `build_weekly_dashboard.py` will automatically detect the new closed week and make it the default active period.

2. **Standalone Integrity**:
   - `index.html` embeds the logo and full data payload. It contains zero external CDN scripts, stylesheets, or web fonts. It operates completely offline and can be pushed to GitHub Pages or emailed directly as a self-contained report.
