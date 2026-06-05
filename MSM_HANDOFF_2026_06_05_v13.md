# MSM 핸드오프 v13 — Phase 2 진입 (Forward Test Day-1 완료 + 우선주 발견)

**작성일**: 2026-06-05 (KST, MSM 세션 #9 종결, 자정 직전)
**대상 repo**: stanleyim/choonsimi-msm
**최신 commit**: 92b047f — Forward test OOS 6/4 LONG signals + state v2
**상태**: ★ v12 LOCK 유지 + Forward Test infrastructure 확립 + 첫 OOS 신호 + 우선주 의심 발견
**다음**: α (우선주 영향 검증) — 진단 우선

---

## 0. 절대 원칙 (v12 §0 + v13 신규)

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
12. v13 신규: **Forward test가 in-sample 못 본 것 발견** — 우선주 의심 케이스가 증명

---

## 1. ★ LOCKED VALUES (v12와 동일)

### 1-1. STEP 1~5 (v10 LOCK, 유지)
### 1-2. STEP 6 (v10 LOCK, 유지) — SHOCK SHORT only
### 1-3. STEP 7 V1 (v11 LOCK, 유지) — Control terminal
### 1-4. STEP 8 (v12 LOCK, 유지) — MSM v2 Production
- v12 commit: 559a65e
- v12.md: 454 lines, 17.4KB

### 1-5. v12 LOCKED CONFIG (변경 금지)
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
- CAGR 16.48%, Sharpe 0.686, MDD -33.13%, GROSS Sh 1.67
- 기간: 2017-01-02 ~ 2026-06-02

---

## 2. ★ Phase 2 — Forward Test 진행 상태

### 2-1. Day-1 Setup 완료 (commit d94cd00)
- forward_test/ 디렉토리 확립
- baseline.json (sharpe_target, mdd_target, cagr_target)
- README.md
- metrics/day1_setup.parquet
- OOS 거래일 확인: 6/4, 6/5 (총 2일)

### 2-2. Stage 2 OOS 신호 생성 (commit 92b047f)
- 6/4 OOS LONG signal 10종목 생성 성공
- T-2 잔고 fetch 우회 성공 (영문 column 변환)
- short_pressure 88.3% coverage
- forward_test/state/oos_state_20260603_20260605.parquet
- forward_test/log/long_signals_20260603_20260605.json

### 2-3. 6/4 LONG 첫 OOS Signals
- 종목 list: 000157, 03473K, 003650, 006405, 058650, 071055, 000155, 065710, 052330, 005389
- 우선주 비중: 최소 4종목 (03473K, 071055, 000155, 005389)
- ★ 진단 필요: 우선주 alpha contamination 여부

### 2-4. 미해결 issue
- 6/3 OOS: KOSPI 영업일 list에서 누락 (6/3은 영업일이지만 T-2 계산 불가)
- 6/5 OOS: T-2 = 6/2 잔고 fetch 실패 (장 마감 전 시도)
- 6/4 OOS만 진짜 신호 생성됨

---

## 3. ★★★ 우선주 발견 — Critical Finding

### 3-1. 사실
- 6/4 LONG 10종목 중 우선주 ≥ 4종목 (40%)
- 우선주 코드 패턴: 끝자리 5 또는 'K' suffix
  - 03473K (SK이노베이션우)
  - 071055 (LG우)
  - 000155 (두산우)
  - 005389 (현대차2우B)
- 보통주: 000157, 003650, 006405, 058650, 065710, 052330 (일부 ETF 가능)

### 3-2. 가설
- NEUTRAL × bot z_ell (저유동성) selection은 우선주에 자주 매칭
- 우선주 = 유동성 낮음 = z_ell 하위에 자주 위치
- in-sample alpha (+107.70bp k=20)의 일부가 우선주 effect 가능성
- Sharpe 0.686 LOCK의 일부 = 우선주 contamination

### 3-3. 검증 필요
- in-sample 백테스트에서 우선주 entry 비율
- 우선주 제외 시 Sharpe 변동
- 우선주만 따로 backtest

### 3-4. 가능 시나리오
- A. 우선주 contribution 미미 → Sharpe 거의 유지 → 안전, v12 LOCK 신뢰
- B. 우선주 contribution 큼 → Sharpe 하락 → v12 LOCK 재검토 필요
- C. 우선주 자체가 한국 시장 특수 alpha → 별도 leg 분리 운용
- D. 우선주 alpha + 보통주 alpha 각각 존재 → dual portfolio

---
## 4. ★ 진단 우선순위 (다음 세션 즉시 작업)

### 4-1. Step 1: 우선주 영향 검증 (★ 최우선)

목적:
- v12 LOCK Sharpe 0.686이 진짜 alpha인지 우선주 effect인지 판정
- in-sample 9.4년 backtest에서 우선주 entry 비율 측정
- 우선주 제외 시 Sharpe / MDD / CAGR 재계산

방법:
- v12 LOCKED config 그대로 + 우선주 코드 식별
- 우선주 식별 rule:
  - 끝자리 5 (보통 우선주)
  - 끝자리 7 (2우B)
  - 9 suffix (구형)
  - K suffix (신형 우선주)
- backtest 2 variants:
  1. 보통주 only
  2. 우선주 only
- 비교: Sharpe / CAGR / MDD / hit rate

산출:
- data/sim/v2_gamma_common_only.parquet
- data/sim/v2_gamma_pref_only.parquet
- data/sim/diag_pref_breakdown.parquet

판정:
- 보통주 Sharpe > 0.6 → v12 LOCK 안전
- 보통주 Sharpe < 0.5 → v12 재검토
- 우선주 Sharpe > 0.6 → 별도 leg 운용 검토

### 4-2. Step 2: 6/3, 6/5 데이터 보완

목적:
- 6/3 OOS 영업일 확인 (df_sv_v2 last = 6/2, 6/3은 영업일)
- 6/5 OOS T-2 (=6/2) 잔고 재시도

방법:
- pykrx 영업일 list와 df_sv_v2 date 비교
- 장 마감 후 (18시 이후) 6/2 잔고 재시도
- 또는 다음 거래일 6/8 (월) 시점에 일괄 fetch

### 4-3. Step 3: Daily Routine 확립

목적:
- 매일 1셀 실행 가능 template
- forward_test/log/{date}.parquet 누적
- rolling metrics 계산

방법:
- 단일 셀 (Daily Run Template)
- input: 어제까지 log + 오늘 OOS fetch
- output: 오늘 signal + position update + git push

### 4-4. Step 4: Realized Return 계산

목적:
- 6/4 entry → 6/5 close 1일 PnL 측정
- in-sample baseline 대비 첫 OOS metric
- 정직: 통계적 의미 0, infrastructure 검증 용

방법:
- 6/4 LONG 10종목의 6/5 close return 계산
- equal weight 평균
- log 저장

---

## 5. ★ 다음 세션 진입 사양

### 5-1. Setup (~40초)
- 새 노트북
- 합본 셀 paste & run (v13 §10-1)
- EXPECTED_HEAD_PREFIX = "92b047f" (또는 v13 push 후 hash)

### 5-2. 첫 메시지 권장

MSM Phase 2 (Forward Test) 진행 중.
MSM_HANDOFF_2026_06_05_v13.md 참고.

현재:
- v12 LOCK 유지 (Sharpe 0.686, MDD -33.13%, CAGR 16.48%)
- Forward Test infrastructure 확립 완료
- 6/4 첫 OOS LONG signal 10종목 생성
- ★ 우선주 비중 40% 발견 — alpha contamination 의심

다음 우선순위:
1. 우선주 영향 검증 (in-sample 재backtest)
2. 6/5+ 데이터 누적
3. Daily routine 확립
4. Realized PnL 측정

§1 추측 X, §6 3축, §7 옵션→형 결정→실행, 단일 셀.

### 5-3. Claude 첫 응답 할 것
1. v13 §0 절대 원칙 정독 (#12 forward test 발견)
2. v13 §1 LOCKED VALUES + v12 config 확인
3. v13 §3 우선주 발견 정독
4. v13 §4 진단 우선순위 4단계 옵션 송부
5. 형 GO 받고 실행

---

## 6. ★ 즉시 실행 가능 옵션 (다음 세션)

| 옵션 | 내용 | 시간 |
|---|---|---|
| **A** | **우선주 영향 검증** (in-sample 재backtest with/without 우선주) | ~5분 |
| **B** | **Daily routine 확립** (cron-style template + 6/5 PnL 측정) | ~3분 |
| **C** | **A + B 결합** (1셀) | ~8분 |
| **D** | choonsimi-premium 6/26 결과 후 dual-engine 검토 시작 | 별도 |
| **E** | STEP 9 (state v3 — sector + market regime + uptick 등) | ~30분 |

권장: **A** (우선주 발견은 정직 검증 필수, v12 LOCK 신뢰성 직결)

---
## 7. 파일 인벤토리 (commit 92b047f 기준)

choonsimi-msm/
- MSM_HANDOFF_2026_06_02.md (v1~v4)
- MSM_HANDOFF_2026_06_03_v6.md
- MSM_HANDOFF_2026_06_04_v7~v11.md
- MSM_HANDOFF_2026_06_05_v12.md (MSM v2 LOCK)
- MSM_HANDOFF_2026_06_05_v13.md ← 이 문서 (Phase 2 진입)
- STEP8_PROGRESS.md
- README.md
- msm_data_supplement.ipynb
- msm_data_ingestion.ipynb
- msm_state_vector.ipynb
- data/
  - raw/
    - active/, delisted/, macro/
    - vkospi_10y_*.csv
    - short/
      - volume/ (39 files, ~54MB)
      - balance/ (38 files, ~92MB)
  - universe/universe_msm.csv
  - state/
    - state_vector/year=*.parquet (v1)
    - regime/year=*.parquet (v1)
    - transition/ (v1)
    - edge/edge_field.parquet (v1)
    - tradeable/year=*.parquet (v1)
    - state_vector_v2/year=*.parquet (v2, 259MB)
    - edge_v2/edge_field_v2.parquet, diag_*.parquet
  - sim/
    - equity_curve_shock_short_only.parquet (STEP 6 LOCKED)
    - equity_t4_v1.parquet (STEP 7 V1 LOCKED)
    - v2_short_only/long_only/long_short.parquet (STEP 8.6)
    - v2_gamma_best.parquet (MSM v2 BEST LOCKED) ★
    - step87_gamma_sweep.parquet
- forward_test/                    ★ v13 신규 (Phase 2)
  - baseline.json
  - README.md
  - metrics/day1_setup.parquet
  - state/oos_state_20260603_20260605.parquet
  - log/long_signals_20260603_20260605.json

---

## 8. 본 세션 (#9) commit 이력

- 92b047f  MSM Phase 2: Forward test OOS 6/4 LONG signals + state v2
- d94cd00  MSM Phase 2: Forward Test infrastructure (Day-1 setup, OOS 2d collected)
- 559a65e  MSM HANDOFF v12: STEP 8 LOCKED. MSM v2 = TRADEABLE SYSTEM

---

## 9. ★ 실수 누적 (v12 #1~#47 + v13 신규)

v12 #43~#47 유지.

v13 신규:
- #48: pykrx 1.2.8 영문 column 변경 미대응. KRX response가 영문 (ISU_CD, BAL_QTY, LIST_SHRS, BAL_AMT, MKTCAP, BAL_RTO) 으로 와도 wrap에서 한국어 column 가정으로 KeyError. 우회: core.전종목_공매도_잔고() 직접 호출 + 영문→snake_case 변환. 재발 방지: KRX format 변경 모니터링, pykrx 깨질 가능성 고려한 fallback wrapper 필수.

- #49: KOSPI 영업일 list와 df_sv_v2 date 불일치 발생. 6/3은 영업일이지만 stock.get_index_ohlcv('20260520','20260605','1001') 결과 list에 누락. 원인: pykrx index OHLCV API의 한계 또는 cache. 재발 방지: 영업일 source를 df_sv_v2['date'] 직접 사용 또는 별도 calendar API.

- #50: ★ Forward test 첫 OOS에서 우선주 비중 40% 발견. in-sample alpha의 일부가 우선주 effect 가능성. v12 LOCK이 contamination 포함했을 위험. 재발 방지: 다음 backtest 시 우선주/보통주 분리 분석 의무화. selection rule에 우선주 필터 옵션 검토.

---

## 10. ★ 다음 세션 합본 셀

### 10-1. Setup 셀 (paste & run, ~40초)

import os, subprocess, shutil, time
from pathlib import Path

t0 = time.time()
REPO = '/content/choonsimi-msm'
EXPECTED_HEAD_PREFIX = 'XXXXXXX'  # ← v13 push 후 v13 commit hash로 갱신

from google.colab import userdata
GH = userdata.get('GH_TOKEN')
assert GH

if Path(REPO).exists():
    shutil.rmtree(REPO)
url = f'https://x-access-token:{GH}@github.com/stanleyim/choonsimi-msm.git'
r = subprocess.run(['git', 'clone', url, REPO], capture_output=True, text=True)
assert r.returncode == 0
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

# Load v2 LOCKED config equity
df_eq_v2_best = pd.read_parquet('data/sim/v2_gamma_best.parquet')
assert len(df_eq_v2_best) == 2307
print(f'v2 BEST equity: {len(df_eq_v2_best)} rows')

# Forward test infrastructure
ft_path = Path('forward_test')
assert ft_path.exists()
print(f'forward_test/: OK')

print(f'준비 완료 {time.time()-t0:.1f}s')

### 10-2. 우선주 검증 셀 (옵션 A)

다음 세션에서 Claude가 송부할 단일 셀 구조:

1. 우선주 식별 함수
   - 끝자리 5 (보통 우선주)
   - 끝자리 7 (2우B)
   - 끝자리 9 (구형)
   - K suffix (신형)

2. v2 LOCKED config 그대로 backtest 재실행 with 우선주 식별
   - LONG entry 시 우선주 비율 측정
   - SHORT entry 시 우선주 비율 측정
   - 일별/연도별 우선주 distribution

3. 3 backtest variants
   - All (현재 v12 BEST = 100% baseline)
   - Common only (우선주 제외 LONG)
   - Pref only (우선주만 LONG)

4. 비교 metric
   - CAGR / Sharpe / MDD 각각
   - 우선주 contribution % to alpha

5. 판정
   - common Sharpe > 0.6 → v12 안전
   - common Sharpe < 0.5 → v12 재검토

---
## 11. Phase 2 진행 일정 (예상)

다음 세션:
- 우선주 검증 (~5분)
- 6/5+ 데이터 누적
- Daily routine template (~3분)
- 첫 OOS PnL 측정 (~3분)
- v14 핸드오프 (필요 시)

1주 후:
- 6/3 ~ 6/12 약 7거래일 누적
- Rolling Sharpe 초기 측정
- regime drift 1차 진단

1개월 후:
- 약 20거래일 누적
- Sharpe 통계 의미 시작
- choonsimi-premium 6/26 결과 비교 가능

3개월 후:
- ~60거래일 누적
- Sharpe 검증 가능 (CI 좁아짐)
- v15 또는 STEP 9 결정

---

## 12. 핵심 한 줄

v12 LOCK 유지. Forward Test infrastructure 확립 완료. 첫 OOS 6/4 LONG signal 10종목 생성 성공. 그러나 우선주 비중 40% 발견 (in-sample alpha contamination 의심). 다음 세션 즉시 작업 = 우선주 영향 검증. v12 Sharpe 0.686 신뢰성 직결.

---

## 13. 형의 다음 세션 분석 우선순위

1. 우선주 효과 검증 (in-sample 보통주만 backtest)
2. v12 LOCK 유지 vs 재검토 결정
3. 6/5+ daily routine 시작
4. Realized PnL 누적 (1~2주)
5. choonsimi-premium 6/26 결과 + MSM v2 비교 (dual-engine 검토 가능 시점)

---

## 14. 정직 메시지

v12 LOCK 시 Sharpe 0.686 도달은 진짜 진전.
그러나 forward test 첫 OOS에서 우선주 40% 발견.

이게 forward test의 진짜 가치:
  in-sample 백테스트가 못 본 risk가 즉시 드러남.

만약 우선주 alpha가 진짜라면:
  보통주에서도 비슷한 alpha 확인 필요.
  안 되면 우선주 의존 = fragile alpha.

만약 우선주 alpha가 contamination이라면:
  v12 LOCK 재검토. 보통주만 backtest로 v12.1 발행.

진단 결과 따라 결정:
  A. 보통주 Sharpe > 0.6 유지 → v12 LOCK 안전, 그대로 진행
  B. 보통주 Sharpe < 0.5 → v12 재검토, common-only LOCK
  C. 우선주만의 alpha 강함 → dual-leg 분리 운용 검토

이건 v12 LOCK 약점이 아니라
forward test 인프라의 첫 성공 사례.

---

**작성자**: Claude (MSM 세션 #9, Phase 2 진입)
**상태**: v12 LOCK 유지, Forward Test 인프라 확립, 우선주 의심 발견
**다음 작업**: 우선주 영향 검증 → v12 LOCK 안전성 판정

끝.
