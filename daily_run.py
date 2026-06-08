"""
MSM Daily Run — Mark-to-market + new OOS entry append
=====================================================

매일 1회 실행 (Colab 단일 셀 또는 cron):
  1. Load realized_log + axis_v3
  2. OPEN position mtm 갱신 (만기 시 CLOSED)
  3. 신규 entry signal이 있으면 append (외부 signal source 의존)
  4. parquet save + git commit + push

Usage:
  python forward_test/daily_run.py [--dry-run]

신규 entry signal 생성은 v12 simulator 영구 불가 (§0 #13)로
별도 input file 의존:
  forward_test/inbox/long_signals_YYYYMMDD.json (10 codes list)
"""

import argparse
import json
import subprocess
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')

# engine.py 의존
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine import (
    REPO_ROOT, HOLD_LONG, OOS_BOUNDARY,
    load_axis_v3,
    update_open_positions, append_oos_entries,
    portfolio_metrics,
)


LOG_PATH    = REPO_ROOT / 'forward_test/log/realized/realized_log.parquet'
INBOX_DIR   = REPO_ROOT / 'forward_test/inbox'
SCHEMA_PATH = REPO_ROOT / 'forward_test/schema/realized_log_v1.json'


# ============================================================
# Helpers
# ============================================================
def latest_krx_biz_day() -> pd.Timestamp:
    from pykrx import stock
    today = pd.Timestamp.now(tz='Asia/Seoul').normalize().tz_localize(None)
    df_idx = stock.get_index_ohlcv_by_date(
        (today - pd.Timedelta(days=14)).strftime('%Y%m%d'),
        today.strftime('%Y%m%d'),
        '1001')
    assert df_idx is not None and len(df_idx) > 0, 'no recent KRX biz days'
    return pd.Timestamp(df_idx.index[-1])


def fetch_close_map(codes: list[str], date: pd.Timestamp) -> dict[str, float]:
    from pykrx import stock
    d_str = date.strftime('%Y%m%d')
    out = {}
    for code in codes:
        try:
            df_px = stock.get_market_ohlcv_by_date(d_str, d_str, code)
            if df_px is None or len(df_px) == 0:
                continue
            out[code] = float(df_px.iloc[-1]['종가'])
        except Exception as e:
            print(f'  fetch fail {code}: {str(e)[:50]}')
    return out


def fetch_two_day_close(codes: list[str], d0: pd.Timestamp, d1: pd.Timestamp) -> dict[str, dict]:
    from pykrx import stock
    out = {}
    for code in codes:
        try:
            df_px = stock.get_market_ohlcv_by_date(
                d0.strftime('%Y%m%d'), d1.strftime('%Y%m%d'), code)
            if df_px is None or len(df_px) < 2:
                continue
            out[code] = {
                'entry_px': float(df_px.iloc[0]['종가']),
                'mtm_px':   float(df_px.iloc[1]['종가']),
            }
        except Exception as e:
            print(f'  fetch fail {code}: {str(e)[:50]}')
    return out


def load_new_signal(date: pd.Timestamp) -> dict | None:
    """forward_test/inbox/long_signals_YYYYMMDD.json 형식:
       { "entry_date": "2026-06-08", "side": "LONG", "codes": [...] }
    """
    p = INBOX_DIR / f'long_signals_{date.strftime("%Y%m%d")}.json'
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding='utf-8'))


def git_commit_push(msg: str, dry_run: bool = False) -> str:
    if dry_run:
        return 'dry-run'
    subprocess.run(['git', 'add', str(LOG_PATH.relative_to(REPO_ROOT))],
                   check=True, cwd=REPO_ROOT)
    r = subprocess.run(['git', 'commit', '-m', msg],
                       capture_output=True, text=True, cwd=REPO_ROOT)
    if 'nothing to commit' in r.stdout.lower():
        return 'no-op'
    r2 = subprocess.run(['git', 'push', 'origin', 'main'],
                        capture_output=True, text=True, cwd=REPO_ROOT)
    return 'OK' if r2.returncode == 0 else r2.stderr[:200]


# ============================================================
# Main
# ============================================================
def main(dry_run: bool = False) -> int:
    print(f'=== MSM daily_run (dry_run={dry_run}) ===')

    # Load
    assert LOG_PATH.exists(), f'NOT FOUND: {LOG_PATH}'
    df_log = pd.read_parquet(LOG_PATH)
    n_orig = len(df_log)
    print(f'  loaded: {n_orig} rows')

    df_ax = load_axis_v3()
    print(f'  axis_v3 cutoff: {df_ax.index.max().date()}')

    # Step 1: latest biz day
    latest_biz = latest_krx_biz_day()
    prev_mtm = pd.to_datetime(df_log.loc[
        df_log['status'] == 'OPEN', 'mtm_date']).max() if (df_log['status']=='OPEN').any() else None
    print(f'  latest_biz: {latest_biz.date()}, prev_mtm: {prev_mtm.date() if pd.notna(prev_mtm) else None}')

    # Step 2: mtm update
    if pd.notna(prev_mtm) and latest_biz <= prev_mtm:
        print(f'  no new biz day → skip mtm update')
        updates, closes = 0, 0
    else:
        codes_open = df_log.loc[
            (df_log['signal_status'] == 'TAKEN') & (df_log['status'] == 'OPEN'),
            'code'].unique().tolist()
        if codes_open:
            px_map = fetch_close_map(codes_open, latest_biz)
            df_log, updates, closes = update_open_positions(df_log, px_map, latest_biz)
            print(f'  mtm: updates={updates}, closes={closes}')
        else:
            updates, closes = 0, 0
            print(f'  no OPEN positions')

    # Step 3: new entry (inbox check)
    new_signal = load_new_signal(latest_biz)
    new_entries = 0
    if new_signal:
        entry_date = pd.Timestamp(new_signal['entry_date'])
        codes = new_signal['codes']
        # entry_date close + latest_biz close 2일 fetch
        px_map_new = fetch_two_day_close(codes, entry_date, latest_biz)
        df_new = append_oos_entries(
            entry_date=entry_date,
            mtm_date=latest_biz,
            codes=codes,
            px_map=px_map_new,
            df_ax=df_ax,
            side=new_signal.get('side', 'LONG'),
            hold_target=new_signal.get('hold_target', HOLD_LONG),
            notes=f'daily_run entry {entry_date.date()}',
        )
        df_log = pd.concat([df_log, df_new], ignore_index=True)
        new_entries = len(df_new)
        print(f'  new entries: {new_entries} (variants × codes)')
    else:
        print(f'  no new signal in inbox')

    # Step 4: save + git
    if dry_run:
        print(f'  dry-run: not saving')
    else:
        df_log.to_parquet(LOG_PATH, index=False)
        print(f'  saved: {LOG_PATH} (total {len(df_log)} rows)')

    # Step 5: summary
    summary = portfolio_metrics(df_log)
    print(f'\nportfolio summary:')
    print(summary.to_string(index=False))

    # Step 6: git
    if updates > 0 or new_entries > 0:
        msg = f'MSM daily_run {latest_biz.date()}: mtm updates={updates} closes={closes} new={new_entries}'
        status = git_commit_push(msg, dry_run)
        print(f'\ngit: {status}')

    return 0


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    sys.exit(main(dry_run=args.dry_run))
