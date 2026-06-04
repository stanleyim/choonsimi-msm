# MSM 핸드오프 v10 — MSM v1 Signal Layer 완료 (STEP 1~6 LOCKED) → STEP 7 (Sizing Layer) 진입

**작성일**: 2026-06-04 (KST, 같은 날 작업 연장)
**대상 repo**: stanleyim/choonsimi-msm
**최신 commit**: 4618806 — MSM STEP 6.6 cost sweep
**상태**: ★ MSM v1 Signal Layer 종결. SHOCK SHORT only alpha 확정.
**다음**: STEP 7 (Sizing / MDD Control Layer) — 설계 진입
**환경**: 태블릿 (Colab), 단일 셀 통합 유지, 새 노트북 권장 (셀 누적 9개 이력)

---

## 0. 절대 원칙 (v9 §0 그대로 유지)

1. §1 추측 금지
2. §6 3번 검토 (정확성 + 사고 가능성 + 안전장치)
3. §7 옵션 → 형 결정 → 실행
4. §13 매 단계 commit/push
5. MSM = choonsimi-premium 독립 (v10c 6/26 freeze)
6. 외부 검토자 3 원칙
7. 단일 셀 통합 코드
8. Signal ≠ Execution constraint (STEP 5 SHOCK SHORT 결정 근거, STEP 6.5 재확인)

---

## 1. ★ LOCKED VALUES (v10 누적 immutable)

### 1-1. STEP 1 (v7) — state_vector
- 파일: data/state/state_vector/year=*.parquet (10 partitions)
- shape: (2,793,837, 12) | universe: 1,603 codes | period: 2017-01-02 ~ 2026-06-02
- columns: date, code, r, sigma, v, ell, f, z_r, z_sigma, z_v, z_ell, z_f
- commit: 6979a1d

### 1-2. STEP 2 (v8) — regime
- 파일: data/state/regime/year=*.parquet (10 partitions)
- shape: (2,793,837, 4)
- 분포: TRANSITION 56.00% / RANGE 25.22% / SHOCK 12.70% / TREND 5.51% / NaN 0.57%
- commit: be5d63d

### 1-3. STEP 3 (v8) — transition
- 파일: data/state/transition/ (transition_matrix + count + yearly)
- Diagonal: SHOCK 0.7674 / TREND 0.1410 / RANGE 0.5195 / TRANSITION 0.7211
- commit: f105ff2

### 1-4. STEP 4 (v9) — edge_field
- 파일: data/state/edge/edge_field.parquet (12 rows = 4 regime × 3 horizon)
- 전 셀 |t|>4 통계 유의
- k=20 means: SHOCK -150.01bp, TREND +60.11bp, RANGE +60.82bp, TRANSITION +44.99bp
- commit: 66c0e52

### 1-5. STEP 5 (v10 신규) — tradeable_region
- 파일: data/state/tradeable/year=*.parquet (10 partitions, 2.06 MB)
- shape: (2,793,837, 7) | tradeable: 9.13% (255,159 rows)
- direction 분포: LONG 30.90% / SHORT 12.77% / NEUT 56.32% / NaN 0.57%
- liquidity_pass 49.19% / flow_pass 76.63%
- 연도별 안정: std 0.64pp, range [7.68%, 9.71%]
- commit: def993f

### 1-6. STEP 6 EXECUTION LAYER LOCKED (v10 신규, MSM v1 종결)
- best config: SHOCK SHORT only, K=5 baseline exit, weight 1/10, score = z_r + z_f
- 파일: data/sim/equity_curve_shock_short_only.parquet
- GROSS: CAGR +52.00%, Sharpe 1.16, MDD -55.09%
- NET (cost 0.30% RT): CAGR +11.92%, Sharpe 0.48, MDD -68.65%
- Breakeven cost: 0.411% RT (Sharpe>0.5 유지: cost ≤ 0.293% RT)
- commits: 3b3ceb0 (SHORT-only LOCK) + 4618806 (cost sweep)

---

## 2. ★ 본 세션 핵심 발견 5종 (alpha decomposition)

### 발견 1 (★ 가장 중요): LONG side selection은 mean reversion 유도
- STEP 4 universe edge: TREND k=20 +60.11bp, RANGE k=20 +60.82bp (positive)
- 실제 realized (top-K subset) k=20: TREND -7.68bp, RANGE -12.04bp (방향 반전)
- ratio: TREND -0.13x, RANGE -0.20x
- 해석: z_r + z_f 상위 = 이미 over-extended → mean reversion 진입
- 결론: LONG side에서 score = z_r+z_f는 reversal trigger로 작동

