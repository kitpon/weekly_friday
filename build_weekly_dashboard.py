"""
Weekly Friday Equity Dashboard Builder
UOB Kay Hian Securities

Extracts weekly Thai equity market data from set_stocks.duckdb,
computes weekly (Friday-Thursday) and YTD performance rankings,
SET50/SET100 rankings, SET top 20 movers, sector turnover breakdown,
and sector NVDR flow. Emits a self-contained index.html with embedded
UOBKH logo and JSON dataset.

Usage:
    python build_weekly_dashboard.py
    python build_weekly_dashboard.py --weeks 12 --out index.html
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import os
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

import duckdb

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = r"C:\Users\kitpo\OneDrive\claw_workspace\Database_main\set_stocks.duckdb"
LOGO_PATH = os.path.join(HERE, "UOBKH_logo.png")
TEMPLATE_PATH = os.path.join(HERE, "template.html")
OUTPUT_PATH = os.path.join(HERE, "index.html")

MAX_WEEKS = 12
MB = 1_000_000.0

# -----------------------------------------------------------------------------
# Sector Definitions & Metadata
# -----------------------------------------------------------------------------

SECTOR_MAP = {
    '.AGRI': {'en': 'Agribusiness', 'th': 'ธุรกิจการเกษตร', 'ind': 'Agro & Food Industry'},
    '.FOOD': {'en': 'Food & Beverage', 'th': 'อาหารและเครื่องดื่ม', 'ind': 'Agro & Food Industry'},
    '.FASHION': {'en': 'Fashion', 'th': 'แฟชั่น', 'ind': 'Consumer Products'},
    '.HOME': {'en': 'Home & Office Products', 'th': 'ของใช้ในครัวเรือนและสำนักงาน', 'ind': 'Consumer Products'},
    '.PERSON': {'en': 'Personal Products & Pharmaceuticals', 'th': 'ของใช้ส่วนตัวและเวชภัณฑ์', 'ind': 'Consumer Products'},
    '.BANK': {'en': 'Banking', 'th': 'ธนาคาร', 'ind': 'Financials'},
    '.FIN': {'en': 'Finance & Securities', 'th': 'เงินทุนและหลักทรัพย์', 'ind': 'Financials'},
    '.INSUR': {'en': 'Insurance', 'th': 'ประกันภัยและประกันชีวิต', 'ind': 'Financials'},
    '.AUTO': {'en': 'Automotive', 'th': 'ยานยนต์', 'ind': 'Industrials'},
    '.CONMAT': {'en': 'Construction Materials', 'th': 'วัสดุก่อสร้าง', 'ind': 'Property & Construction'},
    '.CONS': {'en': 'Construction Services', 'th': 'บริการรับเหมาก่อสร้าง', 'ind': 'Property & Construction'},
    '.PAPER': {'en': 'Paper & Printing Materials', 'th': 'กระดาษและวัสดุการพิมพ์', 'ind': 'Industrials'},
    '.PKG': {'en': 'Packaging', 'th': 'บรรจุภัณฑ์', 'ind': 'Industrials'},
    '.STEEL': {'en': 'Steel and Metal Products', 'th': 'เหล็กและผลิตภัณฑ์โลหะ', 'ind': 'Industrials'},
    '.PETRO': {'en': 'Petrochemicals & Chemicals', 'th': 'ปิโตรเคมีและเคมีภัณฑ์', 'ind': 'Industrials'},
    '.PROP': {'en': 'Property Development', 'th': 'พัฒนาอสังหาริมทรัพย์', 'ind': 'Property & Construction'},
    '.PF&REIT': {'en': 'Property Fund & REITs', 'th': 'กองทุนรวมอสังหาริมทรัพย์และ REITs', 'ind': 'Property & Construction'},
    '.COMM': {'en': 'Commerce', 'th': 'พาณิชย์', 'ind': 'Services'},
    '.HELTH': {'en': 'Health Care Services', 'th': 'บริการสุขภาพ', 'ind': 'Services'},
    '.MEDIA': {'en': 'Media & Publishing', 'th': 'สื่อและสิ่งพิมพ์', 'ind': 'Services'},
    '.PROF': {'en': 'Professional Services', 'th': 'บริการเฉพาะกิจ', 'ind': 'Services'},
    '.TOURISM': {'en': 'Tourism & Leisure', 'th': 'การท่องเที่ยวและสันทนาการ', 'ind': 'Services'},
    '.TRANS': {'en': 'Transportation & Logistics', 'th': 'ขนส่งและโลจิสติกส์', 'ind': 'Services'},
    '.ETRON': {'en': 'Electronic Components', 'th': 'ชิ้นส่วนอิเล็กทรอนิกส์', 'ind': 'Technology'},
    '.ICT': {'en': 'Information & Communication Technology', 'th': 'เทคโนโลยีสารสนเทศและการสื่อสาร', 'ind': 'Technology'},
    '.ENERG': {'en': 'Energy & Utilities', 'th': 'พลังงานและสาธารณูปโภค', 'ind': 'Resources'},
    '.IMM': {'en': 'Industrial Materials & Machinery', 'th': 'วัสดุอุตสาหกรรมและเครื่องจักร', 'ind': 'Industrials'},
}

# Reverse map: from stock_metadata.sector -> sector index symbol
SECTOR_NAME_TO_SYM = {v['en']: k for k, v in SECTOR_MAP.items()}

# Benchmark Indices
BENCHMARK_SYMBOLS = ['.SET', '.SET50', '.SET100', '.sSET', '.mai']

# Official SET50 & SET100 Constituents
SET50_SYMBOLS = [
    "ADVANC", "AOT", "AWC", "BANPU", "BBL", "BCP", "BDMS", "BEM", "BH", "BJC",
    "CCET", "COM7", "CPALL", "CPF", "CPN", "CRC", "DELTA", "EGCO", "GPSC", "GULF",
    "HMPRO", "IVL", "KBANK", "KKP", "KTB", "KTC", "LH", "MINT", "MRDIYT", "MTC",
    "OR", "OSP", "PTT", "PTTEP", "PTTGC", "RATCH", "SCB", "SCC", "SCGP", "TCAP",
    "TFG", "THAI", "TIDLOR", "TISCO", "TLI", "TOP", "TRUE", "TTB", "TU", "WHA"
]

SET100_SYMBOLS = [
    "AAV", "ADVANC", "AEONTS", "AMATA", "AOT", "AP", "AURA", "AWC", "BA", "BAM",
    "BANPU", "BBL", "BCH", "BCP", "BCPG", "BDMS", "BEM", "BGRIM", "BH", "BJC",
    "BLA", "BTG", "BTS", "CBG", "CCET", "CENTEL", "CHG", "CK", "COM7", "CPALL",
    "CPF", "CPN", "CRC", "DELTA", "DOHOME", "EA", "EGCO", "ERW", "GFPT", "GLOBAL",
    "GPSC", "GULF", "GUNKUL", "HANA", "HMPRO", "ICHI", "IRPC", "IVL", "JMART", "JMT",
    "KBANK", "KCE", "KKP", "KTB", "KTC", "LH", "M", "MEGA", "MINT", "MOSHI",
    "MRDIYT", "MTC", "OR", "OSP", "PLANB", "PR9", "PRM", "PTG", "PTT", "PTTEP",
    "PTTGC", "QH", "RATCH", "RCL", "SAWAD", "SCB", "SCC", "SCGP", "SIRI", "SPALI",
    "SPRC", "STA", "STECON", "STGT", "TASCO", "TCAP", "TFG", "THAI", "THCOM", "TIDLOR",
    "TISCO", "TLI", "TOA", "TOP", "TRUE", "TTB", "TU", "VGI", "WHA", "WHAUP"
]

# Regex pattern for derivative warrants
DW_PATTERN = r'[0-9]{2}[CP][0-9]{4}'


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def r(v: Optional[float], nd: int = 2) -> Optional[float]:
    """Round preserving None and collapsing -0.0."""
    if v is None:
        return None
    val = round(float(v), nd)
    return 0.0 if val == 0 else val


def fmt_date_range(d1: dt.date, d2: dt.date) -> str:
    """Format e.g. 18 Sep - 24 Sep 2026"""
    if d1.year == d2.year:
        return f"{d1.strftime('%d %b')} - {d2.strftime('%d %b %Y')}"
    return f"{d1.strftime('%d %b %Y')} - {d2.strftime('%d %b %Y')}"


# -----------------------------------------------------------------------------
# Extraction & Computation
# -----------------------------------------------------------------------------

def get_trading_dates(con: duckdb.DuckDBPyConnection) -> List[dt.date]:
    """Fetch all official trading dates in ascending order."""
    rows = con.execute("""
        SELECT distinct date 
        FROM daily_stocks 
        WHERE volume > 0 
        GROUP BY date 
        HAVING count(*) >= 100 
        ORDER BY date
    """).fetchall()
    return [r[0] for r in rows]


def get_ytd_base_date(con: duckdb.DuckDBPyConnection, current_year: int = 2026) -> dt.date:
    """Get the last trading date of the prior year (2025-12-30)."""
    row = con.execute(f"""
        SELECT max(date) 
        FROM daily_stocks 
        WHERE date <= '{current_year - 1}-12-31' AND volume > 0
    """).fetchone()
    if row and row[0]:
        return row[0]
    # Fallback to earliest trading date in current year
    row2 = con.execute(f"""
        SELECT min(date) 
        FROM daily_stocks 
        WHERE date >= '{current_year}-01-01' AND volume > 0
    """).fetchone()
    return row2[0] if row2 else dt.date(2025, 12, 30)


def build_weekly_periods(dates: List[dt.date], max_weeks: int = MAX_WEEKS) -> List[Dict[str, Any]]:
    """
    Build weekly cycles ending on Thursday (Friday-Thursday periods).
    If there are days after the latest Thursday, include the current in-progress week as WTD.
    """
    thursdays = [d for d in dates if d.weekday() == 3]
    if not thursdays:
        return []

    weeks: List[Dict[str, Any]] = []
    latest_thu = thursdays[-1]
    days_after = [d for d in dates if d > latest_thu]

    # Include in-progress WTD if there are trading days after latest Thursday
    if days_after:
        weeks.append({
            'id': days_after[-1].isoformat(),
            'end_date': days_after[-1],
            'base_date': latest_thu,
            'period_dates': days_after,
            'is_wtd': True,
            'status': 'In Progress',
            'label': f"{days_after[0].strftime('%d %b')} - {days_after[-1].strftime('%d %b %Y')} (WTD)",
            'short_label': f"{days_after[0].strftime('%d %b')} - {days_after[-1].strftime('%d %b')} (WTD)"
        })

    # Add completed Thursday weeks
    for i in range(len(thursdays) - 1, -1, -1):
        if len(weeks) >= max_weeks:
            break
        thu = thursdays[i]
        prev_thu_candidates = [d for d in dates if d < thu and d.weekday() == 3]
        if not prev_thu_candidates:
            continue
        prev_thu = prev_thu_candidates[-1]
        p_days = [d for d in dates if prev_thu < d <= thu]
        if not p_days:
            continue

        weeks.append({
            'id': thu.isoformat(),
            'end_date': thu,
            'base_date': prev_thu,
            'period_dates': p_days,
            'is_wtd': False,
            'status': 'Closed',
            'label': f"{p_days[0].strftime('%d %b')} - {thu.strftime('%d %b %Y')}",
            'short_label': f"{p_days[0].strftime('%d %b')} - {thu.strftime('%d %b')}"
        })

    return weeks


def process_week(
    con: duckdb.DuckDBPyConnection,
    week_meta: Dict[str, Any],
    ytd_base_date: dt.date
) -> Dict[str, Any]:
    """Compute all 7 weekly modules for a specific weekly period."""
    base_dt = week_meta['base_date'].isoformat()
    end_dt = week_meta['end_date'].isoformat()
    ytd_dt = ytd_base_date.isoformat()
    p_start = week_meta['period_dates'][0].isoformat()
    p_end = week_meta['period_dates'][-1].isoformat()
    num_days = len(week_meta['period_dates'])

    # -------------------------------------------------------------------------
    # 1. Benchmark & Sector Index Prices (Base, End, YTD)
    # -------------------------------------------------------------------------
    all_index_symbols = list(SECTOR_MAP.keys()) + BENCHMARK_SYMBOLS
    idx_sql = f"""
    WITH b AS (SELECT symbol, close as c_base FROM daily_stocks WHERE date = '{base_dt}'),
         e AS (SELECT symbol, close as c_end, high as high_end, low as low_end FROM daily_stocks WHERE date = '{end_dt}'),
         y AS (SELECT symbol, close as c_ytd FROM daily_stocks WHERE date = '{ytd_dt}'),
         p_rng AS (
             SELECT symbol, min(low) as min_low, max(high) as max_high 
             FROM daily_stocks 
             WHERE date BETWEEN '{p_start}' AND '{p_end}'
             GROUP BY symbol
         )
    SELECT e.symbol, b.c_base, e.c_end,
           ((e.c_end / b.c_base) - 1) * 100 as wow_pct,
           ((e.c_end / y.c_ytd) - 1) * 100 as ytd_pct,
           y.c_ytd,
           p_rng.min_low, p_rng.max_high
    FROM e
    LEFT JOIN b ON e.symbol = b.symbol
    LEFT JOIN y ON e.symbol = y.symbol
    LEFT JOIN p_rng ON e.symbol = p_rng.symbol
    WHERE e.symbol IN ({','.join([repr(s) for s in all_index_symbols])})
    """
    idx_data = {r[0]: {
        'base': r[1], 'end': r[2], 'wow': r[3], 'ytd': r[4],
        'ytd_base': r[5], 'low': r[6], 'high': r[7]
    } for r in con.execute(idx_sql).fetchall()}

    # -------------------------------------------------------------------------
    # 2. Stock Traded Statistics by Sector in this Period
    # -------------------------------------------------------------------------
    sec_stats_sql = f"""
    SELECT m.sector,
           count(distinct d.symbol) as stocks,
           sum(d.volume) as total_vol,
           sum(d.value) / {MB} as total_val_mb,
           sum(d.nvdr_buy) / {MB} as nvdr_buy_mb,
           sum(d.nvdr_sell) / {MB} as nvdr_sell_mb,
           sum(d.nvdr_net) / {MB} as nvdr_net_mb
    FROM daily_stocks d
    JOIN stock_metadata m ON d.symbol = m.symbol
    WHERE d.date BETWEEN '{p_start}' AND '{p_end}'
      AND m.industry NOT IN ('INDEX', 'MARKET_INDEX', 'SECTOR_INDEX', '')
      AND d.symbol NOT LIKE '.%'
      AND NOT regexp_matches(d.symbol, '-W[0-9]*$')
      AND d.symbol NOT LIKE '%-P'
      AND d.symbol NOT LIKE '%-F'
      AND d.symbol NOT LIKE '%-R'
      AND NOT regexp_matches(d.symbol, '{DW_PATTERN}')
    GROUP BY m.sector
    """
    sec_stats = {r[0]: {
        'stocks': r[1], 'vol': r[2], 'val': r[3],
        'nvdr_buy': r[4], 'nvdr_sell': r[5], 'nvdr_net': r[6]
    } for r in con.execute(sec_stats_sql).fetchall()}

    total_market_val = sum(s['val'] for s in sec_stats.values() if s['val']) or 1.0
    total_market_nvdr = sum(s['nvdr_net'] for s in sec_stats.values() if s['nvdr_net'] is not None)

    # Top buy/sell stock per sector
    top_stock_sql = f"""
    WITH stock_nvdr AS (
        SELECT d.symbol, m.sector,
               sum(d.nvdr_net) / {MB} as net_mb,
               row_number() OVER (PARTITION BY m.sector ORDER BY sum(d.nvdr_net) DESC) as rn_buy,
               row_number() OVER (PARTITION BY m.sector ORDER BY sum(d.nvdr_net) ASC) as rn_sell
        FROM daily_stocks d
        JOIN stock_metadata m ON d.symbol = m.symbol
        WHERE d.date BETWEEN '{p_start}' AND '{p_end}'
          AND m.industry NOT IN ('INDEX', 'MARKET_INDEX', 'SECTOR_INDEX', '')
          AND d.symbol NOT LIKE '.%'
          AND NOT regexp_matches(d.symbol, '-W[0-9]*$')
          AND d.symbol NOT LIKE '%-P'
          AND d.symbol NOT LIKE '%-F'
          AND d.symbol NOT LIKE '%-R'
          AND NOT regexp_matches(d.symbol, '{DW_PATTERN}')
          AND d.nvdr_net IS NOT NULL
        GROUP BY d.symbol, m.sector
    )
    SELECT sector,
           max(CASE WHEN rn_buy = 1 THEN symbol END) as top_buy_sym,
           max(CASE WHEN rn_buy = 1 THEN net_mb END) as top_buy_mb,
           max(CASE WHEN rn_sell = 1 THEN symbol END) as top_sell_sym,
           max(CASE WHEN rn_sell = 1 THEN net_mb END) as top_sell_mb
    FROM stock_nvdr
    GROUP BY sector
    """
    sec_nvdr_top = {r[0]: {
        'top_buy': r[1], 'top_buy_mb': r[2],
        'top_sell': r[3], 'top_sell_mb': r[4]
    } for r in con.execute(top_stock_sql).fetchall()}

    # -------------------------------------------------------------------------
    # 3. Assemble Sector Rankings (Weekly & YTD) and Breakdowns
    # -------------------------------------------------------------------------
    set_wow = idx_data.get('.SET', {}).get('wow')
    set_ytd = idx_data.get('.SET', {}).get('ytd')

    sector_records = []
    for sym, info in SECTOR_MAP.items():
        s_name = info['en']
        id_info = idx_data.get(sym, {})
        st_info = sec_stats.get(s_name, {})
        nv_top = sec_nvdr_top.get(s_name, {})

        val_mb = st_info.get('val', 0.0) or 0.0
        val_share = (val_mb / total_market_val * 100) if total_market_val else 0.0
        nvdr_net = st_info.get('nvdr_net')

        sector_records.append({
            'symbol': sym,
            'name_en': s_name,
            'name_th': info['th'],
            'industry': info['ind'],
            'base_close': r(id_info.get('base')),
            'end_close': r(id_info.get('end')),
            'chg': r((id_info.get('end') - id_info.get('base')) if id_info.get('end') and id_info.get('base') else None),
            'wow_pct': r(id_info.get('wow')),
            'ytd_base': r(id_info.get('ytd_base')),
            'ytd_pct': r(id_info.get('ytd')),
            'alpha_set': r((id_info.get('ytd') - set_ytd) if id_info.get('ytd') is not None and set_ytd is not None else None),
            'week_low': r(id_info.get('low')),
            'week_high': r(id_info.get('high')),
            'val_mb': r(val_mb, 1),
            'val_share': r(val_share, 2),
            'avg_daily_val': r(val_mb / num_days if num_days else 0, 1),
            'stocks_count': st_info.get('stocks', 0),
            'nvdr_buy_mb': r(st_info.get('nvdr_buy'), 1),
            'nvdr_sell_mb': r(st_info.get('nvdr_sell'), 1),
            'nvdr_net_mb': r(nvdr_net, 1),
            'nvdr_ratio': r((abs(nvdr_net) / val_mb * 100) if nvdr_net is not None and val_mb > 0 else None, 1),
            'top_buy_sym': nv_top.get('top_buy'),
            'top_buy_mb': r(nv_top.get('top_buy_mb'), 1),
            'top_sell_sym': nv_top.get('top_sell'),
            'top_sell_mb': r(nv_top.get('top_sell_mb'), 1),
        })

    # Ranking 1: Sector Performance Ranking Last Week (Fri-Thu)
    sec_weekly_ranked = sorted(
        sector_records,
        key=lambda x: (x['wow_pct'] is not None, x['wow_pct']),
        reverse=True
    )
    for i, item in enumerate(sec_weekly_ranked, 1):
        item['rank_wow'] = i

    # Ranking 2: Sector Performance Ranking YTD
    sec_ytd_ranked = sorted(
        sector_records,
        key=lambda x: (x['ytd_pct'] is not None, x['ytd_pct']),
        reverse=True
    )
    for i, item in enumerate(sec_ytd_ranked, 1):
        item['rank_ytd'] = i

    # Ranking 3: Breakdown of Trading Value by Sector
    sec_value_ranked = sorted(
        sector_records,
        key=lambda x: (x['val_mb'] is not None, x['val_mb']),
        reverse=True
    )
    for i, item in enumerate(sec_value_ranked, 1):
        item['rank_val'] = i

    # Ranking 4: NVDR Net Buy/Sell by Sector
    sec_nvdr_ranked = sorted(
        sector_records,
        key=lambda x: (x['nvdr_net_mb'] is not None, x['nvdr_net_mb']),
        reverse=True
    )
    for i, item in enumerate(sec_nvdr_ranked, 1):
        item['rank_nvdr'] = i

    # -------------------------------------------------------------------------
    # 4. Individual Stock Universe Query for SET50, SET100, and SET Top Movers
    # -------------------------------------------------------------------------
    stock_sql = f"""
    WITH b AS (SELECT symbol, close as c_base FROM daily_stocks WHERE date = '{base_dt}'),
         e AS (SELECT symbol, close as c_end, market_cap FROM daily_stocks WHERE date = '{end_dt}'),
         y AS (SELECT symbol, close as c_ytd FROM daily_stocks WHERE date = '{ytd_dt}'),
         stats AS (
             SELECT symbol, 
                    sum(volume) as total_vol,
                    sum(value) / {MB} as val_mb,
                    sum(nvdr_buy) / {MB} as nvdr_buy_mb,
                    sum(nvdr_sell) / {MB} as nvdr_sell_mb,
                    sum(nvdr_net) / {MB} as nvdr_net_mb,
                    min(low) as week_low,
                    max(high) as week_high
             FROM daily_stocks
             WHERE date BETWEEN '{p_start}' AND '{p_end}'
             GROUP BY symbol
         )
    SELECT e.symbol, m.company_name, m.sector, m.industry,
           b.c_base, e.c_end,
           ((e.c_end / b.c_base) - 1) * 100 as wow_pct,
           ((e.c_end / y.c_ytd) - 1) * 100 as ytd_pct,
           stats.val_mb, stats.nvdr_net_mb,
           stats.week_low, stats.week_high,
           e.market_cap / {MB} as mcap_mb,
           stats.total_vol
    FROM e
    JOIN b ON e.symbol = b.symbol
    JOIN stock_metadata m ON e.symbol = m.symbol
    LEFT JOIN stats ON e.symbol = stats.symbol
    LEFT JOIN y ON e.symbol = y.symbol
    WHERE m.industry NOT IN ('INDEX', 'MARKET_INDEX', 'SECTOR_INDEX', '')
      AND e.symbol NOT LIKE '.%'
      AND NOT regexp_matches(e.symbol, '-W[0-9]*$')
      AND e.symbol NOT LIKE '%-P'
      AND e.symbol NOT LIKE '%-F'
      AND e.symbol NOT LIKE '%-R'
      AND NOT regexp_matches(e.symbol, '{DW_PATTERN}')
      AND b.c_base > 0 AND e.c_end > 0
    """
    raw_stocks = con.execute(stock_sql).fetchall()

    def format_stock_row(r_tuple):
        sym, cname, sec, ind, c_b, c_e, wow, ytd, val, nvdr, lo, hi, mcap, vol = r_tuple
        chg = (c_e - c_b) if c_e is not None and c_b is not None else None
        return {
            'symbol': sym,
            'name': cname or sym,
            'sector': sec or '—',
            'industry': ind or '—',
            'base': r(c_b),
            'close': r(c_e),
            'chg': r(chg),
            'wow_pct': r(wow),
            'ytd_pct': r(ytd),
            'val_mb': r(val, 1) if val is not None else 0.0,
            'val_share': r((val / total_market_val * 100) if val and total_market_val else 0.0, 2),
            'nvdr_mb': r(nvdr, 1) if nvdr is not None else None,
            'low': r(lo),
            'high': r(hi),
            'mcap_mb': r(mcap, 0) if mcap is not None else None,
            'vol': int(vol) if vol else 0,
        }

    all_stock_dicts = [format_stock_row(r) for r in raw_stocks]
    stock_by_sym = {s['symbol']: s for s in all_stock_dicts}

    # Fallback lookup for any missing SET100 / SET50 constituent (e.g. suspended/SP or un-traded on end date)
    missing_syms = [s for s in SET100_SYMBOLS if s not in stock_by_sym]
    if missing_syms:
        for ms in missing_syms:
            meta_row = con.execute(
                f"SELECT company_name, sector, industry FROM stock_metadata WHERE symbol = '{ms}'"
            ).fetchone()
            cname = meta_row[0] if meta_row else ms
            sec = meta_row[1] if meta_row else '—'
            ind = meta_row[2] if meta_row else '—'

            last_p = con.execute(
                f"SELECT close FROM daily_stocks WHERE symbol = '{ms}' AND date <= '{end_dt}' AND close IS NOT NULL ORDER BY date DESC LIMIT 1"
            ).fetchone()
            c_last = last_p[0] if last_p else None

            base_p = con.execute(
                f"SELECT close FROM daily_stocks WHERE symbol = '{ms}' AND date <= '{base_dt}' AND close IS NOT NULL ORDER BY date DESC LIMIT 1"
            ).fetchone()
            c_base = base_p[0] if base_p else c_last

            wow_pct = ((c_last / c_base) - 1) * 100 if c_last and c_base and c_base > 0 else 0.0

            stock_by_sym[ms] = {
                'symbol': ms,
                'name': cname or ms,
                'sector': sec or '—',
                'industry': ind or '—',
                'base': r(c_base),
                'close': r(c_last),
                'chg': r((c_last - c_base) if c_last and c_base else 0.0),
                'wow_pct': r(wow_pct),
                'ytd_pct': None,
                'val_mb': 0.0,
                'val_share': 0.0,
                'nvdr_mb': 0.0,
                'low': r(c_last),
                'high': r(c_last),
                'mcap_mb': None,
                'vol': 0,
            }

    # SET50 Ranking (exactly 50)
    set50_list = [stock_by_sym[s] for s in SET50_SYMBOLS if s in stock_by_sym]
    set50_ranked = sorted(set50_list, key=lambda x: (x['wow_pct'] is not None, x['wow_pct']), reverse=True)
    for i, s in enumerate(set50_ranked, 1):
        s['rank'] = i

    # SET100 Ranking (exactly 100)
    set100_list = [stock_by_sym[s] for s in SET100_SYMBOLS if s in stock_by_sym]
    set100_ranked = sorted(set100_list, key=lambda x: (x['wow_pct'] is not None, x['wow_pct']), reverse=True)
    for i, s in enumerate(set100_ranked, 1):
        s['rank'] = i

    # SET Top 20 Performance
    # Filter for reasonable liquidity (turnover >= 5 MB during the week) for high quality gainers/losers
    liquid_stocks = [s for s in all_stock_dicts if s['val_mb'] >= 5.0 and s['wow_pct'] is not None]
    all_valid_stocks = [s for s in all_stock_dicts if s['wow_pct'] is not None]

    top20_gainers_liquid = sorted(liquid_stocks, key=lambda x: x['wow_pct'], reverse=True)[:20]
    top20_losers_liquid = sorted(liquid_stocks, key=lambda x: x['wow_pct'])[:20]

    top20_gainers_all = sorted(all_valid_stocks, key=lambda x: x['wow_pct'], reverse=True)[:20]
    top20_losers_all = sorted(all_valid_stocks, key=lambda x: x['wow_pct'])[:20]

    top20_by_value = sorted(all_stock_dicts, key=lambda x: x['val_mb'], reverse=True)[:20]

    for i, s in enumerate(top20_gainers_liquid, 1):
        s['rank'] = i
    for i, s in enumerate(top20_losers_liquid, 1):
        s['rank'] = i
    for i, s in enumerate(top20_gainers_all, 1):
        s['rank'] = i
    for i, s in enumerate(top20_losers_all, 1):
        s['rank'] = i
    for i, s in enumerate(top20_by_value, 1):
        s['rank'] = i

    # -------------------------------------------------------------------------
    # 5. Market Breadth & Summary KPIs
    # -------------------------------------------------------------------------
    adv_count = sum(1 for s in all_valid_stocks if s['wow_pct'] > 0)
    dec_count = sum(1 for s in all_valid_stocks if s['wow_pct'] < 0)
    unch_count = sum(1 for s in all_valid_stocks if s['wow_pct'] == 0)

    set_info = idx_data.get('.SET', {})
    set50_info = idx_data.get('.SET50', {})
    set100_info = idx_data.get('.SET100', {})

    set_base = set_info.get('base')
    set_close = set_info.get('end')
    set_chg = (set_close - set_base) if set_close and set_base else None

    # Top & bottom sector of the week
    top_sec = sec_weekly_ranked[0] if sec_weekly_ranked else None
    bot_sec = sec_weekly_ranked[-1] if sec_weekly_ranked else None

    # Top foreign inflow / outflow sector
    top_nvdr_sec = sec_nvdr_ranked[0] if sec_nvdr_ranked else None
    bot_nvdr_sec = sec_nvdr_ranked[-1] if sec_nvdr_ranked else None

    summary = {
        'set_close': r(set_close),
        'set_chg': r(set_chg),
        'set_wow_pct': r(set_info.get('wow')),
        'set_ytd_pct': r(set_info.get('ytd')),
        'set50_close': r(set50_info.get('end')),
        'set50_wow_pct': r(set50_info.get('wow')),
        'set100_close': r(set100_info.get('end')),
        'set100_wow_pct': r(set100_info.get('wow')),
        'turnover_mb': r(total_market_val, 0),
        'turnover_bn': r(total_market_val / 1000.0, 2),
        'avg_daily_turnover_bn': r((total_market_val / 1000.0) / num_days if num_days else 0, 2),
        'nvdr_net_mb': r(total_market_nvdr, 1),
        'trading_days': num_days,
        'traded_names': len(all_valid_stocks),
        'adv': adv_count,
        'dec': dec_count,
        'unch': unch_count,
        'top_sector_name': top_sec['name_en'] if top_sec else '—',
        'top_sector_wow': top_sec['wow_pct'] if top_sec else None,
        'top_sector_sym': top_sec['symbol'] if top_sec else '',
        'bot_sector_name': bot_sec['name_en'] if bot_sec else '—',
        'bot_sector_wow': bot_sec['wow_pct'] if bot_sec else None,
        'top_nvdr_sector_name': top_nvdr_sec['name_en'] if top_nvdr_sec else '—',
        'top_nvdr_sector_mb': top_nvdr_sec['nvdr_net_mb'] if top_nvdr_sec else None,
        'bot_nvdr_sector_name': bot_nvdr_sec['name_en'] if bot_nvdr_sec else '—',
        'bot_nvdr_sector_mb': bot_nvdr_sec['nvdr_net_mb'] if bot_nvdr_sec else None,
    }

    return {
        'week_id': week_meta['id'],
        'label': week_meta['label'],
        'short_label': week_meta['short_label'],
        'is_wtd': week_meta['is_wtd'],
        'status': week_meta['status'],
        'base_date': base_dt,
        'end_date': end_dt,
        'period_dates': [d.isoformat() for d in week_meta['period_dates']],
        'summary': summary,
        'sectors_weekly': sec_weekly_ranked,
        'sectors_ytd': sec_ytd_ranked,
        'sectors_value': sec_value_ranked,
        'sectors_nvdr': sec_nvdr_ranked,
        'set50': set50_ranked,
        'set100': set100_ranked,
        'top20_gainers_liquid': top20_gainers_liquid,
        'top20_losers_liquid': top20_losers_liquid,
        'top20_gainers_all': top20_gainers_all,
        'top20_losers_all': top20_losers_all,
        'top20_value': top20_by_value,
        'benchmarks': {k: idx_data.get(k) for k in BENCHMARK_SYMBOLS},
    }


# -----------------------------------------------------------------------------
# Main Builder
# -----------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Build Weekly Friday Market Dashboard")
    parser.add_argument("--db", default=DB_PATH, help="Path to DuckDB file")
    parser.add_argument("--weeks", type=int, default=MAX_WEEKS, help="Number of weekly periods to include")
    parser.add_argument("--out", default=OUTPUT_PATH, help="Output HTML file path")
    args = parser.parse_args()

    if not os.path.exists(args.db):
        sys.exit(f"Error: Database not found at {args.db}")

    print(f"Connecting to DuckDB: {args.db}")
    con = duckdb.connect(args.db, read_only=True)

    print("Fetching trading dates and identifying weekly periods (Fri-Thu)...")
    dates = get_trading_dates(con)
    ytd_base_date = get_ytd_base_date(con, current_year=2026)
    weeks_meta = build_weekly_periods(dates, max_weeks=args.weeks)

    print(f"YTD Base Date: {ytd_base_date}")
    print(f"Discovered {len(weeks_meta)} weekly periods for dashboard.")

    weeks_payload = {}
    for i, wm in enumerate(weeks_meta, 1):
        print(f"  [{i}/{len(weeks_meta)}] Processing {wm['label']} (base: {wm['base_date']}, end: {wm['end_date']})...")
        weeks_payload[wm['id']] = process_week(con, wm, ytd_base_date)

    con.close()

    # Determine default active week:
    # Prefer latest closed week if available, else first in list
    closed_weeks = [wm['id'] for wm in weeks_meta if not wm['is_wtd']]
    default_week_id = closed_weeks[0] if closed_weeks else weeks_meta[0]['id']

    data = {
        'generated': dt.datetime.now().strftime("%d %b %Y %H:%M"),
        'ytdBaseDate': ytd_base_date.isoformat(),
        'defaultWeekId': default_week_id,
        'weekList': [wm['id'] for wm in weeks_meta],
        'weeks': weeks_payload,
        'sectorMeta': SECTOR_MAP,
    }

    # Encode logo
    print(f"Encoding logo from {LOGO_PATH}...")
    with open(LOGO_PATH, "rb") as f:
        logo_b64 = "data:image/png;base64," + base64.b64encode(f.read()).decode("ascii")

    # Read template
    print(f"Reading template from {TEMPLATE_PATH}...")
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    # Inject data & logo
    payload_json = json.dumps(data, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    html = html.replace("/*__LOGO__*/''", json.dumps(logo_b64))
    html = html.replace("/*__DATA__*/null", payload_json)

    # Write output
    print(f"Writing dashboard to {args.out}...")
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(html)

    size_kb = os.path.getsize(args.out) / 1024
    print(f"Successfully generated {args.out} ({size_kb:,.1f} KB, payload {len(payload_json)/1024:,.1f} KB)")


if __name__ == "__main__":
    main()
