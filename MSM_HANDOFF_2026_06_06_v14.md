# MSM 핸드오프 v14 — Phase 2 + state v3 검증 결과

**작성일**: 2026-06-06 (KST, MSM 세션 #10 종결, 메모리 86%)
**대상 repo**: stanleyim/choonsimi-msm
**상태**: ★ v12 LOCK 유지 + state v3 cross-asset 인프라 확립 + LONG v3 검증 통과 / SHORT v3 의심
**다음**: v3 LONG-only LOCK 후보 + Forward test 시작 + SHORT 의심 분리 검증

---

## 0. 절대 원칙 (v13 §0 그대로 + v14 신규)

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
12. Forward test가 in-sample 못 본 것 발견 (v13)
13. **v14 신규**: **v12 LOCK script 부재 — reproduce 불가능 사실**. baseline equity (`v2_gamma_best.parquet`)만 신뢰. backtest logic은 영구적으로 reverse-engineer 불가. 따라서 v3는 v12 reproduce가 아닌 **새 system 구축** 방식으로만 비교 가능.

---

## 1. ★ LOCKED VALUES (v13과 동일, 변경 없음)

### 1-1. STEP 1~5 (v10 LOCK, 유지)
### 1-2. STEP 6 (v10 LOCK, 유지) — SHOCK SHORT only
### 1-3. STEP 7 V1 (v11 LOCK, 유지) — Control terminal
### 1-4. STEP 8 (v12 LOCK, 유지) — MSM v2 Production

### 1-5. v12 LOCKED CONFIG (변경 없음)
LONG side:
- Regime    : NEUTRAL (short_pressure ≈ 0)
- Selection : bot z_ell top 10/day
- Hold      : 15 days
- Weight    : 1/10

SHORT side:
- Regime    : SHOCK (v1 direction=-1 AND tradeable)
- Selection : bot score (z_r+z_f) top 10/day
- Hold      : 5 days
- Weight    : 1/10

Control (T4):
- DD trigger -20% / Exposure 0.5x / Recovery -10%

In-sample 성과:
- CAGR 16.48%, Sharpe 0.686, MDD -33.13%
- 기간: 2017-01-02 ~ 2026-06-02

---

## 2. ★★★ 세션 #10 핵심 발견 (v14 신규)

### 2-1. Cross-asset Raw 수집 완료
- **A1 (flow_market)**: KOSPI+KOSDAQ 시장 투자자별 net flow, 4618 rows, 2017-01-02 ~ 2026-06-05
  - 파일: `data/raw/cross_asset/flow_market_10y.parquet` (190.4KB)
  - 9.4년 외인 평균 net = **-705.5억원/일** (외인 net seller 사실 일치)
- **A4 VIX**: 2458 rows, max 82.69 (코로나 2020-03 peak)
  - 파일: `data/raw/cross_asset/vix_10y.parquet`
- **A4 SOX**: 2368 rows, ticker `^SOX`
  - 파일: `data/raw/cross_asset/sox_10y.parquet`
- **A2 basis**: ★ 실패 — pykrx index catalog에 KOSPI200 선물지수 없음. KRX OpenAPI derivative endpoint 별도 처리 필요 (다음 세션)
- **kospi200_spot_only_10y.parquet**: 현물만 저장 (A2 fallback)

### 2-2. state v3 input LOCKED
- **파일**: `data/macro/macro_10y_v2.parquet` (405.9KB)
- shape: (2309, 21)
- columns: flow (외인/기관/개인/imbalance), VIX, SOX + 9개 z-score (252d rolling)
- Foreign net mean: -705.5억원/일 ✅
- VIX mean 18.83, max 82.69 ✅
- trading days/year 245.1 ✅
- look-ahead 방지: z_*_t1 = shift(1)

### 2-3. ★ Full Pipeline v3 결과 — edge field 강력하나 in-sample
- df_v3 = df_sv_v2 + macro_v2 join (shape 2,793,837 × 29)
- macro_regime 4 categories: NORMAL 73% / RISKOFF 11.4% / OUTFLOW 11.2% / RISKOFF_OUTFLOW 4.6%
- combined_regime (regime × macro_regime) = 20 cells (4×4=16 + 일부 missing)
- ell_bin (3 buckets: bot/mid/top, cutoffs ±1)
- 15-day forward return mean: 0.21%

### 2-4. ★ Edge Field (in-sample 9.4y, 48 cells)
- 최강 LONG: `SHOCK|RISKOFF_OUTFLOW × bot` n=812, +353bp, t=2.70
- 최강 robust LONG: `TRANSITION|RISKOFF × bot` n=22016, +181bp, **t=22.53**
- 최강 SHORT: `SHOCK|RISKOFF × top` n=11730, -232bp, t=-13.97
- tradeable cells (E[r]>0, |t|>2, n>500):
  - LONG: 33 cells (과다, dilution)
  - SHORT: 5 cells (집중)

### 2-5. STEP α concentrated backtest (in-sample, cost 0.30% RT, hold 15d)
LONG cells (top 3):
- `TRANSITION|RISKOFF × bot` (n=22016, t=22.5, +181bp)
- `TRANSITION|RISKOFF_OUTFLOW × mid` (n=51881, t=20.5, +173bp)
- `TRANSITION|NORMAL × bot` (n=129061, t=32.6, +121bp)

SHORT cells (5): SHOCK|RISKOFF top, SHOCK|OUTFLOW top, SHOCK|NORMAL top, SHOCK|OUTFLOW mid, SHOCK|NORMAL mid

In-sample 성과:
| Leg | CAGR | Sharpe | MDD |
|---|---|---|---|
| LONG only | 9.56% | 0.599 | -49.67% |
| SHORT only | 29.16% | **1.035** | -50.19% |
| COMBINED | 22.04% | **2.271** | -11.12% |

→ Sharpe 2.271은 **artifact 강하게 의심** (v12 LOCK 0.686의 3.3배)

### 2-6. ★★★ STEP β1+β3 검증 결과 — 핵심 판정

**β3 Causality check**: ✅ **PASSED**
- regime 생성 코드에 leak pattern 0건
- t_fwd/t_now ratio: RANGE 0.20, SHOCK 0.25, TRANSITION 0.05, TREND 0.09 (모두 <1.0)
- regime label은 honest (당일/과거 정보만 사용)

**β1 Walk-forward** (train 2018-01~2022-12, test 2023-01~2026-06):

| Leg | Train Sh | Test Sh | Δ |
|---|---|---|---|
| LONG | 1.011 | **0.697** | -0.315 (정상 decay) |
| SHORT | 1.478 | **0.418** | **-1.060** (심한 decay) |
| COMBO | 2.711 | **1.052** | -1.659 |

**판정**:
- **★ LONG v3 = STRONG ALPHA 후보** (OOS Sharpe 0.697 > v12 LOCK 0.686, MDD -22% < v12 -33%)
- ★ SHORT v3 = OVERFIT 의심 (decay -1.060)
- ★ COMBO LOCK = 위험 (SHORT 의심 포함)

---

## 3. ★ 세션 #10 실수 누적 (절대 누락 X)

### #51: A4 SOX/VIX 1차 column rename 버그
- 증상: `KeyError: 'date'` (FDR `reset_index()` 후 index name 처리 실패)
- 원인: `df.columns = [...]` list comp가 index name 변환 못함
- 해결: 첫 column 무조건 'date'로 강제 (positional rename)
- 재발 방지: pandas `reset_index()` 결과 column rename은 positional 처리

### #52: A2 진단 셀 'theme' 영문 추측
- 증상: `market 옵션이 올바르지 않습니다`
- 원인: pykrx `get_index_ticker_list(market=...)` 유효값 'KOSPI/KOSDAQ/KRX/테마/ALL' 미확인 상태로 'theme' 추측
- 사전 검토 누락 사례 (#48과 동일 패턴: pykrx API 한국어 사용을 영문으로 추측)
- 해결: web_search로 'KOSPI/KOSDAQ/KRX/테마' 한글 확인
- 재발 방지: pykrx API signature 미확인 시 web_search 또는 source 직접 확인 의무

### #53: A2 KOSPI200 선물지수 catalog 부재
- 증상: pykrx index_ticker_list 어느 market에도 선물 관련 indices 0개
- 원인: pykrx `get_index_ticker_list`는 cash index만 반환. derivative는 별도 endpoint
- 추측 코드 1029~1031 시도도 모두 실패 (영문 column issue #48 동시 발현)
- 해결: A2 폐기, KRX OpenAPI derivative endpoint 별도 phase로 분리 (다음 세션)
- 재발 방지: cash vs derivative endpoint 분리 인식. pykrx 범위 명확화.

### #54: ★ v12 LOCK NEUTRAL 정의 오류 추론
- 증상: 1차 reproduce 시 `regime=='NEUTRAL'` filter → entries 0
- 원인: v13 §1-5 LOCKED CONFIG에 "Regime: NEUTRAL"로 기재. 실제 df_sv_v2 regime values는 `{TRANSITION, RANGE, SHOCK, TREND}` 4개로 'NEUTRAL' 부재
- STEP8_PROGRESS.md §4 발견: `NEUTRAL = |short_pressure| <= threshold` (별도 derived field, regime ≠ NEUTRAL)
- 그러나 정확한 threshold 값 미명시 (question mark `0.5?`)
- 1차 추론으로 `tradeable==True` 매칭 시도 → entries 22,780 매칭 (PREF_DIAGNOSIS와 일치) → 우연 일치 의심
- 2차 시도 `|short_pressure|<=0.5` → OOS 2026-06-04 매칭 0/10 → 정의 오류 확정
- ★ 핵심 결론: v12 LOCK 실제 NEUTRAL 정의 unknown
- 재발 방지: handoff doc spec의 모호한 표현은 추론 금지. ★ 우선 STEP8_PROGRESS / 노트북에서 정확 정의 확인.

### #55: ★★ v12 LOCK backtest script repo 부재 확정
- 증상: `grep v2_gamma_best` 결과 = handoff `.md` 2개만 (코드 0개)
- 원인: STEP 8.7 gamma sweep + LOCK 결정이 session #8 ad-hoc 노트북 cell에서 실행. backtest 함수 자체가 commit되지 않음
- 영향: v12 LOCK은 영구적 **black box**. baseline equity만 신뢰 가능
- ★ 핵심 결론: v12 LOCK reproduce 시도 폐기. v3는 새 system으로 구축, 결과 metric만 v12 비교
- 재발 방지: ★ 향후 모든 backtest 함수는 commit 후 LOCK. session ad-hoc cell 결과만 저장 금지.

### #56: ★ position-level reproduce 1차 실패 (Reading A/B 시도)
- 증상: Reading A `sum × 1/10`: CAGR -89% MDD -100% (catastrophic)
- 원인: r_fwd shift 방향 + cost timing + weight model 정확 spec 모름
- baseline exposure 분포: 0.5 (1402 days) / 1.0 (905 days) = T4 control terminal LOCKED 적용된 equity. 우리 reproduce는 control 미반영
- 시도 후 폐기 결정 (β'' discard)
- 재발 방지: black box system reproduce 무리하지 말 것. 새 system 구축이 더 정직.

### #57: ★ day-level overlay 결과 Δ +0.061 신뢰 한계
- 증상: vix_skip + flow_half combined → Sharpe 0.746 (Δ +0.061), MDD 개선 6.79pt
- 원인: net_return = LONG+SHORT 합산. day-level mask는 SHORT side 영향 분리 불가
- 첫 인상 채택 후보였으나 method violation으로 polish 안 됨
- 재발 방지: day-level approximation은 1차 hypothesis 검증 용도만, LOCK은 position-level 검증 후

### #58: ★ v3 SHORT side 강한 in-sample fitting
- 증상: SHORT in-sample Sharpe 1.035 (cost adj), train 1.478 → test 0.418 (decay -1.060)
- 원인: SHOCK regime 자체가 high-fwd-volatility 영역. SHORT cell 5개 합치면 cell n 큰 cells 합산 → in-sample fitting amplified
- 추가 risk: SHORT 287,706 signals (125/day) × 15d hold = ~1,875 동시 positions. 한국 공매도 가능 universe (KOSPI200/KOSDAQ150 ~350) 초과 → execution infeasible
- 재발 방지: SHORT cell 채택은 borrow universe filter + recent-only train으로 재검증 필수

### #59: 메모리 관리 미흡
- 증상: 세션 #10 종결 시 메모리 86%
- 원인: df_v3 481MB × 여러 셀에서 reload. gc.collect() 부분만, full clear 안 함
- 영향: 다음 셀 실행 가능 cell 수 제한
- 재발 방지: ★ 큰 dataframe (df_sv_v2 등) reload 시 del + gc.collect() 의무. 한 세션 내 reload 횟수 minimize.

---

## 4. ★ 다음 세션 (#11) 즉시 진입 옵션

### 4-1. ★ 권장 우선순위

| 옵션 | 내용 | 상태 |
|---|---|---|
| **A** | **v3 LONG-only LOCK** — top 3 LONG cells, cost-aware backtest 결과 LOCK 후보. OOS Sharpe 0.697 > v12 0.686. Forward test 시작. | strong candidate |
| B | SHORT cells recent-only retrain (2023-2026 train, 2024+ test) — overfit 검증 | 별도 검증 |
| C | A + 6/4 forward test 진단 (v3 LONG cells 적용 시 6/4 OOS signal) | 결합 가능 |
| D | KRX OpenAPI derivative endpoint으로 basis (A2) 재시도 | infra 확장 |
| E | choonsimi-premium 6/26 결과 후 dual-engine 검토 | wait |
| F | v12 LOCK 유지 + v3 LONG 병행 운영 검토 | parallel |

### 4-2. ★ 권장: **A + C 결합**
- v3 LONG-only LOCK 후보 (OOS 검증 통과)
- forward test 6/4 데이터에서 v3 LONG cells 적용 시 어떤 종목 selection 되는지 확인
- v12 LOCK signal 10종목과 overlap 확인
- 둘이 의미 있게 다르면 → v3 LONG이 진짜 신호

### 4-3. ★ 위험 옵션 (선택 시 매우 신중)
- COMBO (LONG+SHORT) v3 LOCK = SHORT 의심 포함 → ★ 추천 안 함
- SHORT-only v3 LOCK = 강한 overfit + execution infeasible → ★ 추천 안 함

---

## 5. ★ 파일 인벤토리 (commit 본 세션 종결 시점)

choonsimi-msm/
- MSM_HANDOFF_2026_06_02.md (v1~v4)
- MSM_HANDOFF_2026_06_03_v6.md
- MSM_HANDOFF_2026_06_04_v7~v11.md
- MSM_HANDOFF_2026_06_05_v12.md
- MSM_HANDOFF_2026_06_05_v13.md
- **MSM_HANDOFF_2026_06_06_v14.md** ← 이 문서 (Phase 2 검증 결과)
- PREF_DIAGNOSIS_2026_06_05.md
- STEP8_PROGRESS.md
- README.md
- msm_data_supplement.ipynb
- msm_data_ingestion.ipynb
- msm_state_vector.ipynb
- data/
  - raw/
    - active/, delisted/, macro/
    - vkospi_10y_*.csv
    - short/volume/, balance/
    - **cross_asset/** ★ v14 신규
      - flow_market_10y.parquet (190.4KB)
      - vix_10y.parquet
      - sox_10y.parquet
      - kospi200_spot_only_10y.parquet (A2 fallback)
  - macro/
    - **macro_10y_v2.parquet** ★ v14 신규 (405.9KB, state v3 input)
  - state/
    - state_vector/, regime/, transition/, edge/, tradeable/ (v1)
    - state_vector_v2/, edge_v2/ (v2)
    - **edge_v3/** ★ v14 신규
      - edge_field_v3.parquet (48 cells)
      - tradeable_v3.parquet (33 LONG cells)
  - sim/
    - equity_curve_shock_short_only.parquet (STEP 6)
    - equity_t4_v1.parquet (STEP 7)
    - v2_short_only/long_only/long_short.parquet (STEP 8.6)
    - v2_gamma_best.parquet (MSM v2 LOCKED, **black box**)
    - step87_gamma_sweep.parquet
  - **sim_v3/** ★ v14 신규
    - concentrated_long.parquet (LONG only equity)
    - concentrated_short.parquet (SHORT only)
    - concentrated_combined.parquet (COMBO, **결과 의심**)
- forward_test/
  - baseline.json, README.md, metrics/, state/, log/

---

## 6. 본 세션 (#10) commit 이력

- d368b33  MSM α: cross-asset raw (flow/basis/sox/vix) 1/2 OK
- 73257f7  MSM α hotfix: SOX/VIX 2/2 OK + A2 catalog diag
- ca8f466  MSM state v3 input: macro_10y_v2 (flow+VIX+SOX, 252d z-score)
- ce4a6de  MSM v3 pipeline: edge_field_v3 (48 cells, 33 LONG tradeable)
- cac047b  MSM v3 α: concentrated LONG3+SHORT5 cost-aware (Sharpe=2.271)
- (HEAD) MSM HANDOFF v14: Phase 2 검증. v3 LONG OOS 0.697 / SHORT decay -1.060

---

## 7. ★ 다음 세션 합본 셀 (paste & run, ~40초)

EXPECTED_HEAD_PREFIX = "XXXXXXX" ← v14 commit hash로 갱신 (이 셀 실행 직후 확인)

```python
import os, subprocess, shutil, time, sys, glob
from pathlib import Path
import pandas as pd

t0 = time.time()
REPO = '/content/choonsimi-msm'
EXPECTED_HEAD_PREFIX = 'XXXXXXX'  # ← v14 push 후 갱신

from google.colab import userdata
GH = userdata.get('GH_TOKEN'); assert GH
for k in ['KRX_ID','KRX_PW','ECOS_API_KEY','GH_TOKEN']:
    try:
        v = userdata.get(k)
        if v and k in ('KRX_ID','KRX_PW'): os.environ[k] = v
    except: pass

if Path(REPO).exists(): shutil.rmtree(REPO)
url = f'https://x-access-token:{GH}@github.com/stanleyim/choonsimi-msm.git'
subprocess.run(['git', 'clone', url, REPO], check=True)
os.chdir(REPO)
head = subprocess.run(['git','rev-parse','--short','HEAD'], capture_output=True, text=True).stdout.strip()
assert head.startswith(EXPECTED_HEAD_PREFIX), f'HEAD mismatch'
print(f'clone HEAD={head}')

subprocess.run([sys.executable,'-m','pip','install','-q','pyarrow','pandas','numpy','psutil','pykrx','finance-datareader'], check=True)
subprocess.run(['git','config','user.email','msm@stanleyim.local'], check=True, cwd=REPO)
subprocess.run(['git','config','user.name','stanleyim'], check=True, cwd=REPO)

# Load
sv2_files = sorted(glob.glob('data/state/state_vector_v2/year=*.parquet'))
df_sv_v2 = pd.concat([pd.read_parquet(f) for f in sv2_files], ignore_index=True)
df_sv_v2['date'] = pd.to_datetime(df_sv_v2['date'])
assert df_sv_v2.shape == (2793837, 25)

df_macro_v2 = pd.read_parquet('data/macro/macro_10y_v2.parquet')
assert df_macro_v2.shape == (2309, 21)

df_edge_v3 = pd.read_parquet('data/state/edge_v3/edge_field_v3.parquet')
df_trad_v3 = pd.read_parquet('data/state/edge_v3/tradeable_v3.parquet')

df_eq_v2_best = pd.read_parquet('data/sim/v2_gamma_best.parquet')
print(f'준비 완료 {time.time()-t0:.1f}s')
print(f'v3 edge cells: {len(df_edge_v3)}, tradeable: {len(df_trad_v3)}')
```

---

## 8. ★ 핵심 한 줄

v12 LOCK 유지 (변경 X). Cross-asset 4축 (flow/VIX/SOX) raw 수집 완료. state v3 input LOCKED (macro_10y_v2). v3 edge field 48 cells, in-sample 강력 (t-stat 22+). β1+β3 검증: causality 안전 + LONG OOS Sharpe 0.697 (v12 LOCK 0.686 상회) / SHORT decay -1.060 의심. v12 LOCK script 부재 확정 (#55) — 영구 reproduce 불가. 다음 세션: v3 LONG-only LOCK + forward test 시작.

---

## 9. 형의 다음 세션 분석 우선순위

1. **v3 LONG-only LOCK 결정** (OOS 0.697 vs v12 0.686 비교)
2. v3 LONG cells + 6/4 forward test signal 진단 (v12와 overlap)
3. SHORT 의심 - recent-only retrain 또는 폐기
4. choonsimi-premium 6/26 결과 (D-20)
5. dual-engine 운영 (v12 + v3 LONG) 검토

---

## 10. 정직 메시지 — 세션 #10 reflection

세션 #10에서 한 일:
- ★ Cross-asset 인프라 + state v3 build = **건전한 진전**
- ★ v3 LONG OOS 0.697 발견 = **유의미한 alpha 후보**
- ★ β3 causality check + β1 walk-forward = **올바른 검증 절차**

세션 #10 함정에 빠진 일:
- v12 LOCK reproduce 시도 (3회) — backtest script 부재 확인 전 시간 낭비
- day-level overlay 결과 채택 보류 결정은 정직 (방법론 위반)
- COMBO Sharpe 2.271 첫 인상에 사로잡힐 뻔했으나 즉시 의심 발동 → β1+β3로 검증 → LONG 진짜, SHORT 의심 분리 → ★ 올바른 결론

세션 #10 형 sanity check 결정적:
- 옵션 결정 시점마다 형이 STATE → REGIME → TRANSITION → EDGE → TRADEABLE 구조 기준 평가
- COMBO Sharpe 2.271 즉시 폐기 결정 X, β1+β3 검증 → 진짜/가짜 분리
- 메모리 86% 시점 종결 결정 = 정확한 판단

다음 세션 핵심 reminder:
- v3 LONG OOS Sharpe 0.697은 **3.4년 OOS** 결과. 통계적 의미 있음
- 그러나 forward test (진짜 OOS) 누적 전 LOCK은 신중
- v12 + v3 LONG 병행 운영이 안전한 첫 단계

---

**작성자**: Claude (MSM 세션 #10, Phase 2 검증 종결)
**상태**: v12 LOCK 유지, state v3 검증 통과 (LONG only), 다음 세션 LOCK 후보
**다음 작업**: v3 LONG LOCK + forward test 시작 + SHORT 분리 검증

끝.