### 발견 2: SHORT side selection은 edge 증폭
- STEP 4 universe edge: SHOCK k=20 -150.01bp
- 실제 realized (bottom-K subset) k=20: SHOCK -173.76bp
- ratio: 1.16x (1.16× 증폭)
- 해석: SHOCK regime + 극단적 z_r+z_f bottom = continuation 강화
- 결론: SHORT side에서 score = z_r+z_f는 momentum 강화로 작동

### 발견 3: alpha = SHOCK SHORT 단일
- LONG side 전체 alpha: ~0 bp/거래 (12,653 entries 평균)
- SHORT side alpha: ~21 bp/day (9,604 entries)
- baseline LS GROSS +66.52%의 ~100% = SHORT side 기여
- LONG 거래 = noise + cost drag
- 검증: LONG only run → GROSS +4.76%, Sharpe 0.33 (Run 2)

### 발견 4: LONG score 재설계 시도 모두 실패
- z_r only: Sharpe 1.42 (LS env), LONG-only +6.29% / Sharpe 0.37
- z_f only: Sharpe 0.00 (no alpha)
- z_r+z_f: Sharpe 1.45 (LS env, best), LONG-only +4.76% / Sharpe 0.33
- z_r*sign(z_f): Sharpe -0.36 (역효과)
- -z_r (reversal): LONG-only +6.29% / Sharpe 0.37
- -z_r-z_f: LONG-only +5.37% / Sharpe 0.34
- 결론: LONG side에 score-rankable alpha 존재하지 않음

### 발견 5: Cost sensitivity = 선형, breakeven 0.411% RT
- daily cost: 4.17bp per 0.1% cost increment
- daily alpha: 21.40bp gross → cost 0.10% 증가시 net -4.17bp 감소 (선형)
- breakeven NET CAGR=0: cost 0.411% RT
- Sharpe>0.5 유지 한계: cost ≤ 0.293% RT
- MDD도 cost와 함께 악화: 0% cost -55%, 0.5% cost -84%

---
## 3. ★ Sub-step 진행 이력 (본 세션 누적)

| Sub-step | 변경 | NET CAGR | NET Sharpe | 결과 |
|---|---|---|---|---|
| STEP 5 | tradeable region 추출 | — | — | 9.13% density, feasibility 통과 |
| STEP 6.0 | LS K=5 baseline | -18.04% | -0.27 | cost > alpha |
| STEP 6.2 | LS K=20 hold | -17.17% | -0.27 | holding 늘려도 미개선 |
| STEP 6.3 (F-3) | baseline/fixed K=5/K=20 sweep | best -10.81% | -0.18 | 모두 NET 음수 → CASE C |
| STEP 6.4 (H-4) | G-1 subset edge + G-2 score sweep | (진단) | — | LONG side sign flip 발견 |
| STEP 6.5 (I-3) | SHORT-only + LONG variants | +11.92% | +0.48 | ★ alpha 정체 확정 |
| STEP 6.6 (J-5) | cost sensitivity sweep | (진단) | — | breakeven 0.411% RT |

---

## 4. 확정 정책 (v9 §2 + 본 세션 §2-14)

### v9 §2-1 ~ §2-13 (변경 없음)

### v10 §2-14 신규 — Execution Layer (STEP 6 LOCKED)
- Portfolio: SHORT-only (SHOCK regime) — LONG side는 alpha 없음 확정
- N_SHORT: 10
- Weight: 1/N (equal)
- Score: z_r + z_f (best across 4 variants)
- Selection: nsmallest by score (SHOCK regime, direction=-1, tradeable=True)
- Exit: tradeable==False OR holding>=5d
- Cost assumption: 0.30% RT (실거래 가정)

### v10 §2-15 신규 — Selection Asymmetry 원칙
- SHORT side: top-K selection ⊆ edge_field universe alpha 증폭
- LONG side: top-K selection ⊆ mean reversion 영역 진입 (alpha 반전)
- 원리: extreme score = momentum extreme = SHORT에서는 continuation, LONG에서는 exhaustion
- 함의: edge_field 측정은 universe 평균. realized alpha는 selection bias에 따라 다름. asymmetric.

---

## 5. 파일 인벤토리 (commit 4618806 기준)

