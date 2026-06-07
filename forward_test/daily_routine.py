# === MSM Daily Routine — paste & run (idempotent) ===
# 사용법: setup 셀 실행 후 이 셀 paste & run. TODAY 자동 = KST 오늘.
import os, subprocess, json, pandas as pd, numpy as np
from pathlib import Path
from datetime import datetime, timezone, timedelta

REPO = '/content/choonsimi-msm'; os.chdir(REPO)
KST  = timezone(timedelta(hours=9))
TODAY = pd.Timestamp(datetime.now(KST).date())   # KST 오늘
print(f'[daily] TODAY (KST) = {TODAY.date()}')

# --- A. raw 갱신 (수동 push 가정: 본 template은 갱신 X, 사실 사용만) ---
# kospi_excl/incl/vkospi 최신 push는 별도 셀에서. 여기선 last raw date 확인.
vk = pd.read_parquet('data/raw/web/vkospi_ohlc_94y.parquet')
ke = pd.read_parquet('data/raw/web/12008/kospi_excl_etf_94y.parquet')
ki = pd.read_parquet('data/raw/web/12008/kospi_incl_etf_94y.parquet')
for df in (vk, ke, ki): df['일자'] = pd.to_datetime(df['일자'])
last_raw = min(vk['일자'].max(), ke['일자'].max(), ki['일자'].max())
print(f'[daily] last raw date = {last_raw.date()}')

# --- B. biz_full + axis 60d z ---
eq = pd.read_parquet('data/sim/v2_gamma_best.parquet')
biz_in = sorted(eq['date'].tolist())
common = sorted((set(vk['일자']) & set(ke['일자']) & set(ki['일자'])) - set(biz_in))
biz_full = sorted(biz_in + common)
print(f'[daily] biz_full = {biz_full[0].date()}~{biz_full[-1].date()} (n={len(biz_full)})')

inst_cols = ['금융투자','보험','투신','사모','은행','기타금융','연기금 등']
def z60(s): return (s - s.rolling(60, min_periods=60).mean()) / s.rolling(60, min_periods=60).std()
vk_i = vk.set_index('일자').reindex(biz_full)
ke_i = ke.set_index('일자').reindex(biz_full)
ki_i = ki.set_index('일자').reindex(biz_full)

m2 = z60(vk_i['등락률'].astype(float))
m8 = z60(ke_i[inst_cols].sum(axis=1))
fi = ki_i['외국인'].astype(float) + ki_i['기타외국인'].astype(float)
fe = ke_i['외국인'].astype(float) + ke_i['기타외국인'].astype(float)
m6 = z60(fi - fe)
axis = pd.DataFrame({'M2_z_vkospi_delta': m2, 'M8_z_inst_kospi': m8, 'M6_z_foreign_kospi_etf': m6})
axis.index.name = 'date'
axis_t1 = axis.shift(1)

# --- C. Path D 판정: 가장 최근 raw 영업일 entry 기준 ---
# entry = last_raw (raw가 그날 close 포함). T-1 axis = biz_prev(last_raw).
entry = last_raw
if entry not in axis_t1.index:
    print(f'[daily] {entry.date()} not in biz_full — SKIP'); raise SystemExit
r = axis_t1.loc[entry]
cm2 = bool(r['M2_z_vkospi_delta'] > -1.0)
cm8 = bool(r['M8_z_inst_kospi']   >  0.0)
cm6 = bool(r['M6_z_foreign_kospi_etf'] <  0.0)
sp  = cm2 and cm8 and cm6
print(f'[daily] entry={entry.date()}  M2={r["M2_z_vkospi_delta"]:+.3f}({cm2})  '
      f'M8={r["M8_z_inst_kospi"]:+.3f}({cm8})  M6={r["M6_z_foreign_kospi_etf"]:+.3f}({cm6})  '
      f'strict_pass={sp}  decision={"LONG" if sp else "NO_TRADE"}')

# --- D. log append (idempotent: entry_date PK upsert) ---
log_path = Path('forward_test/axis_oos/pathD_eval_oos.parquet')
old = pd.read_parquet(log_path) if log_path.exists() else pd.DataFrame()
new_row = pd.DataFrame([{
    'entry_date'     : entry.date().isoformat(),
    'axis_biz_T-1'   : axis_t1.loc[entry].name if False else (axis.index[axis.index.get_indexer([entry])[0]-1]).date().isoformat(),
    'M2': float(r['M2_z_vkospi_delta']),
    'M8': float(r['M8_z_inst_kospi']),
    'M6': float(r['M6_z_foreign_kospi_etf']),
    'cond_M2_gt_-1.0': cm2, 'cond_M8_gt_0.0': cm8, 'cond_M6_lt_0.0': cm6,
    'strict_pass': sp, 'decision': 'LONG' if sp else 'NO_TRADE',
}])
merged = pd.concat([old[old['entry_date'] != new_row['entry_date'].iloc[0]], new_row], ignore_index=True)
merged = merged.sort_values('entry_date').reset_index(drop=True)
merged.to_parquet(log_path)
merged.to_csv(str(log_path).replace('.parquet','.csv'), index=False)
print(f'[daily] log appended/upserted: {log_path}  total rows={len(merged)}')
print(merged.tail(5).to_string(index=False))

# --- E. commit & push ---
subprocess.run(['git','add','forward_test/axis_oos/pathD_eval_oos.parquet',
                'forward_test/axis_oos/pathD_eval_oos.csv'], cwd=REPO, check=False)
msg = f'MSM daily: Path D eval {entry.date().isoformat()}'
c = subprocess.run(['git','commit','-m',msg], cwd=REPO, capture_output=True, text=True)
p = subprocess.run(['git','push'], cwd=REPO, capture_output=True, text=True)
print(f'[daily] commit: {(c.stdout or c.stderr).strip()[-120:]}')
print(f'[daily] push  : {(p.stdout or p.stderr).strip()[-120:]}')
