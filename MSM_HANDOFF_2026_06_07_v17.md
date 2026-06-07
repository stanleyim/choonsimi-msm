# MSM 핸드오프 v17 — Phase 3.1 진입 (Realized Log Schema v1.2 + OOS #1)

**작성일**: 2026-06-07 (KST, MSM 세션 #11 종결)
**대상 repo**: stanleyim/choonsimi-msm
**v16 최신 commit**: 1b59c91
**v17 최신 commit**: 612c1aa — schema v1.2 + 6/4 OOS#1 n=50 full state
**상태**: ★ v12 LOCK 유지 + Realized Log schema 결함 해결 + 첫 OOS 1 day trajectory 확보 + 이벤트 대기 모드 진입
**다음**: 6/8 (월) KRX OpenAPI 4축 승인 확인 + daily_run 본체 (N7-full) 설계

---

## 0. 절대 원칙 (v16 §0 + v17 신규)

1. §1 추측 금지
2. §6 3번 검토 (정확성 + 사고 가능성 + 안전장치)
3. §7 옵션 → 형 결정 → 실행
4. §13 매 단계 commit/push
5. MSM = choonsimi-premium 독립 (v10c 6/26 freeze)
6. 외부 검토자 3 원칙
7. 단일 셀 통합 코드
8. Signal ≠ Execution constraint
9. Selection asymmetry: edge_field universe ≠ realized top-K
10. Control manifold ≠ Alpha manifold
11. State manifold > Control manifold (v12)
12. v13: Forward test가 in-sample 못 본 것 발견
13. v14 §0: v12 simulator + regime detection 재현 영구 불가
14. **v17 신규**: **REJECTED state도 STATE의 일부** — filter로 entry 거부된 cash state 미기록 시 edge biased. P(no-trade|filter) 추정 가능해야 unbiased edge.

---

## 1. ★ LOCKED VALUES (v12와 동일, 변경 없음)

### 1-1. STEP 1~5 (v10 LOCK, 유지)
### 1-2. STEP 6 (v10 LOCK, 유지)
### 1-3. STEP 7 V1 (v11 LOCK, 유지)
### 1-4. STEP 8 (v12 LOCK, 유지) — MSM v2 Production
- v12 commit: 559a65e
- v12.md: 454 lines, 17.4KB

### 1-5. v12 LOCKED CONFIG (변경 금지)
```
LONG : NEUTRAL × bot z_ell top 10, hold 15d, weight 1/10
SHORT: SHOCK × bot score top 10, hold 5d, weight 1/10
T4   : DD -20% / Exposure 0.5x / Recovery -10%
Cost : 0.30% RT (entry 0.15% + exit 0.15%)
```

In-sample 성과 (변경 없음):
- CAGR 16.48%, Sharpe 0.686, MDD -33.13%, GROSS Sh 1.67
- 기간: 2017-01-02 ~ 2026-06-02

---

## 2. ★ Phase 3 진행 상태 (v16 § 진척)

### 2-1. 데이터 (v16 § 유지)
- web/12008 (3 file) + web/8 type (parquet) = 9.4y 12 type 확보
- 채권 4종 보류 (KRX OpenAPI 미승인)
- 19 axis 카탈로그 → redundancy 제거 → 16 axis
- Tier 1: M8 / M2 / M6 / M17 / M3
- Protocol C: M8/M2/M6 ΔSh +0.23/+0.23/+0.17

### 2-2. Path D 확정 (v16 § 유지)
- Protocol C 결과 → forward test 즉시 적용
- M8 = best risk-adjusted (MDD -22.9%)
- M2 = best gain (active 86%, 약한 filter)
- M6 = passive flow signal

---

## 3. ★★★ v17 신규 — Realized Log Infrastructure 확립

### 3-1. schema 진화 (v17 본 세션)

| version | 변경 | 결함 |
|---|---|---|
| v1.0 | 28 columns 초안 (axis flag 없음) | 실행 전 폐기 |
| v1.1 | + `axis_ref_date`, `axis_lag_bd` (lag honesty) | REJECTED 미기록 |
| **v1.2** | + `signal_status` (TAKEN / REJECTED_BY_FILTER) | ★ 적용 중 |

### 3-2. schema v1.2 핵심 컬럼

`forward_test/schema/realized_log_v1.json`:

```
log_id, entry_date, exit_date, code, side
signal_source: v12_RAW / v12+M8 / v12+M2 / v12+M6 / v12+M8M2M6
signal_status: TAKEN / REJECTED_BY_FILTER
is_pollution_risk: bool (True if filter uses M2/M8/M6)
is_oos: bool (True if entry_date >= 2026-06-04)
entry_px, mtm_px, mtm_date, gross_ret_mtm, entry_cost, exit_cost, net_ret_mtm
weight, hold_days_elapsed, hold_days_target, status (OPEN/CLOSED/SKIPPED)
regime_at_entry
axis_M8, axis_M2, axis_M6, axis_ref_date, axis_lag_bd
filter_M8_pass, filter_M2_pass, filter_M6_pass
notes
```

### 3-3. REJECTED rule (★ 핵심)

```
조건: signal_source has filter AND filter_pass=False
overrides:
  entry_px=NaN, mtm_px=NaN, mtm_date=NaT
  gross_ret_mtm=0.0, entry_cost=0.0, exit_cost=0.0
  net_ret_mtm=0.0, weight=0.0, hold_days_elapsed=0
  status='SKIPPED'
```

→ variant별 n=10 always (TAKEN + REJECTED 합)
→ portfolio_return = mean(net_ret_mtm) over n=10 = unbiased

### 3-4. Pollution rule (OOS-IS 분리, 외부 평가 핵심 수용)

```
is_pollution_risk:
  True: v12+M8 / v12+M2 / v12+M6 / v12+M8M2M6 (sweep_C 출처)
  False: v12_RAW

true_OOS_metric_eligibility:
  is_oos==True AND signal_source=='v12_RAW' 만 진짜 OOS 통계 산출 가능
```

### 3-5. Lag rule

```
ideal_lag_bd: 1 (T-1 axis)
current_known_issue: axis_v3 cutoff 6/2 → 6/4 entry T-1(6/3) 데이터 없음 → T-2(6/2) 강제 fallback → axis_lag_bd=2
```

---

## 4. ★ OOS #1 결과 (2026-06-04 → 06-05)

### 4-1. 데이터
- entry_date: 2026-06-04
- mtm_date  : 2026-06-05
- LONG codes (10): 000157, 03473K, 003650, 006405, 058650, 071055, 000155, 065710, 052330, 005389
- axis @ ref_date=2026-06-02 (T-2, axis_lag_bd=2):
  - M8 z_inst_kospi   = -0.309 → **REJECT** (rule M8>0)
  - M2 z_vkospi_delta = -0.838 → pass (rule M2>-1)
  - M6 z_foreign_kospi_etf = -0.245 → pass (rule M6<0)

### 4-2. Portfolio result (1 day mtm, equal weight)

| variant | status | n | net_bp | pollution |
|---|---|---|---|---|
| v12_RAW | TAKEN | 10 | **-440** | False |
| v12+M2 | TAKEN | 10 | -440 | True |
| v12+M6 | TAKEN | 10 | -440 | True |
| v12+M8 | REJECTED | 10 | **0** | True |
| v12+M8M2M6 | REJECTED | 10 | 0 | True |

### 4-3. 해석 (정직)
- **n=1, 통계적 의미 0**
- v12 raw 1일 -4.40% = single anomaly
- M8 filter는 이 entry 자체를 거부 (axis -0.309 < 0)
- M2/M6는 6/4 시점에 non-discriminative
- 방향 정합: in-sample sweep_C M8 1순위 → OOS #1 에서 entry 거부 정합
- 단정 금지: 우연 가능. n≥20 누적 후 통계 평가

---

## 5. ★ N7a — Daily mtm update template

### 5-1. 위치 & 동작
- 본체: 단일 셀 (paste & run, 매일 1회)
- repo 저장 위치: 본 세션 #11에서는 별도 파일 미생성 (셀 내 inline)
- 다음 세션에서 `forward_test/templates/daily_mtm_update.py` 또는 notebook으로 정형화 권장

### 5-2. 동작 정의
```
1. realized_log load
2. (signal_status=TAKEN AND status=OPEN) 필터
3. 가장 최근 KRX 거래일 식별 (KOSPI index OHLCV)
4. prev_mtm_date >= latest_biz → no-op exit (idempotent)
5. OPEN row의 code별 종가 fetch
6. mtm_px / mtm_date / gross_ret_mtm / hold_days_elapsed 갱신
7. hold_days_elapsed >= hold_days_target 시 status=CLOSED + exit_cost=0.0015
8. parquet overwrite + commit + push
```

### 5-3. Idempotency 검증 완료
- 본 세션 #11 첫 실행: latest_biz=6/5 == prev_mtm=6/5 → no-op exit
- 같은 mtm_date 재실행 안전
- 새 거래일 도달 시만 update

### 5-4. 만기 예정일
- 6/4 entry + 15bd = **2026-06-25 (수)** 예상 (KRX 영업일 기준 확인 필요)
- 만기 시 자동 CLOSED, exit_cost 0.0015 차감

---

## 6. ★ 이벤트 대기 모드 정의 (v17 신규)

### 6-1. 조건
```
next KRX biz day > prev_mtm_date → N7a 실행
else: no-op
```

### 6-2. 예상 일정
- 6/8 (월): N7a → mtm @ 6/8, hold=2bd
- 6/9 ~ 6/24: 매일 N7a 실행 (영업일만)
- 6/25 (수, 예상): hold=15bd 도달 → 자동 CLOSED
- 6/25 ~: t=15 full trajectory 분석 가능

### 6-3. 축적 목표
```
R_1, R_2, ..., R_15 (single entry trajectory)
```

### 6-4. 분석 진입 조건
- t ≥ 5  → 초기 shape 분석
- t ≥ 10 → convexity 확인
- t ≥ 15 → exit rule 정의

---

## 7. ★ 다음 세션 우선순위

### 7-1. Step 1 (★ 즉시, 6/8 월): KRX OpenAPI 4축 승인 확인
- basis / pcr / etf / kts endpoint 승인 여부
- 승인 = N7-full daily_run 본체 설계에 즉시 반영
- 미승인 = 보류, N7-full minimal 우선

### 7-2. Step 2: daily_run 본체 (N7-full) 설계
범위:
- state_v2 daily append (1,603 종목 OHLCV → r/sigma/v/ell/f → z-score → state_vector_v2/year=2026.parquet 갱신)
- 공매도 잔고 daily fetch (T-2 input)
- axis_v3 daily append (19 axis 중 fetchable subset)
- 신규 v12 LONG/SHORT signal 생성 (regime detection 영구 불가 → ★ 대안 필요)
- realized_log에 새 OOS row append (TAKEN + REJECTED 모두)

★ 핵심 미해결: **regime detection 영구 불가** → 신규 signal 생성 = bot z_ell top 10 + 직접 정의 NEUTRAL rule 필요. v14 §0와 정합 유지.

### 7-3. Step 3: N7a 매일 실행
- 6/8부터 매일 1셀 paste & run
- 자동 commit/push
- 6/25까지 15-day trajectory 확보

### 7-4. Step 4: t=5/10/15 분석 셀 (조건부)
- 6/15 (목): t≈5 도달 시 multi-day return surface 추출
- 6/22 (월): t≈10 convexity 분석
- 6/25 (수): t=15 완성 + exit rule 정의

---

## 8. ★ 즉시 실행 가능 옵션 (다음 세션)

| 옵션 | 내용 | 시간 | 의존성 |
|---|---|---|---|
| **A** | N7a 6/8 mtm update (자동) | ~1분 | 6/8 장 마감 후 |
| **B** | KRX OpenAPI 승인 확인 | ~3분 | KRX 응답 |
| **C** | N7-full minimal 설계 (state_v2 append만, signal 생성 보류) | ~15분 | Setup |
| **D** | N7-full 본체 (signal 생성 포함, regime 대안 필요) | ~30분+ | regime 대안 결정 |
| **E** | multi-day return surface schema 사전 설계 (t=5 도달 전) | ~5분 | 데이터 부족, 비권장 |

권장: A → B → C (안전 순서)

---

## 9. ★ 실수 누적 (v16 #1~#57 + v17 신규 #58~#60)

v16 #51~#57 유지.

**v17 신규**:

- **#58**: `axis_candidates_19.parquet` 구조 추측 실패. v13에서 `df_ax['date']` 컬럼 가정으로 코드 작성했으나 실제는 DatetimeIndex (index name = None). KeyError 발생. **재발 방지**: parquet load 후 `print(df.shape), print(df.index.name), print(df.columns)` 진단 의무. 단일 셀 작성 전 1셀 진단 권장.

- **#59**: axis_v3 cutoff = 2026-06-02. 6/4 entry의 T-1(6/3) axis 데이터 없음 → T-2(6/2) 강제 fallback. axis_lag_bd=2 = forward filter 신뢰도 1단계 약화. 근본 원인: axis_v3 daily append 로직 부재. **재발 방지**: daily_run 본체 (N7-full) 설계 시 axis_v3 daily append 필수 포함. 19 axis 중 fetchable subset (M1/M2/M5~M14 등) 매일 +1 row 갱신.

- **#60**: ★ schema v1.1 초기 설계 결함 — REJECTED row 미기록. 첫 OOS day(6/4)에서 즉시 발견. v12_RAW와 v12+M8을 동일 sample size로 비교 불가능 = edge biased. v1.2 bump (signal_status 신설)로 즉시 수정. **재발 방지**: schema 설계 시 "filter REJECT = 0 cash state도 STATE의 일부"라는 §0 #14 원칙 사전 확인 의무. P(no-trade|filter) 추정 가능성 = unbiased edge 전제.

---

## 10. ★ 다음 세션 합본 셀

### 10-1. Setup 셀 (paste & run, ~50초)

```python
# ===== MSM 합본 Setup Cell v17 (paste & run) =====
import os, subprocess, shutil, time
from pathlib import Path

os.chdir('/content')
t0 = time.time()
REPO = '/content/choonsimi-msm'
EXPECTED_HEAD_PREFIX = '612c1aa'  # v17 종결 commit (또는 v17 upload 후 갱신)

from google.colab import userdata
GH = userdata.get('GH_TOKEN'); assert GH

if Path(REPO).exists():
    shutil.rmtree(REPO)
url = f'https://x-access-token:{GH}@github.com/stanleyim/choonsimi-msm.git'
r = subprocess.run(['git', 'clone', url, REPO], capture_output=True, text=True, cwd='/content')
assert r.returncode == 0, r.stderr
os.chdir(REPO)
head = subprocess.run(['git','rev-parse','--short','HEAD'], capture_output=True, text=True).stdout.strip()
print(f'clone HEAD={head}')
assert head.startswith(EXPECTED_HEAD_PREFIX)

import sys
subprocess.run([sys.executable,'-m','pip','install','-q','pyarrow','pandas','numpy','psutil','pykrx'], check=True)
import pyarrow, pandas as pd, numpy as np, psutil

for k in ['KRX_ID','KRX_PW','ECOS_API_KEY','GH_TOKEN']:
    try:
        v = userdata.get(k)
        if v and k in ('KRX_ID','KRX_PW'):
            os.environ[k] = v
    except: pass

subprocess.run(['git','config','user.email','msm@stanleyim.local'], check=True, cwd=REPO)
subprocess.run(['git','config','user.name','stanleyim'], check=True, cwd=REPO)

# Load v2 state_vector
from glob import glob
sv2_files = sorted(glob('data/state/state_vector_v2/year=*.parquet'))
df_sv_v2 = pd.concat([pd.read_parquet(f) for f in sv2_files], ignore_index=True)
df_sv_v2['date'] = pd.to_datetime(df_sv_v2['date'])
df_sv_v2['score'] = df_sv_v2['z_r'] + df_sv_v2['z_f']
assert df_sv_v2.shape == (2793837, 26)
print(f'df_sv_v2: {df_sv_v2.shape}')

# v12 LOCK equity
df_eq_v2_best = pd.read_parquet('data/sim/v2_gamma_best.parquet')
assert len(df_eq_v2_best) == 2307
print(f'v2 BEST equity: {len(df_eq_v2_best)} rows')

# Realized log (v17 신규)
log_path = Path('forward_test/log/realized/realized_log.parquet')
if log_path.exists():
    df_log = pd.read_parquet(log_path)
    print(f'realized_log: {len(df_log)} rows ({(df_log["signal_status"]=="TAKEN").sum()} TAKEN, '
          f'{(df_log["signal_status"]=="REJECTED_BY_FILTER").sum()} REJECTED)')

# axis catalog
df_ax = pd.read_parquet('data/state/axis_v3/axis_candidates_19.parquet')
print(f'axis_v3: shape={df_ax.shape}, cutoff={df_ax.index.max().date()}')

print(f'준비 완료 {time.time()-t0:.1f}s')
```

### 10-2. 첫 메시지 권장

```
MSM Phase 3.1 진행 중.
MSM_HANDOFF_2026_06_07_v17.md 참고.

현재:
- v12 LOCK 유지 (Sharpe 0.686)
- Realized log schema v1.2 (signal_status TAKEN/REJECTED)
- OOS #1 n=50 (6/4→6/5): v12_RAW -440bp, M8 REJECT
- N7a daily mtm template 확립 + idempotent 검증 완료
- 이벤트 대기 모드: 6/8 첫 mtm update 예정

다음 우선순위:
1. KRX OpenAPI 4축 승인 확인
2. N7a 6/8 mtm update 실행
3. N7-full minimal 설계 (state_v2 daily append)
4. regime detection 대안 결정 (v14 §0 영구 불가)

§1 추측 X, §6 3축, §7 옵션→형 결정→실행, 단일 셀.
```

---

## 11. 파일 인벤토리 (commit 612c1aa 기준)

```
choonsimi-msm/
- MSM_HANDOFF_2026_06_02_v1~v4.md
- MSM_HANDOFF_2026_06_03_v6.md
- MSM_HANDOFF_2026_06_04_v7~v11.md
- MSM_HANDOFF_2026_06_05_v12~v13.md
- MSM_HANDOFF_2026_06_07_v14~v16.md
- MSM_HANDOFF_2026_06_07_v17.md ← 이 문서
- MSM_WORKPLAN_v1~v2.md
- STEP8_PROGRESS.md
- README.md
- *.ipynb (data_ingestion / data_supplement / state_vector)
- data/
  - raw/ (active/delisted/macro/short/openapi/web)
  - universe/universe_msm.csv
  - state/
    - state_vector/year=*.parquet (v1)
    - state_vector_v2/year=*.parquet (v2, 259MB)
    - regime/edge/tradeable/transition (v1)
    - edge_v2/edge_field_v2.parquet
    - axis_v3/
      - axis_candidates_19.parquet ★ (2307×19, cutoff 6/2)
      - axis_corr_matrix.parquet
      - lag_k_corr.parquet
      - dd_conditional_corr.parquet
      - monthly_corr.parquet
      - sweep_C_filter_v12pnl.parquet
  - sim/
    - v2_gamma_best.parquet (MSM v2 BEST LOCK)
    - step87_gamma_sweep.parquet
- forward_test/
  - baseline.json
  - README.md
  - metrics/day1_setup.parquet
  - state/oos_state_20260603_20260605.parquet
  - log/long_signals_20260603_20260605.json
  - log/realized/realized_log.parquet ★ v17 신규 (n=50)
  - schema/realized_log_v1.json ★ v17 신규 (v1.2)
```

---

## 12. 본 세션 (#11) commit 이력

- 612c1aa  MSM session#11 N6: realized_log v1.2 (signal_status TAKEN/REJECTED) + 6/4 OOS#1 n=50 full state
- (v17 핸드오프 upload 시 새 commit, 직접 갱신 필요)

---

## 13. 핵심 한 줄

본 세션 #11 = **realized log infrastructure 결함 해결**. schema v1.0→v1.1→v1.2 진화로 REJECTED state 보존 + axis lag honesty 확보. OOS #1 n=50 full state 확보 (v12_RAW -440bp / M8 REJECT cash 0bp). N7a daily mtm template 확립 + idempotent 검증. 이벤트 대기 모드 진입. 다음 세션 = 6/8 KRX OpenAPI 승인 확인 + N7-full 본체 설계.

---

## 14. 정직 메시지

본 세션 #11에서 발견한 진짜:

**좋은 것**:
- schema 결함이 첫 OOS day에서 즉시 드러남 = forward test 인프라의 두 번째 성공 사례 (v13 §14 우선주 발견에 이어)
- v1.1 → v1.2 bump = 24시간 내 즉시 수정 = 누적 오염 0
- N7a idempotent 검증 = 매일 자동 실행 안전성 확보

**한계**:
- OOS n=1, 통계 의미 0
- M8 reject가 정합인지 우연인지 판정 불가 (n≥20 필요)
- axis_v3 cutoff 6/2 = axis_lag_bd=2 (T-1 의도 vs 실제 T-2)
- regime detection 영구 불가 (v14 §0) = 신규 OOS entry 자동 생성 불가
- daily_run 본체 (N7-full) 미구현 = OOS 1점 trajectory만 추적, 신규 entry 불가

**결론**:
- 본 세션 = 인프라 작업 (성능 향상 0)
- 진짜 성능 검증 = OOS 1.5~3개월 누적 후
- 단, schema가 결함 없이 누적 = 그때 신뢰 가능한 통계 산출 가능

**다음 세션 핵심**:
- KRX OpenAPI 승인 결과
- N7-full 본체 = regime 대안 결정이 bottleneck

---

## 부록 1 — Realized Log Schema v1.2 컬럼 정의 (Reference)

| 컬럼 | dtype | 설명 |
|---|---|---|
| log_id | str | {entry_date}_{code}_{signal_source} |
| entry_date | date | T+0 entry 의도일 |
| exit_date | date | nullable; OPEN/SKIPPED 시 NaT |
| code | str | KRX 6-digit code |
| side | str | LONG / SHORT |
| signal_source | str | v12_RAW / v12+M8 / v12+M2 / v12+M6 / v12+M8M2M6 |
| signal_status | str | TAKEN / REJECTED_BY_FILTER |
| is_pollution_risk | bool | True if filter from sweep_C |
| is_oos | bool | True if entry_date >= 2026-06-04 |
| entry_px | float | entry close; REJECTED 시 NaN |
| mtm_px | float | current mark; REJECTED 시 NaN |
| mtm_date | date | latest mark; REJECTED 시 NaT |
| gross_ret_mtm | float | (mtm/entry)-1; REJECTED=0.0 |
| entry_cost | float | 0.0015 if TAKEN else 0.0 |
| exit_cost | float | 0.0015 if CLOSED else 0.0 |
| net_ret_mtm | float | gross - costs; REJECTED=0.0 |
| weight | float | 0.10 if TAKEN else 0.0 |
| hold_days_elapsed | int | biz days entry→mtm; REJECTED=0 |
| hold_days_target | int | 15 LONG / 5 SHORT |
| status | str | OPEN / CLOSED / SKIPPED |
| regime_at_entry | str | v12 regime label (raw 미가용 시 NaN) |
| axis_M8 | float | M8_z_inst_kospi at axis_ref_date |
| axis_M2 | float | M2_z_vkospi_delta at axis_ref_date |
| axis_M6 | float | M6_z_foreign_kospi_etf at axis_ref_date |
| axis_ref_date | date | axis 실제 참조일 |
| axis_lag_bd | int | entry_date - axis_ref_date (의도 1, 실제 ≥1) |
| filter_M8_pass | bool | axis_M8 > 0.0 |
| filter_M2_pass | bool | axis_M2 > -1.0 |
| filter_M6_pass | bool | axis_M6 < 0.0 |
| notes | str | free text |

---

## 부록 2 — 19 Axis 정의 (v16 부록 1 유지)

| ID | 이름 | source | 정의 | Tier |
|---|---|---|---|---|
| M1 | z_vkospi | 0546 | VKOSPI 종가 60d z | 2 |
| M2 | z_vkospi_delta | 0546 | VKOSPI 등락률 60d z | **1** |
| M3 | z_ytm_change | 3351 | YTM diff 60d z | **1** |
| M4 | z_duration | 3351 | 듀레이션 60d z | 3 |
| M5 | z_foreign_kospi_cash | 12008 | KOSPI(excl) 외인합 60d z | 2 |
| M6 | z_foreign_kospi_etf | 12008 | (kospi_incl - kospi_excl) 외인합 60d z | **1** |
| M7 | z_foreign_kosdaq | 12008 | KOSDAQ 외인합 60d z | 2 |
| M8 | z_inst_kospi | 12008 | KOSPI(excl) 기관7합 60d z | **1** |
| M9 | z_inst_kosdaq | 12008 | KOSDAQ 기관7 60d z | 3 |
| M10 | z_indiv_kospi | 12008 | KOSPI(excl) 개인 60d z | 3 |
| ~~M11~~ | ~~z_indiv_kosdaq~~ | 12008 | (M7 mirror) | ❌ 제거 |
| ~~M12~~ | ~~z_foreign_divergence~~ | 12008 | (M5 대체) | ❌ 제거 |
| ~~M13~~ | ~~z_etf_foreign~~ | 1415 | (M6 동일) | ❌ 제거 |
| M14 | z_etf_pension | 1415 | ETF 연기금 60d z | 2 |
| M15 | z_basis_k200 | 2524 | KOSPI200 괴리율 60d z | 2 |
| M16 | z_basis_kq150 | 3729 | KOSDAQ150 괴리율 60d z | 3 |
| M17 | z_basis_vkospi | 4031 | VKOSPI 시장베이시스 60d z | **1** |
| M18 | z_pc_k200 | 4914 | KOSPI200 P/C 60d z | 2 |
| M19 | z_pc_kq150 | 0145 | KOSDAQ150 P/C 60d z | 3 |

유지 16 axis. Tier 1 = 5개.

---

## 부록 3 — Protocol C Top 5 (v16 §2-5 유지)

| axis | dir | th | Sharpe | ΔSh | active% | MDD |
|---|---|---|---|---|---|---|
| M2 vkospi_delta | gt | -1.0 | 0.917 | **+0.231** | 86% | -30.8% |
| M8 inst_kospi | gt | 0.0 | 0.915 | **+0.229** | 50% | **-22.9%** |
| M6 foreign_etf | lt | 0.0 | 0.855 | **+0.170** | 51% | -22.8% |
| M17 basis_vkospi | gt | -1.0 | 0.816 | +0.130 | 65% | -35.0% |
| M3 ytm_change | gt | -1.0 | 0.749 | +0.064 | 85% | -30.0% |

---

**작성자**: Claude (MSM 세션 #11, Phase 3.1 진입)
**상태**: v12 LOCK 유지, schema v1.2 확립, OOS #1 n=50 full state, N7a idempotent 확보, 이벤트 대기 모드
**다음 작업**: 6/8 KRX OpenAPI 확인 + N7-full 본체 설계

끝.
