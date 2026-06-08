# ============================================================
# MSM Daily Run — Colab Single-Cell Template (paste & run)
# 매일 1회 실행. idempotent. push 자동.
# ============================================================
import os, sys, subprocess, json
from pathlib import Path
import warnings; warnings.filterwarnings('ignore')

REPO = '/content/choonsimi-msm'
os.chdir(REPO)
sys.path.insert(0, REPO)

from engine import (
    HOLD_LONG, OOS_BOUNDARY,
    load_axis_v3, update_open_positions, append_oos_entries,
    portfolio_metrics,
)

import pandas as pd, numpy as np
from pykrx import stock

LOG  = Path('forward_test/log/realized/realized_log.parquet')
INBOX = Path('forward_test/inbox')

# ---- 1. load ----
df_log = pd.read_parquet(LOG)
df_ax  = load_axis_v3()
n_orig = len(df_log)
print(f'[1] loaded: {n_orig} rows, axis cutoff={df_ax.index.max().date()}')

# ---- 2. latest biz day ----
today = pd.Timestamp.now(tz='Asia/Seoul').normalize().tz_localize(None)
df_idx = stock.get_index_ohlcv_by_date(
    (today - pd.Timedelta(days=14)).strftime('%Y%m%d'),
    today.strftime('%Y%m%d'), '1001')
latest = pd.Timestamp(df_idx.index[-1])
prev_mtm = pd.to_datetime(df_log.loc[df_log['status']=='OPEN', 'mtm_date']).max() \
           if (df_log['status']=='OPEN').any() else None
print(f'[2] latest_biz={latest.date()}, prev_mtm={prev_mtm.date() if pd.notna(prev_mtm) else None}')

# ---- 3. mtm update ----
if pd.notna(prev_mtm) and latest <= prev_mtm:
    print('[3] no new biz day → skip')
    updates, closes = 0, 0
else:
    codes_open = df_log.loc[
        (df_log['signal_status']=='TAKEN') & (df_log['status']=='OPEN'),
        'code'].unique().tolist()
    if codes_open:
        px_map = {}
        for c in codes_open:
            try:
                df_px = stock.get_market_ohlcv_by_date(
                    latest.strftime('%Y%m%d'), latest.strftime('%Y%m%d'), c)
                if df_px is not None and len(df_px) > 0:
                    px_map[c] = float(df_px.iloc[-1]['종가'])
            except: pass
        df_log, updates, closes = update_open_positions(df_log, px_map, latest)
        print(f'[3] mtm: updates={updates}, closes={closes}')
    else:
        updates, closes = 0, 0
        print('[3] no OPEN positions')

# ---- 4. new entry signal (inbox) ----
sig_path = INBOX / f'long_signals_{latest.strftime("%Y%m%d")}.json'
new_entries = 0
if sig_path.exists():
    sig = json.loads(sig_path.read_text(encoding='utf-8'))
    entry_date = pd.Timestamp(sig['entry_date'])
    codes = sig['codes']
    px_map_new = {}
    for c in codes:
        try:
            df_px = stock.get_market_ohlcv_by_date(
                entry_date.strftime('%Y%m%d'), latest.strftime('%Y%m%d'), c)
            if df_px is not None and len(df_px) >= 2:
                px_map_new[c] = {
                    'entry_px': float(df_px.iloc[0]['종가']),
                    'mtm_px':   float(df_px.iloc[1]['종가']),
                }
        except: pass
    df_new = append_oos_entries(
        entry_date=entry_date, mtm_date=latest,
        codes=codes, px_map=px_map_new, df_ax=df_ax,
        side=sig.get('side', 'LONG'),
        hold_target=sig.get('hold_target', HOLD_LONG),
        notes=f'inbox {entry_date.date()}',
    )
    df_log = pd.concat([df_log, df_new], ignore_index=True)
    new_entries = len(df_new)
    print(f'[4] new entries: {new_entries}')
else:
    print(f'[4] no signal in inbox ({sig_path.name})')

# ---- 5. save ----
df_log.to_parquet(LOG, index=False)
print(f'[5] saved: {LOG} ({len(df_log)} rows)')

# ---- 6. summary ----
summ = portfolio_metrics(df_log)
print('\n[6] portfolio summary:')
print(summ.to_string(index=False))

# ---- 7. git ----
if updates > 0 or new_entries > 0:
    subprocess.run(['git','add', str(LOG)], check=True)
    msg = f'MSM daily {latest.date()}: mtm u={updates} c={closes} new={new_entries}'
    r = subprocess.run(['git','commit','-m', msg], capture_output=True, text=True)
    if 'nothing to commit' not in r.stdout.lower():
        r2 = subprocess.run(['git','push','origin','main'], capture_output=True, text=True)
        print(f'[7] push: {"OK" if r2.returncode==0 else r2.stderr[:200]}')
head = subprocess.run(['git','rev-parse','--short','HEAD'],
                      capture_output=True, text=True).stdout.strip()
print(f'[7] HEAD={head}')