choonsimi-msm/
- MSM_HANDOFF_2026_06_02.md (v1~v4)
- MSM_HANDOFF_2026_06_03_v6.md
- MSM_HANDOFF_2026_06_04_v7.md
- MSM_HANDOFF_2026_06_04_v8.md
- MSM_HANDOFF_2026_06_04_v9.md
- MSM_HANDOFF_2026_06_04_v10.md ← 이 문서
- README.md
- msm_data_supplement.ipynb
- msm_data_ingestion.ipynb
- msm_state_vector.ipynb
- data/
  - raw/ (v7 그대로)
  - universe/universe_msm.csv
  - state/
    - state_vector/year=*.parquet     (STEP 1, 10p)
    - regime/year=*.parquet           (STEP 2, 10p)
    - transition/                      (STEP 3)
    - edge/edge_field.parquet          (STEP 4)
    - tradeable/year=*.parquet         (STEP 5, 10p)  ← v10 신규
  - sim/                               ← v10 신규
    - portfolio.parquet                (STEP 6.0 LS baseline)
    - equity_curve.parquet
    - portfolio_h20.parquet            (STEP 6.2)
    - equity_curve_h20.parquet
    - portfolio_best_fixed_k20.parquet (STEP 6.3 best)
    - equity_curve_best_fixed_k20.parquet
    - sweep_F3_summary.parquet
    - diag_G1_subset_edge.parquet      (STEP 6.4)
    - diag_G2_score_sweep.parquet
    - diag_step6_5_decomposition.parquet (STEP 6.5)
    - equity_curve_shock_short_only.parquet ★ LOCKED FINAL
    - diag_step6_6_cost_sweep.parquet  (STEP 6.6)
  - checks/

---

## 6. 본 세션 주요 commit (시간순)

- 4618806  MSM STEP 6.6: J-5 cost sweep, breakeven=0.411% RT
- 3b3ceb0  MSM STEP 6.5: I-3 decomposition (SHORT-only + LONG variants)
- eaa4048  MSM STEP 6.4: H-4 diagnostic (G-1 subset edge + G-2 score sweep)
- 0b945bf  MSM STEP 6.3: F-3 sweep (baseline/K=5/K=20), best=fixed K=20
- f6eb2c5  MSM STEP 6.2: hold=20 backtest
- e830d00  MSM STEP 6: sizing+execution (LS, score=z_r+z_f)
- def993f  MSM STEP 5: tradeable region
- 4edd0fb  MSM HANDOFF v9
- 66c0e52  MSM STEP 4: edge field

---

## 7. §8 실수 누적 (v8 #1~#34 + v9 #35~#36 + v10 신규)

v9 #35~#36 유지.

v10 신규:
- #37: edge_field universe mean ≠ realized portfolio mean. 본 세션 STEP 6.4에서 발견. universe mean은 regime 전체 평균이고, top-K selection은 alpha distribution의 한쪽 꼬리만 사용. SHORT side는 증폭 (1.16×), LONG side는 반전 (-0.13~-0.20×). 재발 방지: 새 signal 설계시 universe edge 측정 후 realized top-K subset에서 재측정 (G-1 방법론) 의무화.
- #38: 합본 셀 paste 시 답변 본문의 표시용 markdown을 코드로 paste하면 SyntaxError. 본 세션 STEP 6.4 직후 발생. 재발 방지: 코드 블록은 항상 python 펜스 안에만. 표시용 표/숫자는 명백히 코드 아닌 형식 (파이프 사용).
- #39: triple-quote 문자열 안에 markdown 코드 펜스가 많을 때 Python parser가 incomplete input 오류. 본 세션 v10 작성 첫 시도에서 발생. 재발 방지: 긴 markdown 파일 작성은 chunk 분할 + raw string r''' ''' 사용 + append 모드로 누적.

---

## 8. ★ MSM v1 진행 상태 (FINAL)

STEP 1: State Vector Construction     ✅ LOCKED (6979a1d)
STEP 2: Regime Detection              ✅ LOCKED (be5d63d)
STEP 3: Transition Estimation         ✅ LOCKED (f105ff2)
STEP 4: Edge Field Calculation        ✅ LOCKED (66c0e52)
STEP 5: Tradeable Region Extraction   ✅ LOCKED (def993f)
STEP 6: Execution (Signal Layer)      ✅ LOCKED (3b3ceb0 + 4618806)
        - SHORT-only, K=5, score=z_r+z_f
        - NET CAGR +11.92%, Sharpe 0.48 @ 0.30% RT
        - Breakeven cost 0.411% RT
        - MDD -68.65% ← STEP 7 대상

STEP 7: Sizing / MDD Control Layer    ⏸ 진입 대기

→ MSM v1 Signal Engine = COMPLETE

---

## 9. ★ STEP 7 진입 사양

### 9-1. INPUT
- SHOCK SHORT signal (LOCKED)
- equity_curve_shock_short_only.parquet (baseline equity 곡선)
- daily entries/exits 로그
- cost curve (0~0.5% sensitivity 확보됨)

### 9-2. TARGET
- MDD < -30% (현재 -68.65% → 절반 이하)
- Sharpe 유지 또는 ↑ (현재 0.48 @ cost 0.30%)
- CAGR 손실 최소화 (가능하면 +10% 이상 유지)

### 9-3. CANDIDATE TECHNIQUES (Q-T1~Tn 후보)

