# ============================================================
# MSM Forward Test — Daily Run @ 19:30 KST
# paste & run. idempotent. push 자동. mtm + entry + Path D eval 통합.
#
# v12 LOCK 운용:
#   LONG : NEUTRAL × bot z_ell top 10, hold 15d, weight 1/10
#   SHORT: SHOCK × bot score top 10, hold 5d, weight 1/10
#
# Signal source: forward_test/inbox/long_signals_YYYYMMDD.json (외부 공급)
#   없으면 mtm만 수행. 시스템 종료 X.
# ============================================================
import os, sys, subprocess, json, time
from pathlib import Path
from datetime import datetime, timezone, timedelta
import warnings; warnings.filterwarnings('ignore')

# === 0. 환경 (Colab repo root) ===
REPO = '/content/choonsimi-msm'
os.chdir(REPO)
sys.path.insert(0, REPO)

KST = timezone(timedelta(hours=9))
now_kst = datetime.now(KST)
print(f'=== MSM Daily Run @ {now_kst.strftime("%Y-%m-%d %H:%M:%S")} KST ===')

# === 1. 의존성 ===
from engine import (
    HOLD_LONG, OOS_BOUNDARY,
    load_axis_v3, update_open_positions, append_oos_entries,
    portfolio_metrics,
)
import pandas as pd, numpy as np
from pykrx import stock

LOG_PATH    = Path('forward_test/log/realized/realized_log.parquet')
INBOX_DIR   = Path('forward_test/inbox')
PATHD_LOG   = Path('forward_test/axis_oos/pathD_eval_oos.parquet')

# inbox 부재 시 생성 (시스템 안정성)
INBOX_DIR.mkdir(parents=True, exist_ok=True)

# === 2. load ===
assert LOG_PATH.exists(), f'realized_log 부재: {LOG_PATH}'
df_log = pd.read_parquet(LOG_PATH)
df_ax  = load_axis_v3()
n_orig = len(df_log)
print(f'[1] loaded: {n_orig} rows, axis cutoff={df_ax.index.max().date()}')

# === 3. latest biz day ===
today = pd.Timestamp.now(tz='Asia/Seoul').normalize().tz_localize(None)
df_idx = stock.get_index_ohlcv_by_date(
    (today - pd.Timedelta(days=14)).strftime('%Y%m%d'),
    today.strftime('%Y%m%d'), '1001')
assert df_idx is not None and len(df_idx) > 0, 'KRX biz day fetch 실패'
latest = pd.Timestamp(df_idx.index[-1])
prev_mtm = pd.to_datetime(df_log.loc[df_log['status']=='OPEN', 'mtm_date']).max() \
           if (df_log['status']=='OPEN').any() else None
print(f'[2] latest_biz={latest.date()}, prev_mtm={prev_mtm.date() if pd.notna(prev_mtm) else None}')

# 19:30 이전 실행 시 경고 (data 확정 전 가능성)
if now_kst.hour < 18 and now_kst.date() == latest.date():
    print(f'    ⚠️ 18:00 KST 이전 실행 — 당일 close 확정 전 가능성. 19:30 후 권장.')

# === 4. mtm update ===
if pd.notna(prev_mtm) and latest <= prev_mtm:
    print('[3] no new biz day → skip mtm')
    updates, closes = 0, 0
else:
    codes_open = df_log.loc[
        (df_log['signal_status']=='TAKEN') & (df_log['status']=='OPEN'),
        'code'].unique().tolist()
    if codes_open:
        px_map = {}
        fail_codes = []
        for c in codes_open:
            try:
                df_px = stock.get_market_ohlcv_by_date(
                    latest.strftime('%Y%m%d'), latest.strftime('%Y%m%d'), c)
                if df_px is not None and len(df_px) > 0:
                    px_map[c] = float(df_px.iloc[-1]['종가'])
                else:
                    fail_codes.append(c)
            except Exception as e:
                fail_codes.append(c)
                print(f'    fetch fail {c}: {str(e)[:60]}')
            time.sleep(0.1)
        if fail_codes:
            print(f'    ⚠️ price fetch fail: {len(fail_codes)} codes: {fail_codes[:5]}')
        df_log, updates, closes = update_open_positions(df_log, px_map, latest)
        print(f'[3] mtm: updates={updates}, closes={closes}, OPEN→{(df_log["status"]=="OPEN").sum()}')
    else:
        updates, closes = 0, 0
        print('[3] no OPEN positions')

# === 5. new entry signal (inbox check) ===
sig_path = INBOX_DIR / f'long_signals_{latest.strftime("%Y%m%d")}.json'
new_entries = 0
if sig_path.exists():
    sig = json.loads(sig_path.read_text(encoding='utf-8'))
    entry_date = pd.Timestamp(sig['entry_date'])
    codes = sig['codes']
    print(f'[4] inbox signal: entry={entry_date.date()}, n_codes={len(codes)}')

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
            elif df_px is not None and len(df_px) == 1:
                # entry == latest 동일일 시
                px_map_new[c] = {
                    'entry_px': float(df_px.iloc[0]['종가']),
                    'mtm_px':   float(df_px.iloc[0]['종가']),
                }
        except Exception as e:
            print(f'    fetch fail {c}: {str(e)[:60]}')
        time.sleep(0.1)

    df_new = append_oos_entries(
        entry_date=entry_date, mtm_date=latest,
        codes=codes, px_map=px_map_new, df_ax=df_ax,
        side=sig.get('side', 'LONG'),
        hold_target=sig.get('hold_target', HOLD_LONG),
        notes=f'inbox {entry_date.date()} @ 19:30 KST',
    )
    df_log = pd.concat([df_log, df_new], ignore_index=True)
    new_entries = len(df_new)
    print(f'    new entries: {new_entries} rows (5 variants × {len(codes)} codes)')
