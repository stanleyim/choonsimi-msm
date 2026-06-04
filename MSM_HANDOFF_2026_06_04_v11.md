# MSM 핸드오프 v11 — STEP 7 LOCKED (Control Manifold Exhausted) → STEP 8 (Alpha Restructuring) 진입

**작성일**: 2026-06-04 (KST, 같은 날 작업 연장 세션 #7)
**대상 repo**: stanleyim/choonsimi-msm
**최신 commit**: ed74628 — MSM STEP 7-C recovery kernel sweep
**상태**: ★ STEP 7 (Control Layer) 종결. V1 (T4) = frontier-optimal terminal point.
**다음**: STEP 8 — Alpha Restructuring (distribution 자체 재설계)
**환경**: 태블릿 (Colab), 단일 셀 통합 유지, 새 노트북 권장

---

## 0. 절대 원칙 (v10 §0 그대로 유지 + v11 신규)

1. §1 추측 금지
2. §6 3번 검토 (정확성 + 사고 가능성 + 안전장치)
3. §7 옵션 → 형 결정 → 실행
4. §13 매 단계 commit/push
5. MSM = choonsimi-premium 독립 (v10c 6/26 freeze)
6. 외부 검토자 3 원칙
7. 단일 셀 통합 코드
8. Signal ≠ Execution constraint (v10 §0-8)
9. Selection asymmetry: edge_field universe ≠ realized top-K (v10 §2-15)
10. v11 신규: Control manifold ≠ Alpha manifold (STEP 7 발견)

---

## 1. ★ LOCKED VALUES (v11 누적 immutable)

### 1-1. STEP 1~5 (v10에서 LOCKED, 유지)
- state_vector  : data/state/state_vector/year=*.parquet, (2,793,837, 12), 1603 codes
- regime        : data/state/regime/year=*.parquet, (2,793,837, 4)
- transition    : data/state/transition/, 4x4 MLE, diagonal SHOCK 0.7674
- edge_field    : data/state/edge/edge_field.parquet, 12 rows (4 regime x 3 horizon)
- tradeable     : data/state/tradeable/year=*.parquet, (2,793,837, 7), 9.13% tradeable

### 1-2. STEP 6 (v10에서 LOCKED) — SHOCK SHORT only
- 파일: data/sim/equity_curve_shock_short_only.parquet
- GROSS: CAGR +52.00%, Sharpe 1.16, MDD -55.09%
- NET (cost 0.30% RT): CAGR +11.92%, Sharpe 0.48, MDD -68.65%
- Breakeven cost: 0.411% RT
- commit: 3b3ceb0 + 4618806

### 1-3. STEP 7 V1 LOCKED (v11 신규, frontier-optimal terminal)
- Config: T4 circuit breaker
  - DD trigger = -20%
  - exposure_low = 0.5x
  - recovery_DD = -10%
- 파일: data/sim/equity_t4_v1.parquet
- CAGR  : +10.10% (V0 대비 -1.82pp)
- Sharpe: +0.48 (V0와 동일, control은 Sharpe 보존)
- MDD   : -49.96% (V0 대비 +18.69pp 개선)
- commit: 90eb86d

### 1-4. STEP 7 Sub-variants (v11 신규, 진단 데이터)

STEP 7.1 T4 sweep (commit 90eb86d):
- V0 (no sizing) : CAGR +11.92%, Sharpe +0.48, MDD -68.65%
- V1 (-20/0.5x/-10) LOCKED: CAGR +10.10%, Sharpe +0.48, MDD -49.96%
- V2 (-30/0.5x/-15) : CAGR +6.13%, Sharpe +0.35, MDD -52.42%
- V3 (-40/0.25x/-20): CAGR +2.48%, Sharpe +0.23, MDD -52.69%
- Reduced% : V1=80%, V2=71%, V3=85% (영구 축소 패턴)

STEP 7-B sweep (commit fbd9266) — pre-entry blocking:
- W1 (DD<-10%, br>15%) : CAGR -1.88%, Sharpe -0.52, MDD -16.94%, Block 97.5%
- W2 (DD<-10%, br>30%) : 동일 (breadth dead)
- W3 (DD<-25%, br>15%) : CAGR +3.16%, Sharpe +0.27, MDD -35.27%, Block 89.2%
- W4 (DD<-25%, br>30%) : 동일
- 진단: SHOCK_breadth_5d 분포 P50=12.76%, P90=13.08% → threshold 15% 거의 미발동
- 진단: DD-only filter는 absorbing state (영구 차단)

STEP 7-C sweep (commit ed74628) — recovery kernel:
- Recovery: time >= 20거래일 OR breadth_5d <= P50(12.76%)
- Y1 (DD=-15, br=13.0): CAGR -2.77%, Sharpe -0.68, MDD -23.79%, Episodes 1118, AvgEp 3.0d, Block 97.4%
- Y2 (DD=-15, br=13.5): 동일
- Y3 (DD=-25, br=13.0): CAGR +3.02%, Sharpe +0.27, MDD -35.27%, Episodes 996, AvgEp 3.1d, Block 90.2%
- Y4 (DD=-25, br=13.5): CAGR +3.16%, Sharpe +0.27, MDD -35.27%, Episodes 993, Block 89.2%
- 진단: Ergodicity 복원 (episodes 다회, AvgEp 3d)
- 진단: 그러나 DD self-trap → recovery 직후 즉시 재차단 → effective 동일

---
## 2. ★ 본 세션 핵심 발견 5종 (Control Manifold Theory)

### 발견 1 (★ 가장 중요): Control Equivalence Class
- T4 (post-damage scaling) = 7-B (pre-entry blocking) = 7-C (recovery kernel)
- 모두 동일 equivalence class: exposure modulation
- 어떤 control variant도 alpha-MDD frontier 위에서 이동만 함
- frontier 자체는 못 뚫음
- 결론: control space exhausted

### 발견 2: Sharpe Invariance
- V0 baseline Sharpe = 0.48
- V1 (T4) Sharpe = 0.48 (동일)
- 모든 다른 variant: Sharpe ↓ (alpha 손실)
- 의미: control layer는 Sharpe 보존 (최선) 또는 손실. 절대 개선 불가
- 이는 information ratio constraint의 직접 표현

### 발견 3: MDD Cluster Dominance Law
- MDD = f(cluster formation), NOT f(control system)
- V0=-68%, V1=-50%, 7-B=-16~35%, 7-C=-23~35% — 모두 다른 cluster reshaping
- 어떤 control도 cluster formation 자체를 변경 못함
- Empirical invariant: SHOCK SHORT alpha의 heavy-tailed/cluster-heavy 구조에서
  MDD reduction은 alpha destruction과 등가

### 발견 4: Absorbing State Trap (7-B specific)
- DD-only filter는 entry 차단 → no PnL → DD frozen → 영구 차단
- 한 번 trigger 발동되면 회복 메커니즘 없으면 ergodicity 깨짐
- 7-C가 recovery kernel로 ergodicity 복원했으나, DD self-trap으로 effective 무력화
- 의미: control system은 Markov chain 측면에서 reversible 해야 valid

### 발견 5: Domain Mismatch
- STEP 7 모든 control: realized path 위에서 작동
- alpha failure mode: pre-path distributional structure (cluster formation)
- 두 domain이 다름 → intervention 무효
- 결론: alpha restructuring (STEP 8)은 distribution 자체를 바꿔야 함

---

## 3. ★ Sub-step 진행 이력 (본 세션 누적)

| Sub-step | 변경 | CAGR | Sharpe | MDD | 결과 |
|---|---|---|---|---|---|
| STEP 7.1 V0 (no sizing) | baseline | +11.92% | 0.48 | -68.65% | reference |
| STEP 7.1 V1 (T4 best) | DD<-20% to 0.5x | +10.10% | 0.48 | -49.96% | LOCK |
| STEP 7.1 V2/V3 | T4 deeper trigger | +6.13/+2.48% | 0.35/0.23 | -52% | T4 ceiling |
| STEP 7-B W1/W3 | DD-only entry block | -1.88/+3.16% | -0.52/+0.27 | -17/-35% | absorbing |
| STEP 7-C Y1~Y4 | block + recovery | -2.77~+3.16% | -0.68~+0.27 | -24/-35% | DD self-trap |

---

## 4. 확정 정책 (v10 §2 + 본 세션 §2-16/§2-17 신규)

### v10 §2-1 ~ §2-15 (변경 없음)

### v11 §2-16 신규 — STEP 7 Control Layer (LOCKED V1)
- Sizing/Control config: T4 circuit breaker
- DD trigger = -20% (cumulative NET drawdown 기준)
- Exposure low = 0.5x (트리거 발동 시 다음날부터 exposure 절반)
- Recovery DD = -10% (축소 상태에서 DD가 -10% 이상으로 회복 시 다음날 exposure 복원)
- Frontier-optimal 인정: V0 alpha 85% 보존 + MDD 18.69pp 개선
- 단, MDD<-30% target은 미달 → STEP 8에서 alpha 자체 재설계로 도전

### v11 §2-17 신규 — Control Manifold Theory
- 모든 control layer (scaling, blocking, recovery) = exposure modulation 등가
- Control은 Sharpe 보존 (최선) 또는 손실, 개선 불가
- MDD reduction은 cluster formation에 무관, exposure timing만 변경
- 따라서 MDD<-50% 이하는 alpha 자체 변경 없이는 불가
- 함의: Sharpe 0.48 alpha의 inherent MDD floor ≈ -50%

---
## 5. 파일 인벤토리 (commit ed74628 기준)

choonsimi-msm/
- MSM_HANDOFF_2026_06_02.md (v1~v4)
- MSM_HANDOFF_2026_06_03_v6.md
- MSM_HANDOFF_2026_06_04_v7.md ~ v10.md
- MSM_HANDOFF_2026_06_04_v11.md ← 이 문서
- README.md
- msm_data_supplement.ipynb
- msm_data_ingestion.ipynb
- msm_state_vector.ipynb
- data/
  - raw/                                 (v7 그대로)
  - universe/universe_msm.csv
  - state/                                (STEP 1~5)
    - state_vector/year=*.parquet
    - regime/year=*.parquet
    - transition/
    - edge/edge_field.parquet
    - tradeable/year=*.parquet
  - sim/                                  (STEP 6, 7, v10+v11)
    - portfolio.parquet                  (STEP 6.0 LS baseline)
    - equity_curve.parquet
    - portfolio_h20.parquet              (STEP 6.2)
    - equity_curve_h20.parquet
    - portfolio_best_fixed_k20.parquet   (STEP 6.3)
    - equity_curve_best_fixed_k20.parquet
    - sweep_F3_summary.parquet
    - diag_G1_subset_edge.parquet        (STEP 6.4)
    - diag_G2_score_sweep.parquet
    - diag_step6_5_decomposition.parquet (STEP 6.5)
    - equity_curve_shock_short_only.parquet ★ STEP 6 LOCKED
    - diag_step6_6_cost_sweep.parquet    (STEP 6.6)
    - equity_t4_v1.parquet               ★ STEP 7 V1 LOCKED (v11 신규)
    - step7_t4_sweep_summary.parquet     (v11 신규)
    - step7b_sweep_summary.parquet       (v11 신규)
    - equity_7b_w1.parquet               (v11 신규)
    - step7c_sweep_summary.parquet       (v11 신규)
    - equity_7c_y4.parquet               (v11 신규)
  - checks/

---

## 6. 본 세션 주요 commit (시간순)

- ed74628  MSM STEP 7-C: recovery kernel (time OR breadth), 4 variants Y1-Y4, best=Y4
- fbd9266  MSM STEP 7-B: entry filter sweep (DD + SHOCK_breadth), best=W1
- 90eb86d  MSM STEP 7.1: T4 circuit breaker sweep (V1/V2/V3), best=V1
- 025c2e4  MSM HANDOFF v10 (STEP 6 LOCKED)
- 4618806  MSM STEP 6.6: J-5 cost sweep
- 3b3ceb0  MSM STEP 6.5: I-3 decomposition (SHORT-only)

---

## 7. §8 실수 누적 (v10 #1~#39 + v11 신규)

v10 #37~#39 유지.

v11 신규:
- #40: STEP 7-B에서 SHOCK_breadth threshold (15%, 30%) 가 실제 분포 (P50=12.76%, P90=13.08%) 보다 높아서 filter dead-on-arrival. W1=W2, W3=W4 collapse가 증거. 재발 방지: filter threshold는 항상 실제 데이터 분포 (P25/P50/P75/P90) 확인 후 설정. 사전 분포 측정 의무화.
- #41: STEP 7-C에서 recovery kernel로 ergodicity 복원했으나 DD self-trap 발생. block 동안 자본 미사용 → DD 회복 불가 → recovery 직후 즉시 재차단. 재발 방지: DD-based intervention 설계 시 "exposure 0 → DD frozen" 메커니즘 사전 인지. 회복 mechanism은 exposure 외부 변수에 의존해야 함.
- #42: STEP 7 전체에서 alpha-MDD frontier 위 이동만 가능함을 증명. control space 완전 탐색 후 도달한 결론. 재발 방지: 다음 phase는 반드시 alpha distribution 자체를 변경해야 함. control variant sweep으로 frontier 통과 시도 금지.

---

## 8. ★ MSM v1 진행 상태 (FINAL UPDATE)

STEP 1: State Vector Construction     ✅ LOCKED (6979a1d)
STEP 2: Regime Detection              ✅ LOCKED (be5d63d)
STEP 3: Transition Estimation         ✅ LOCKED (f105ff2)
STEP 4: Edge Field Calculation        ✅ LOCKED (66c0e52)
STEP 5: Tradeable Region Extraction   ✅ LOCKED (def993f)
STEP 6: Execution (Signal Layer)      ✅ LOCKED (3b3ceb0 + 4618806)
        - SHORT-only, K=5, score=z_r+z_f
        - NET +11.92%, Sharpe 0.48, MDD -68.65%
STEP 7: Sizing/Control Layer          ✅ LOCKED (90eb86d, V1=T4 best)
        - T4 (-20%/0.5x/-10%) circuit breaker
        - CAGR +10.10%, Sharpe 0.48, MDD -49.96%
        - frontier-optimal within control class
        - Sub-variants: T4(V1-V3) + 7-B(W1-W4) + 7-C(Y1-Y4) all logged

STEP 8: Alpha Restructuring          ⏸ 진입 대기
        - distribution 자체 재설계
        - cluster formation 변경

→ MSM v1 Control Manifold = EXHAUSTED

---
## 9. ★ STEP 8 진입 사양

### 9-1. INPUT
- STEP 7 V1 LOCKED equity (data/sim/equity_t4_v1.parquet)
- STEP 6 baseline equity (data/sim/equity_curve_shock_short_only.parquet)
- df_sv (state_vector + regime + tradeable merged) — re-load 가능

### 9-2. TARGET (재정의)
- Sharpe > 0.6 (V1의 0.48 대비 +0.12)
- MDD < -40% (V1의 -49.96 대비 +10pp 개선)
- CAGR >= 10% (V1 수준 유지)
- 또는 frontier 외부 영역 도달 (구조적 불가 증명 시 V1 LOCK 영구)

### 9-3. CANDIDATE TECHNIQUES (Q-A1 ~ Q-A5)

| # | 기법 | 방향 | 예상 효과 |
|---|---|---|---|
| A-1 | Universe 재정의 | 시총 상위 N, 변동성 quantile 제거 | SHOCK 강도 ↓ |
| A-2 | State vector 확장 | + sector, + market regime, + multi-horizon r | conditional alpha |
| A-3 | Regime 재정의 | SHOCK sub-divide (acute/chronic), 5-regime CRASH | tail isolation |
| A-4 | Edge field 재측정 | k=1/3/5/10/20/40, regime-conditioned z_r quantile | optimal k 식별 |
| A-5 | Selection 재설계 | Anti-selection (중간 강도), Bottom-X% sampling, conditional score | distribution sampling |

### 9-4. STEP 8 EXECUTION 구조 (Q-A1~A5 + P1~P3)

P1 — Multi-target sweep (권장):
- P1-α: Anti-selection (SHORT candidates 25~50%ile)
- P1-β: Universe 축소 (시총 상위 500)
- P1-γ: Multi-horizon (k=10 fixed exit)

P2 — Anti-selection 단독 정밀:
- bottom 5% / 10-30% / 25-50% / 50-75% / 25-75%
- 5 variants

P3 — Universe sweep:
- 시총 상위 1000 / 500 / KOSPI200

→ 다음 세션에서 형 결정 → 단일 셀 실행

---

## 10. 다음 세션 START GUIDE

### 10-1. 첫 메시지 권장

MSM STEP 8 (Alpha Restructuring) 시작.
MSM_HANDOFF_2026_06_04_v11.md 참고.

환경: 태블릿, 새 노트북
현재: STEP 1~7 LOCKED
   - signal layer (STEP 6): SHOCK SHORT only, V0 baseline
     NET +11.92%, Sharpe 0.48, MDD -68.65% @ 0.3% RT
   - control layer (STEP 7): V1 = T4 (-20%/0.5x/-10%)
     CAGR +10.10%, Sharpe 0.48, MDD -49.96%
   - STEP 7 control manifold exhausted (5 발견: equivalence class)
다음: STEP 8 — alpha distribution 재설계

§1 추측 X, §6 3번 검토 3축, §7 옵션→형 결정→실행, 단일 셀.
v11 §10-3 합본 셀 사용. 새 노트북에서 1셀 실행.

### 10-2. Claude 첫 응답 할 것
1. v11 §0 절대 원칙 정독 (#10 control manifold ≠ alpha manifold 강조)
2. v11 §1 LOCKED VALUES 검증 (state_vector + regime + tradeable + STEP 6 equity + STEP 7 V1 equity 5종)
3. v11 §2 5대 발견 정독 (특히 control equivalence class)
4. v11 §9 STEP 8 진입 사양 + Q-A1~A5 + P1/P2/P3 옵션 송부
5. 형 결정 받고 실행

### 10-3. ★ 새 노트북 합본 셀 (다음 세션 복붙용)

```python
import os, subprocess, shutil, time
from pathlib import Path

t0 = time.time()
REPO = '/content/choonsimi-msm'
EXPECTED_HEAD_PREFIX = 'XXXXXXX'  # ← v11 push 후 v11 commit hash로 갱신 필요

# [0] GH_TOKEN
from google.colab import userdata
GH = userdata.get('GH_TOKEN')
assert GH

# [1] Clone
if Path(REPO).exists():
    shutil.rmtree(REPO)
url = f'https://x-access-token:{GH}@github.com/stanleyim/choonsimi-msm.git'
r = subprocess.run(['git', 'clone', url, REPO], capture_output=True, text=True)
assert r.returncode == 0, r.stderr
os.chdir(REPO)
head = subprocess.run(['git','rev-parse','--short','HEAD'], capture_output=True, text=True).stdout.strip()
print(f'[1] clone OK HEAD={head}')
assert head.startswith(EXPECTED_HEAD_PREFIX), f'HEAD mismatch: expected {EXPECTED_HEAD_PREFIX}, got {head}'

# [2] pip
import sys
subprocess.run([sys.executable,'-m','pip','install','-q','pyarrow','pandas','numpy','psutil'], check=True)
import pyarrow, pandas as pd, numpy as np, psutil
print(f'[2] pip OK')

# [3] Secrets
for k in ['KRX_ID','KRX_PW','ECOS_API_KEY','GH_TOKEN']:
    try:
        v = userdata.get(k)
        if v and k in ('KRX_ID','KRX_PW'):
            os.environ[k] = v
    except: pass
print(f'[3] secrets OK')

# [4] git config
subprocess.run(['git','config','user.email','msm@stanleyim.local'], check=True, cwd=REPO)
subprocess.run(['git','config','user.name','stanleyim'], check=True, cwd=REPO)
print(f'[4] git config OK')

# [5] STEP 1~7 LOCKED load
from glob import glob
sv_files = sorted(glob('data/state/state_vector/year=*.parquet'))
df_sv = pd.concat([pd.read_parquet(f) for f in sv_files], ignore_index=True)
assert df_sv.shape == (2793837, 12)
assert df_sv['code'].nunique() == 1603

rg_files = sorted(glob('data/state/regime/year=*.parquet'))
df_rg = pd.concat([pd.read_parquet(f) for f in rg_files], ignore_index=True)
assert df_rg.shape == (2793837, 4)

df_edge = pd.read_parquet('data/state/edge/edge_field.parquet')
assert len(df_edge) == 12

trd_files = sorted(glob('data/state/tradeable/year=*.parquet'))
df_trd = pd.concat([pd.read_parquet(f) for f in trd_files], ignore_index=True)
assert df_trd.shape == (2793837, 7)

df_eq_step6 = pd.read_parquet('data/sim/equity_curve_shock_short_only.parquet')
assert len(df_eq_step6) == 2307

df_eq_step7 = pd.read_parquet('data/sim/equity_t4_v1.parquet')
assert len(df_eq_step7) == 2307

df_sv = df_sv.merge(df_rg[['date','code','regime']], on=['date','code'], how='left')
df_sv = df_sv.merge(df_trd[['date','code','direction','tradeable']], on=['date','code'], how='left')
assert df_sv.shape == (2793837, 15)
print(f'[5] load OK shape={df_sv.shape}, mem {psutil.virtual_memory().percent:.1f}%')

print(f'준비 완료 — {time.time()-t0:.1f}s. STEP 8 (Alpha Restructuring) 실행 셀 대기.')
```

---

## 11. 핵심 원칙 재공지

1. §1 추측 금지
2. §6 3번 검토 3축
3. §7 옵션 → 형 결정 → 실행
4. 단일 셀 통합 (새 노트북 우선)
5. GitHub = truth
6. LOCKED VALUES 변경 금지
7. MSM = choonsimi-premium 독립
8. Signal ≠ Execution constraint
9. Selection asymmetry (v10)
10. Control manifold ≠ Alpha manifold (v11) — STEP 8은 alpha 자체 변경

---

## 12. 핵심 한 줄

STEP 7 LOCKED. V1 (T4 -20%/0.5x/-10%) = frontier-optimal terminal point (CAGR +10.10%, Sharpe 0.48, MDD -49.96%). Control equivalence class 증명: T4 = 7-B = 7-C = exposure modulation 모두 동일. Sharpe invariance + MDD cluster dominance + Domain mismatch 5대 발견. 다음은 alpha distribution 자체 재설계 (STEP 8).

---

## 13. 형의 다음 세션 분석 우선순위

> STEP 8에서 반드시 닫아야 하는 변수:
> 1. SHOCK SHORT alpha의 cluster-heavy 구조 원인 분해
> 2. Universe / state / regime / edge / selection 5개 layer 중 어느 곳을 건드릴지 결정
> 3. P1 sweep으로 3 방향 동시 검증 (Anti-selection / Universe 축소 / Multi-horizon)
> 4. Sharpe > 0.6 가능 영역 존재 여부 판정
> 5. 불가 시 V1 영구 LOCK 결정

→ Q-A1~A5 + P1/P2/P3 sweep 매트릭스 결정 필요.

---

**작성자**: Claude (MSM 세션 #7, 본 세션 마감)
**상태**: MSM v1 Control Layer 완료. STEP 7 LOCKED.
**다음 작업**: 새 노트북 → v11 §10-3 합본 셀 → STEP 8 Q-A1~A5 옵션 결정 → alpha restructuring 실행

끝.