| # | 기법 | 효과 추정 |
|---|---|---|
| T-1 | Volatility targeting (portfolio annualized vol = const) | MDD ↓ 가능, CAGR ↓ 약간 |
| T-2 | Regime intensity scaling (|z_r| 강도별 weight) | upside capture |
| T-3 | Position-level stop loss (-X% per name) | tail risk 컷, 시그널 conflict |
| T-4 | Portfolio-level drawdown circuit breaker (MDD>Y% 시 size halve) | MDD bound 가능 |
| T-5 | Score-weighted sizing (|score| 큰 종목 weight ↑, capped) | concentration 위험 |
| T-6 | Kill-switch (consecutive loss days N >= K → halt) | tail event 차단 |
| T-7 | Diversification floor (correlation matrix 기반 capping) | 복잡도 ↑ |

### 9-4. STEP 7 EXECUTION 구조 (사전 제안)
- Q-T1: vol target 도입 여부 (Y/N + target %)
- Q-T2: regime intensity scaling 여부
- Q-T3: stop loss 여부 (포지션 -X%)
- Q-T4: circuit breaker (MDD -Y%에서 size halve)
- Q-T5: score weighting 여부
- Q-T6: kill-switch 여부
- Q-T7: 조합 최소 set

→ 다음 세션에서 형 결정 → 단일 셀 실행

---

## 10. 다음 세션 START GUIDE

### 10-1. 첫 메시지 권장

MSM STEP 7 (Sizing / MDD Control Layer) 시작.
MSM_HANDOFF_2026_06_04_v10.md 참고.

환경: 태블릿, 새 노트북
현재: STEP 1~6 LOCKED
   - signal: SHOCK SHORT only (NET +11.92%, Sharpe 0.48, MDD -68.65% @ 0.3% RT)
   - alpha = SHOCK regime SHORT 단일 (LONG side dead 확정)
   - cost breakeven: 0.411% RT
다음: STEP 7 — MDD 컨트롤 (target < -30%)

§1 추측 X, §6 3번 검토 3축, §7 옵션→형 결정→실행, 단일 셀.
v10 §10-3 합본 셀 사용. 새 노트북에서 1셀 실행.

### 10-2. Claude 첫 응답 할 것
1. v10 §0 절대 원칙 정독
2. v10 §1 LOCKED VALUES 검증 (state_vector + regime + transition + edge + tradeable + equity_curve_shock_short_only 6종)
3. v10 §2 5대 발견 정독 (특히 #37 selection asymmetry)
4. v10 §9 STEP 7 사양 + Q-T1~T7 옵션 송부
5. 형 결정 받고 실행

### 10-3. ★ 새 노트북 합본 셀 (다음 세션 복붙용)

```python
import os, subprocess, shutil, time
from pathlib import Path

t0 = time.time()
REPO = '/content/choonsimi-msm'
EXPECTED_HEAD_PREFIX = 'XXXXXXX'  # ← v10 push 후 v10 commit hash로 갱신 필요

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

# [5] STEP 1~6 LOCKED load
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

df_sv = df_sv.merge(df_rg[['date','code','regime']], on=['date','code'], how='left')
df_sv = df_sv.merge(df_trd[['date','code','direction','tradeable']], on=['date','code'], how='left')
assert df_sv.shape == (2793837, 15)
print(f'[5] load OK shape={df_sv.shape}, mem {psutil.virtual_memory().percent:.1f}%')

print(f'준비 완료 — {time.time()-t0:.1f}s. STEP 7 (Sizing Layer) 실행 셀 대기.')
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
8. Signal ≠ Execution constraint (#15)
9. Selection asymmetry: edge_field universe ≠ realized top-K (v10 §2-15 신규)

---

## 12. 핵심 한 줄

STEP 6 LOCKED. MSM v1 alpha 정체 확정: SHOCK SHORT 단일 (Sharpe 1.16 gross, NET +11.92% @ 0.30% RT). LONG side dead 확정 (4 score variants 모두 Sharpe <0.4). Breakeven cost 0.411% RT — 실거래 가능 영역. MDD -68.65% 미해결 → STEP 7 sizing layer 진입.

---

## 13. 형의 다음 세션 분석 우선순위

> STEP 7에서 반드시 닫아야 하는 변수:
> 1. MDD < -30% 달성 가능한 sizing 기법 식별
> 2. Sharpe 유지 또는 개선 (목표 0.5+)
> 3. CAGR 손실 최소화 (10%+ 유지)
> 4. tail risk (SHOCK 클러스터 폭주) 대응 구조

→ Q-T1~T7 옵션 매트릭스 + 각 기법 단독/조합 검증 sweep 필요.

---

**작성자**: Claude (MSM 세션 #6, 본 세션 마감)
**상태**: MSM v1 Signal Layer 완료. STEP 6 LOCKED.
**다음 작업**: 새 노트북 → v10 §10-3 합본 셀 → STEP 7 Q-T1~T7 옵션 결정 → sizing layer 실행

끝.
