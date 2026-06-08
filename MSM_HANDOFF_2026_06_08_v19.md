# MSM 핸드오프 v19 — STATE freeze (M17 front-month) + K3 진입 준비

**작성일**: 2026-06-08 (KST, MSM 세션 #14 종결)
**대상 repo**: stanleyim/choonsimi-msm
**최신 commit**: 195750f — MSM v19: extract_basis_front for M17 (front-month, B' rule)
**상태**: ★ STATE freeze 완료, K3 BLOCK 해제, 다음 세션 즉시 K3 9.4y backfill 진입 가능
**다음 작업**: K3 9.4y backfill (2017-01-02 ~ 2024-07-07, ~1,830 dates, ~3~5h)

---

## 0. 절대 원칙 (v18 §0 + v19 신규)

1. §1 추측 금지 (검증 없는 단정 금지, 모든 결론은 코드/데이터로 증명)
2. §6 3번 검토 (정확성 + 사고 가능성 + 안전장치)
3. §7 옵션 → 형 결정 → 실행 (큰 결정만 옵션 송부, 기술 세부는 자체 실행)
4. §13 매 단계 commit/push (GitHub = sole ground truth)
5. MSM = choonsimi-premium 독립 (v10c 6/26 freeze)
6. 단일 셀 통합 코드 (tablet 환경)
7. Long-running (30분+) 작업 시 batch + auto-push 의무
8. **v19 신규**: STATE 정의 변경은 forward test가 발견한 진실에 기반. legacy ≠ SSOT 발견 시 4-필드 검증(legacy rule / SSOT rule / divergence / intent) 필수

---

## 1. ★ LOCKED VALUES

### 1-1. v12 LOCK (변경 없음)
- v12 commit: 559a65e
- LONG: NEUTRAL × bot z_ell top 10, hold 15d, weight 1/10
- SHORT: SHOCK × bot score top 10, hold 5d, weight 1/10
- T4 Control: -20% DD / 0.5x exposure / -10% recovery
- In-sample 성과: CAGR 16.48%, Sharpe 0.686, MDD -33.13%, GROSS Sh 1.67
- 기간: 2017-01-02 ~ 2026-06-02

### 1-2. v18 LOCK (변경 없음)
- KRX OpenAPI 10 endpoint 검증 완료
- 16 axes (M1~M11, M15~M19, M12-M14 보류)
- legacy axis_raw_17axis.parquet: 463 rows (2024-07-08 ~ 2026-06-05)

### 1-3. v19 NEW LOCK ★
- **scripts/build_axis.py SSOT 확정** (HEAD 195750f)
- **M17 selection rule**: front-month (deterministic, `min(yyyymm)` over PROD_NM='변동성지수 선물' AND MKT_NM='정규' AND NOT SP)
- **M15/M16 selection rule**: max(ACC_TRDVOL) (현행 유지)
- **5월 cross-val 19/19 PASS** (2025-05-02 ~ 2025-05-30)
- **API call**: 4 endpoints (drvprod, bon, fut, opt) × 0.2s sleep + KRX OpenAPI retry 3회 내장

---

## 2. ★ 본 세션 (#14) 진행 내역

### 2-1. Setup verification (HEAD 7b6784a)
- legacy 463 rows / 12008 flow 2309 rows / KRX_API_KEY OK / RAM 12.4GB free
- 전 항목 PASS

### 2-2. Cross-val 1차 (2025-05 19 dates)
- 결과: 17/19 PASS (5/12, 5/13 M17 FAIL)
- 5/12: legacy=0.00, SSOT=0.85 (diff=0.85)
- 5/13: legacy=0.34, SSOT=1.14 (diff=0.80)
- K3 BLOCKED

### 2-3. M17 진단 (D 추적, 4 phase)

#### Phase 1: raw response 분석
- r_fut는 list (dict 아님). 5/12 cands=11, F202505 vol=2 (basis=0), F202506 vol=4 (basis=0.85)
- SSOT (max_vol) → F202506 (0.85). legacy → F202505 (0.00)

#### Phase 2: git 추적
- scripts/build_axis.py = 오늘 7b6784a 신규 (1 commit). 이전 코드 없음
- legacy 463 rows = H2 backfill 10 batch (0756575 ~ fb8ea7c)
- engine.py / daily_run.py에 basis 로직 없음

#### Phase 3: 결정적 단서 발견
- `data/raw/web/vkospi_basis_94y.parquet` (4a0825c upload)
- column: 일자/종목코드/종목명/선물가격/현물가격/**시장베이시스**
- single row/date, 종목명 = 'F YYYYMM' (front month)
- 5/12 시장베이시스=0.00, 5/13=0.34 → **legacy M17과 100% 일치**
- 결론: legacy는 web parquet 기반 (front month), SSOT는 KRX OpenAPI 기반 (max_vol). **다른 system**

#### Phase 4: 만기 전환 + 후보 평가
- VKOSPI 5월물 만기 전환: 5/13 → 5/14 (legacy parquet 기준)
- K200 5월물 만기 5/8 — vol 압도적 (185k) → max_vol=front 자동 매칭 → M15 5/8 PASS
- 3 후보 정의:
  - A: `min(yyyymm) where yyyymm >= basMM`
  - B: `min(yyyymm)` 전체
  - C: `vol>0 AND min(yyyymm)`
- 5월 19 dates 시뮬 → A/B/C 모두 19/19 PASS
- 분기점 5/14에서 KRX가 만기월 자동 제거 → 3 후보 결과 동일

### 2-4. B' 확정 (형 결정)
- 선택 rule: **M17 = front (legacy 유지), M15/M16 = max_vol (SSOT 유지)**
- 후보 B 채택 (가장 단순, 5월 19/19 PASS, legacy 동작과 직접 정합)
- 핵심 논리: VKOSPI 저유동성 → vol 기반 선택은 microstructure noise / front month는 deterministic + state continuity 보장

### 2-5. SSOT 수정 + 검증 + commit
- backup → anchor verify → extract_basis_front 정의 inject → m17 호출 rewire → reload
- 5월 19/19 PASS 재확인 (127.9s)
- commit 195750f, push 완료
- HEAD 7b6784a → **195750f**

---

## 3. ★ M17 SSOT 정의 (v19 LOCKED)

### 3-1. 코드 (scripts/build_axis.py)

```python
def extract_basis_front(rows, prod_nm):
    """B': front-month basis (deterministic, vol-independent).
    Selection rule: min(yyyymm) over PROD_NM==prod_nm AND MKT_NM=='정규' AND not SP.
    Legacy alignment: web/vkospi_basis_94y.parquet (single row/date).
    NaN if cls or spot missing."""
    import re as _re
    cands = []
    for r in (rows or []):
        if r.get("PROD_NM") != prod_nm: continue
        if r.get("MKT_NM") != "정규": continue
        isu = r.get("ISU_NM") or ""
        if "SP" in isu: continue
        m = _re.search(r"F\s*(\d{6})", isu)
        if not m: continue
        cands.append((r, int(m.group(1))))
    if not cands:
        return float("nan")
    nearest, _ = min(cands, key=lambda x: x[1])
    cls, spot = _f(nearest.get("TDD_CLSPRC")), _f(nearest.get("SPOT_PRC"))
    if np.isnan(cls) or np.isnan(spot):
        return float("nan")
    return cls - spot
```

### 3-2. STATE 정의

```
M17_t = basis(min(yyyymm))          # deterministic, front-month
M15_t = basis(argmax(ACC_TRDVOL))   # stochastic, active contract
M16_t = basis(argmax(ACC_TRDVOL))   # stochastic, active contract
```

### 3-3. 성질

| 속성 | M17 (front) | M15/M16 (max_vol) |
|---|---|---|
| Selection | deterministic | stochastic |
| Continuity | 보장 (roll 시 다음 contract 자연 전환) | KRX 만기 처리에 의존 |
| Information | 만기 수렴 시 0 (regime feature) | active contract signal |
| Noise stability | 안정 | vol 적은 종목 (VKOSPI)에서 불안정 |
| Anomaly | vol=0인 만기월 → NaN | - |

### 3-4. Anomaly diagnostic (state 비개입)

front 만기월 vol=0 → flag만 별도 log. selection rule 분기 없음.

---

## 4. ★ K3 진입 패키지 (다음 세션)

### 4-1. 범위

- 기간: 2017-01-02 ~ 2024-07-07
- 추정 dates: ~1,830 영업일
- API call/date: 4 endpoints × 0.2s + response time
- 추정 시간: **~3~5h**
- Colab timeout 12h → 안전 마진 충분
- batch 50 + auto-push (single point of failure 없음)
- resume capability (progress.json)

### 4-2. 영업일 source 결정 (다음 세션 첫 결정)

| 옵션 | 방법 | 장단점 |
|---|---|---|
| **A** | pykrx `get_index_ohlcv('20170102','20240707','1001')` index | legacy가 사용했을 가능성. 단, KRX 영업일 ≠ index 거래일 가능성 |
| **B** | KRX OpenAPI 자연 skip (응답 빈 list → skip) | 정확하나 비영업일도 API call 발생 (API 부담 ↑) |
| **C** | data/raw/active/ohlcv parquet에서 unique dates 추출 | 이미 확보된 한국 영업일 source. 가장 안전 |

**Claude 권장**: **C** (이미 보유한 데이터, 별도 API 부담 없음, 9.4y 검증된 source)

### 4-3. K3 실행 cell (paste & run 준비)

```python
# MSM Phase 4 K3 — 9.4y axis backfill (2017-01-02 ~ 2024-07-07)
# batch 50 + auto-push + resume capability
# ★ Setup cell (§6-1) 이후 실행
import time, json, gc, numpy as np, pandas as pd
from pathlib import Path
import subprocess

# === 0. config ===
START_DATE   = '2017-01-02'
END_DATE     = '2024-07-07'   # legacy 시작일(2024-07-08) 직전까지
BATCH_SIZE   = 50
SLEEP_PER_CALL = 0.2
PROGRESS_FILE = Path('data/state/axis_raw/k3_progress.json')
FAIL_FILE     = Path('data/state/axis_raw/k3_fail_log.json')
TARGET_FILE   = Path('data/state/axis_raw/axis_raw_17axis.parquet')

# === 1. 영업일 list (option C: ohlcv parquet 기반) ===
from glob import glob
ohlcv_files = sorted(glob('data/raw/active/ohlcv/year=*.parquet'))
all_dates = set()
for f in ohlcv_files:
    df_tmp = pd.read_parquet(f, columns=['date'])
    all_dates.update(pd.to_datetime(df_tmp['date']).dt.date.unique())
biz_dates = sorted([d for d in all_dates
                    if pd.Timestamp(d) >= pd.Timestamp(START_DATE)
                    and pd.Timestamp(d) <= pd.Timestamp(END_DATE)])
print(f'✓ K3 target biz days: {len(biz_dates)}')
print(f'  range: {biz_dates[0]} ~ {biz_dates[-1]}')

# === 2. resume ===
if PROGRESS_FILE.exists():
    progress = json.loads(PROGRESS_FILE.read_text())
    completed = set(pd.to_datetime(d).date() for d in progress.get('completed', []))
    print(f'✓ resume: {len(completed)} dates already done')
else:
    progress = {'completed': []}
    completed = set()

if FAIL_FILE.exists():
    fail_log = json.loads(FAIL_FILE.read_text())
else:
    fail_log = {'fails': []}
fail_dates = set(pd.to_datetime(d).date() for d in
                 [x['date'] for x in fail_log.get('fails', [])])

# todo = target - completed - fail (recovered 만 재시도하려면 fail 제외)
todo = [d for d in biz_dates if d not in completed]
print(f'✓ todo: {len(todo)} dates (already failed {len(fail_dates)} dates excluded? — manual: 포함됨)')

# === 3. existing axis_raw load ===
if TARGET_FILE.exists():
    df_existing = pd.read_parquet(TARGET_FILE)
    df_existing['date'] = pd.to_datetime(df_existing['date'])
    print(f'✓ existing axis_raw: {df_existing.shape}')
else:
    df_existing = pd.DataFrame(columns=COL_ORDER)
    print('✓ no existing — start fresh')

# === 4. batch loop ===
auth = os.environ['KRX_API_KEY']
new_rows = []
t_start = time.time()
batch_num = 0

for i, d in enumerate(todo, 1):
    d_ts = pd.Timestamp(d)
    try:
        row = build_axis_row(d_ts, df_excl, df_incl, df_kq,
                             auth, sleep=SLEEP_PER_CALL)
    except Exception as e:
        fail_log['fails'].append({'date': str(d), 'reason': f'EXC:{type(e).__name__}',
                                   'msg': str(e)[:120]})
        print(f'  [{i:5d}/{len(todo)}] {d} EXC: {type(e).__name__}')
        continue

    if row is None:
        fail_log['fails'].append({'date': str(d), 'reason': 'FETCH_NONE'})
        if i % 20 == 0:
            print(f'  [{i:5d}/{len(todo)}] {d} FETCH_NONE')
        continue

    new_rows.append(row)
    progress['completed'].append(str(d))

    # batch flush
    if len(new_rows) >= BATCH_SIZE or i == len(todo):
        batch_num += 1
        df_batch = pd.DataFrame(new_rows)
        df_batch['date'] = pd.to_datetime(df_batch['date'])
        df_combined = pd.concat([df_existing, df_batch], ignore_index=True)
        df_combined = df_combined.drop_duplicates('date').sort_values('date').reset_index(drop=True)
        df_combined = df_combined[COL_ORDER]
        df_combined.to_parquet(TARGET_FILE, index=False)
        df_existing = df_combined
        new_rows = []

        # progress + fail save
        PROGRESS_FILE.write_text(json.dumps(progress, indent=2))
        FAIL_FILE.write_text(json.dumps(fail_log, indent=2))

        # git push
        elapsed = time.time() - t_start
        n_done = len(progress['completed']) - len(completed)
        eta = elapsed / max(n_done, 1) * (len(todo) - i)
        msg = (f'MSM K3 batch {batch_num}: '
               f'total {len(df_existing)} dates, fail {len(fail_log["fails"])}')
        subprocess.run(['git', 'add', str(TARGET_FILE), str(PROGRESS_FILE),
                        str(FAIL_FILE)], check=True)
        r = subprocess.run(['git', 'commit', '-m', msg],
                           capture_output=True, text=True)
        if r.returncode == 0:
            rp = subprocess.run(['git', 'push', 'origin', 'HEAD'],
                                capture_output=True, text=True)
            push_ok = '✓' if rp.returncode == 0 else f'✗ {rp.stderr[:80]}'
        else:
            push_ok = f'no-commit ({r.stdout[:60]})'

        print(f'  [batch {batch_num:3d}] '
              f'progress {len(df_existing)}/{len(biz_dates)} '
              f'fail {len(fail_log["fails"])} '
              f'elapsed {elapsed/60:.1f}m '
              f'eta {eta/60:.1f}m  push {push_ok}')

        gc.collect()

total_elapsed = time.time() - t_start
print(f'\n{"="*60}')
print(f'K3 완료: {len(df_existing)} rows, fail {len(fail_log["fails"])}')
print(f'총 소요: {total_elapsed/60:.1f}m')
print(f'HEAD 확인 → 다음 세션 v20 핸드오프')
print(f'{"="*60}')
```

### 4-4. K3 후 확인사항

- axis_raw_17axis.parquet 총 rows ≈ 463 (legacy) + ~1,830 (K3) - overlap = **~2,290 rows 예상**
- fail dates pattern 분석 (legacy 37 fail dates와 유사한지)
- _n_valid 분포 확인 (16/16, 15/16, 등)
- date range: 2017-01-02 ~ 2026-06-05 (9.4y full)

---

## 5. ★ 차후 작업일정

### 5-1. 다음 세션 (즉시)

| Step | 작업 | 시간 |
|---|---|---|
| 1 | Setup cell (§6-1) | ~40s |
| 2 | K3 영업일 source 결정 (A/B/C) — Claude 옵션 송부 | ~즉시 |
| 3 | K3 9.4y backfill 실행 | ~3~5h |
| 4 | K3 결과 sanity (fail pattern, _n_valid 분포) | ~5분 |
| 5 | v20 handoff commit | ~5분 |

### 5-2. K3 완료 후 (별도 세션 권장)

| Step | 작업 | 시간 |
|---|---|---|
| 6 | **v4 STEP 2 REGIME** (rule-based) | ~10분 |
|   | - shock: M1 > 40 또는 quantile 90% | |
|   | - trend: \|M5/M7 net flow\| 임계 + \|M2\| 작음 | |
|   | - range: \|M2\| 작음 + \|basis\| 작음 | |
|   | - transition: else | |
| 7 | **v4 STEP 3** TRANSITION (kNN k=50) | ~20분 |
|   | - normalize: robust (median/IQR) | |
|   | - Edge(S_t) = mean(r_{t+1} over neighbors) | |
|   | - r_{t+1} source: state_v2 portfolio return | |
| 8 | **v4 STEP 4** EDGE FIELD + TRADEABLE | ~10분 |
| 9 | v4 vs v12 비교 (in-sample) | ~10분 |

### 5-3. 후순위 (잔존 issue)

- M12-M14 보류 axes (KRX OpenAPI 미커버 — 별도 source 필요)
- choonsimi-premium v10c 6/26 forward test 결과 review
- dual-engine 검토 (v10c Core + Hyper Momentum mode)
- Daily routine 자동화 (forward_test/daily_routine.py 확장)
- VKOSPI 만기월 vol=0 anomaly diagnostic (현재 STATE 비개입, 별도 분석)

---

## 6. ★ 다음 세션 진입 패키지

### 6-1. Setup cell (paste & run, ~40s)

```python
# MSM Phase 4 Session #15 — Setup Cell
# v19 STATE freeze. K3 진입 준비.
import os, subprocess, shutil, time, sys
from pathlib import Path

t0 = time.time()
REPO = '/content/choonsimi-msm'
EXPECTED_HEAD_PREFIX = '195750f'   # v19 ★

from google.colab import userdata
GH = userdata.get('GH_TOKEN')
assert GH, 'GH_TOKEN 필요'

if Path(REPO).exists():
    shutil.rmtree(REPO)
url = f'https://x-access-token:{GH}@github.com/stanleyim/choonsimi-msm.git'
r = subprocess.run(['git', 'clone', url, REPO], capture_output=True, text=True)
assert r.returncode == 0, f'clone 실패: {r.stderr}'
os.chdir(REPO)

head = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'],
                      capture_output=True, text=True).stdout.strip()
assert head.startswith(EXPECTED_HEAD_PREFIX), f'HEAD 불일치: {head}'
print(f'✓ clone HEAD={head}')

subprocess.run([sys.executable, '-m', 'pip', 'install', '-q',
                'pyarrow', 'pandas', 'numpy', 'psutil', 'pykrx', 'requests'],
               check=True)
import pyarrow, pandas as pd, numpy as np, psutil, requests
print(f'✓ packages')

for k in ['KRX_ID', 'KRX_PW', 'ECOS_API_KEY', 'KRX_API_KEY']:
    try:
        v = userdata.get(k)
        if v:
            os.environ[k] = v
    except Exception:
        pass
assert os.environ.get('KRX_API_KEY'), 'KRX_API_KEY secret 필요'
print(f'✓ env')

subprocess.run(['git', 'config', 'user.email', 'msm@stanleyim.local'],
               check=True, cwd=REPO)
subprocess.run(['git', 'config', 'user.name', 'stanleyim'],
               check=True, cwd=REPO)

sys.path.insert(0, 'scripts')
from build_axis import (build_axis_row, load_flow_parquets,
                         AXIS_KEYS, COL_ORDER,
                         extract_basis, extract_basis_front)
print(f'✓ build_axis v19 SSOT (extract_basis_front available)')

df_excl, df_incl, df_kq = load_flow_parquets()
df_axis = pd.read_parquet('data/state/axis_raw/axis_raw_17axis.parquet')
print(f'✓ 12008 loaded: {len(df_excl)}/{len(df_incl)}/{len(df_kq)}')
print(f'✓ axis_raw legacy: {df_axis.shape}')
print(f'  date range: {df_axis["date"].min().date()} ~ {df_axis["date"].max().date()}')

mem = psutil.virtual_memory()
print(f'\nRAM: {mem.used/1e9:.1f}/{mem.total/1e9:.1f} GB (free {mem.available/1e9:.1f})')
print(f'준비 완료 {time.time()-t0:.1f}s')

print(f'''
============================================================
다음 작업:
1. K3 영업일 source 결정 (A: pykrx / B: API natural / C: ohlcv parquet)
2. K3 9.4y backfill (~1,830 dates, ~3~5h, batch 50 + auto-push)
3. K3 sanity → v20 handoff
============================================================
''')
```

### 6-2. 첫 메시지 (Claude에게)

```
MSM Phase 4 세션 #15.
HEAD = 195750f (v19, M17 front-month freeze).

상태:
- STATE freeze 완료 (M17 = extract_basis_front, M15/M16 = max_vol)
- 5월 cross-val 19/19 PASS
- legacy 463 rows 보존 (2024-07-08 ~ 2026-06-05)
- K3 BLOCK 해제

다음 작업:
1. K3 영업일 source 결정
2. K3 9.4y backfill (2017-01-02 ~ 2024-07-07, ~1,830 dates, ~3~5h)
3. v20 handoff

§1 추측 X, §6 3축, §7 옵션→형 결정→실행, 단일 셀.
옵션 송부 최소화 (큰 결정만), 기술 세부는 자체 판단 실행 후 보고.

먼저 Setup cell 검증 결과 송부.
```

### 6-3. Claude 첫 응답 할 것

1. v19 §0 절대 원칙 정독
2. v19 §1 LOCKED VALUES 확인 (특히 §1-3 v19 NEW LOCK)
3. v19 §3 M17 SSOT 정의 확인
4. v19 §4 K3 패키지 확인
5. Setup cell 출력 검증 (HEAD=195750f 확정)
6. 영업일 source 옵션 송부 (A/B/C) — 권장 C
7. 형 GO C 시 K3 cell 즉시 송부 (§4-3 그대로 + setup-specific 수정)
8. K3 진행 (~3~5h, batch 50 auto-push)

---

## 7. 파일 인벤토리 (commit 195750f 기준)

```
choonsimi-msm/
├── scripts/
│   └── build_axis.py            ★ v19 SSOT (5,956 chars, extract_basis_front 추가)
├── MSM_HANDOFF_2026_06_08_v19.md ← 본 문서
├── MSM_HANDOFF_2026_06_08_v18.md
├── MSM_HANDOFF_2026_06_07_v17.md
├── (v15, v16, v14, v13, v12 …)
├── engine.py
├── daily_run.py
├── msm_data_ingestion.ipynb
├── msm_data_supplement.ipynb
├── msm_state_vector.ipynb
├── data/
│   ├── state/
│   │   ├── axis_raw/
│   │   │   ├── axis_raw_17axis.parquet     (463 rows legacy)
│   │   │   ├── fail_log.json               (legacy 37 fails)
│   │   │   └── (K3 후: k3_progress.json + k3_fail_log.json 추가)
│   │   ├── state_vector_v2/year=*.parquet
│   │   ├── regime/, transition/, tradeable/, edge_v2/, edge_v3/
│   │   └── axis_v3/ (sweep candidates, redundancy 검증용)
│   ├── raw/
│   │   ├── web/
│   │   │   ├── vkospi_basis_94y.parquet   ★ M17 legacy source (front-month)
│   │   │   ├── kospi200_basis_94y.parquet ★ M15 web parquet (max_vol과 정합)
│   │   │   ├── kosdaq150_basis_94y.parquet ★ M16 web parquet
│   │   │   ├── 12008/{kospi_excl_etf, kospi_incl_etf, kosdaq}_94y.parquet
│   │   │   └── (etf_investor_flow, krx_bond_index, *_pc, vkospi_ohlc)
│   │   ├── active/{flow, foreign, ohlcv, ohlcv_adj}/year=*.parquet
│   │   ├── delisted/...
│   │   └── short/{balance, volume}/q_*.parquet
│   └── sim/, sim_v3/
├── forward_test/
│   ├── baseline.json, README.md
│   ├── daily_routine.py, daily_run.py
│   ├── templates/daily_run_cell.py
│   ├── axis_oos/, log/, metrics/, realized/, state/, schema/
└── README.md, STEP8_PROGRESS.md, MSM_WORKPLAN_v1.md, v2.md, PREF_DIAGNOSIS_2026_06_05.md
```

---

## 8. 본 세션 (#14) commit 이력

- **195750f** MSM v19: extract_basis_front for M17 (front-month, B' rule). Selection: min(yyyymm) deterministic. M15/M16=max_vol unchanged. May 2025 cross-val 19/19 PASS. STATE freeze ready.
- (이전) 7b6784a MSM v18: scripts/build_axis.py — SSOT for 16 axes (sample-validated)

---

## 9. ★ 실수 누적 (v18 #1~#68 + v19 신규)

#69: **5월 cross-val 1차 17/19 PASS → "FAIL 차단" 판정 시 원인을 추측하지 않고 raw response 직접 dump로 즉각 진단했음.** front month vs max_vol 차이를 4 phase (raw → git → web parquet → 후보 시뮬)로 검증. v18 §0 #1 "추측 금지"를 본 세션에서 강하게 준수. 재발 방지: cross-val FAIL 시 raw level diff dump부터 시작.

#70: **legacy axis_raw 생성 코드 미보존 (H2 backfill 시점 build_axis.py 없음).** scripts/build_axis.py 7b6784a 신규 = legacy 함수와 별개. legacy = web parquet pre-built basis lookup, SSOT = KRX OpenAPI 직접 계산. 두 source가 다른 system. 재발 방지: backfill에 사용된 코드는 반드시 commit + 스크립트 보존 (notebook cell만 사용 시 추후 검증 불가).

#71: **STATE 정의 = signal fidelity + noise stability + deterministic continuity.** "max_vol = active contract"는 K200 같은 고유동성 종목에서만 valid. VKOSPI는 vol 자체가 stochastic noise. STATE의 invariance를 위해 deterministic rule (front-month) 우위. 재발 방지: 새 axis 추가 시 selection rule의 deterministic 여부 명시.

#72: **handoff v18 문서에 "nearest" 키워드 명시 vs 코드는 max_vol** — 문서/코드 의미 불일치를 본 세션에서 발견. v19부터 handoff 문서의 axis 정의에 selection rule 명시적 코드 (e.g. "min(yyyymm)") 포함. 재발 방지: axis 정의 = 자연어 + 코드 식 둘 다 명시.

---

## 10. 핵심 한 줄

v18 → v19: forward test가 발견한 진실 (M17 우선주 외 새로운 case — VKOSPI roll-over noise)을 즉시 진단 → STATE 정의를 deterministic하게 freeze. 5월 19/19 PASS, K3 BLOCK 해제. 다음 세션 = K3 9.4y backfill (~3~5h, batch 50 + auto-push).

---

## 11. 정직 메시지

본 세션의 진짜 가치:
1. forward test infrastructure가 in-sample 못 본 STATE 정의 모순(legacy ≠ SSOT)을 즉시 노출
2. 추측 없이 4 phase 추적으로 진실 도달 (raw → git → web parquet → 후보 시뮬)
3. STATE의 invariance (deterministic > stochastic) 원칙 확립
4. M17만 분기, M15/M16 보존 → 최소 변경으로 정합 회복

남은 risk:
- 9.4y K3 backfill 중 만기 직후 dates에서 front contract vol=0 / 또는 KRX가 다음월로 자동 전환하는 시점 차이 → 검증 필요
- 만약 K3 fail rate 높으면 (>5%) front rule 재검토 필요
- 만기월 vol=0 anomaly는 STATE 비개입 (flag만), 추후 별도 diagnostic 분석

K3 진행 + sanity 결과로 v20 commit. 이후 v4 STEP 2 REGIME 진입.

---

**작성자**: Claude (MSM 세션 #14, STATE freeze 완료)
**상태**: v19 LOCK (M17 front-month deterministic). K3 BLOCK 해제.
**다음 작업**: K3 9.4y backfill → v20

끝.