else:
    print(f'[4] no signal in inbox ({sig_path.name})')

# === 6. save realized_log ===
df_log.to_parquet(LOG_PATH, index=False)
print(f'[5] saved: {LOG_PATH} ({len(df_log)} rows, +{len(df_log)-n_orig})')

# === 7. portfolio summary ===
summ = portfolio_metrics(df_log)
print(f'\n[6] portfolio summary:')
print(summ.to_string(index=False))

# === 8. Path D axis eval (별도 무관 로깅) ===
try:
    from glob import glob
    vk = pd.read_parquet('data/raw/web/vkospi_ohlc_94y.parquet')
    ke = pd.read_parquet('data/raw/web/12008/kospi_excl_etf_94y.parquet')
    ki = pd.read_parquet('data/raw/web/12008/kospi_incl_etf_94y.parquet')
    for d in (vk, ke, ki): d['일자'] = pd.to_datetime(d['일자'])

    common_dates = sorted(set(vk['일자']) & set(ke['일자']) & set(ki['일자']))
    if latest in common_dates:
        inst_cols = ['금융투자','보험','투신','사모','은행','기타금융','연기금 등']
        def z60(s): return (s - s.rolling(60, min_periods=60).mean()) / s.rolling(60, min_periods=60).std()
        vk_i = vk.set_index('일자').reindex(common_dates)
        ke_i = ke.set_index('일자').reindex(common_dates)
        ki_i = ki.set_index('일자').reindex(common_dates)
        m2 = z60(vk_i['등락률'].astype(float))
        m8 = z60(ke_i[inst_cols].sum(axis=1))
        fi = ki_i['외국인'].astype(float) + ki_i['기타외국인'].astype(float)
        fe = ke_i['외국인'].astype(float) + ke_i['기타외국인'].astype(float)
        m6 = z60(fi - fe)
        axis_t1 = pd.DataFrame({'M2': m2, 'M8': m8, 'M6': m6}).shift(1)

        if latest in axis_t1.index:
            r = axis_t1.loc[latest]
            cm2 = bool(r['M2'] > -1.0)
            cm8 = bool(r['M8'] >  0.0)
            cm6 = bool(r['M6'] <  0.0)
            sp  = cm2 and cm8 and cm6

            old = pd.read_parquet(PATHD_LOG) if PATHD_LOG.exists() else pd.DataFrame()
            new_row = pd.DataFrame([{
                'entry_date': latest.date().isoformat(),
                'M2': float(r['M2']), 'M8': float(r['M8']), 'M6': float(r['M6']),
                'cond_M2_gt_-1.0': cm2, 'cond_M8_gt_0.0': cm8, 'cond_M6_lt_0.0': cm6,
                'strict_pass': sp, 'decision': 'LONG' if sp else 'NO_TRADE',
            }])
            merged = pd.concat([old[old.get('entry_date', pd.Series()) != new_row['entry_date'].iloc[0]],
                                new_row], ignore_index=True) if len(old) > 0 else new_row
            merged = merged.sort_values('entry_date').reset_index(drop=True)
            merged.to_parquet(PATHD_LOG)
            merged.to_csv(str(PATHD_LOG).replace('.parquet','.csv'), index=False)
            print(f'\n[7] Path D eval: {latest.date()} decision={"LONG" if sp else "NO_TRADE"} '
                  f'(M2={r["M2"]:+.2f}/M8={r["M8"]:+.2f}/M6={r["M6"]:+.2f})')
except Exception as e:
    print(f'\n[7] Path D eval skip: {str(e)[:80]}')

# === 9. git commit + push ===
files_to_add = [str(LOG_PATH)]
if PATHD_LOG.exists():
    files_to_add.append(str(PATHD_LOG))
    files_to_add.append(str(PATHD_LOG).replace('.parquet', '.csv'))

if updates > 0 or new_entries > 0 or closes > 0:
    subprocess.run(['git','add'] + files_to_add, check=False)
    msg = (f'MSM daily {latest.date()} @ KST: '
           f'mtm u={updates} c={closes} new={new_entries}')
    r = subprocess.run(['git','commit','-m', msg], capture_output=True, text=True)
    if 'nothing to commit' not in r.stdout.lower():
        r2 = subprocess.run(['git','push','origin','HEAD'], capture_output=True, text=True)
        push_ok = 'OK' if r2.returncode == 0 else r2.stderr[:200]
        print(f'\n[8] commit + push: {push_ok}')
    else:
        print(f'\n[8] nothing to commit')
else:
    # Path D eval만 변경 시
    if PATHD_LOG.exists():
        subprocess.run(['git','add'] + files_to_add, check=False)
        r = subprocess.run(['git','commit','-m', f'MSM Path D eval {latest.date()}'],
                            capture_output=True, text=True)
        if 'nothing to commit' not in r.stdout.lower():
            r2 = subprocess.run(['git','push','origin','HEAD'], capture_output=True, text=True)
            print(f'\n[8] Path D push: {"OK" if r2.returncode==0 else r2.stderr[:200]}')

head = subprocess.run(['git','rev-parse','--short','HEAD'],
                      capture_output=True, text=True).stdout.strip()
print(f'\n[9] HEAD={head}  완료시각={datetime.now(KST).strftime("%H:%M:%S")} KST')
print('============================================================')
