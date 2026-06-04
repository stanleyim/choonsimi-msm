# MSM 핸드오프 v8 — STEP 1~3 완료 (Transition Estimation LOCKED)

**작성일**: 2026-06-04
**대상 repo**: stanleyim/choonsimi-msm
**최신 commit**: f105ff2 — MSM STEP 3 transition matrix
**상태**: ★ MSM v1 STEP 3 (Transition Estimation) 완료 — LOCKED
**다음**: STEP 4 (Edge Field Calculation)
**환경**: 태블릿 (Colab), 단일 셀 통합 유지

---

## 0. 절대 원칙 (v7 §0 그대로)

1. §1 추측 금지
2. §6 3번 검토 (정확성 + 사고 가능성 + 안전장치)
3. §7 옵션 → 형 결정 → 실행
4. §13 매 단계 commit/push
5. MSM = choonsimi-premium 독립 (v10c 6/26 freeze)
6. 외부 검토자 3 원칙
7. 단일 셀 통합 코드

---

## 1. ★ LOCKED VALUES (v8 누적 immutable)

### 1-1. STEP 1 (v7에서 LOCK)
- state_vector.parquet (PT_year, 10 partitions)
- shape: (2,793,837, 12)
- universe: 1,603 codes
- period: 2017-01-02 ~ 2026-06-02
- columns: date, code, r, sigma, v, ell, f, z_r, z_sigma, z_v, z_ell, z_f
- commit: 6979a1d

### 1-2. STEP 2 (v8 신규 LOCK)
- regime.parquet (PT_year, 10 partitions)
- shape: (2,793,837, 4)
- columns: date, code, regime, pool_size
- size: total 1.09 MB, max 0.12 MB
- commit: be5d63d

분포:
- TRANSITION: 1,564,490 (56.00%)
- RANGE:        704,657 (25.22%)
- SHOCK:        354,854 (12.70%)
- TREND:        153,815 ( 5.51%)
- NaN:           16,021 ( 0.57%)

NaN 원인: z_sigma NaN 일치 (워밍업 + pool<100, 2017-01-02~01-13)
연도별 안정성: 모든 regime 변동폭 < 1.4%p

### 1-3. STEP 3 (v8 신규 LOCK)
- transition/transition_matrix.parquet (4×4 MLE)
- transition/transition_count.parquet  (4×4 raw count)
- transition/transition_yearly.parquet (long-form 연도별)
- commit: f105ff2

Transition matrix P(S_t+1 | S_t) — full sample:

|            | SHOCK  | TREND  | RANGE  | TRANSITION |
|------------|--------|--------|--------|------------|
| SHOCK      | 0.7674 | 0.0089 | 0.0074 | 0.2163     |
| TREND      | 0.0386 | 0.1410 | 0.2850 | 0.5354     |
| RANGE      | 0.0130 | 0.0738 | 0.5195 | 0.3937     |
| TRANSITION | 0.0430 | 0.0492 | 0.1867 | 0.7211     |

Diagonal persistence:
- SHOCK:      0.7674  (★ 단발 아님, 연속 클러스터)
- TREND:      0.1410  (★ 가장 unstable, 평균 dwell ~1.16일)
- RANGE:      0.5195  (느슨한 평형)
- TRANSITION: 0.7211  (기본 상태)

Row entropy:
- H(SHOCK)      = 0.6125  (가장 결정적)
- H(TREND)      = 1.0942  (가장 분산)
- H(RANGE)      = 0.9560
- H(TRANSITION) = 0.8326

Valid pairs: 2,776,216 / 2,793,837 (99.37%)
0-count cells: 0 / 16  (MLE 그대로 완전)
Row min count: 153,729
연도별 diagonal 변동폭: 모든 regime < 4%p (stationarity 실증)

---

## 2. ★ 확정 정책 (v7 §2 + v8 신규)

### 2-1 ~ 2-9 (v7 그대로, 변경 없음)
- R1: 거래정지일 행 제거 (volume!=0 AND trade_value!=0)
- U1: Universe 1603 (LOCKED)
- G1: lookback 50% 가드
- P_R5: r 극단값 무처리
- r = log(close_adj_t / close_adj_{t-1})
- f = (inst_5d + foreign_5d) / trade_value_5d
- Foreign 한도소진률 미사용
- Cross-sectional z-score (매일별)
- 저장 형식: PT_year

### 2-10. v8 신규 — Regime 정의 (STEP 2)
- 우선순위: SHOCK > TREND > RANGE > TRANSITION
- 사용 축: z_r, z_sigma (z_v/z_f/z_ell 미사용 — STEP 4 이연)
- Threshold: cross-section daily percentile

조건:
- SHOCK:      z_sigma ≥ P90  OR  |z_r| ≥ P95
- TREND:      |z_r| ≥ P80    AND z_sigma ≤ P60
- RANGE:      |z_r| ≤ P40    AND z_sigma ≤ P50
- TRANSITION: 나머지

NaN 조건:
- z_r is NaN OR z_sigma is NaN → regime = NaN
- pool_size < 100              → regime = NaN

### 2-11. v8 신규 — Transition 추정 (STEP 3)
- 단위: market-wide (per-stock X)
- Time step: 1d (next trading day)
- 방법: MLE (단순 count → row normalize)
- NaN: pair drop (S_t 또는 S_{t+1} NaN → 제외)
- 시점: full-sample (연도별은 sanity 보조)
- Pair 추출: code별 그룹 내 shift (group boundary 자동 격리)

---

## 3. 파일 인벤토리 (commit f105ff2 기준)

choonsimi-msm/
- MSM_HANDOFF_2026_06_02.md (v1~v4)
- MSM_HANDOFF_2026_06_03_v6.md
- MSM_HANDOFF_2026_06_04_v7.md
- MSM_HANDOFF_2026_06_04_v8.md ← 이 문서
- README.md
- msm_data_supplement.ipynb
- msm_data_ingestion.ipynb
- msm_state_vector.ipynb
- data/
  - raw/ (v7 그대로)
  - universe/universe_msm.csv
  - state/
    - state_vector/year=*.parquet   (STEP 1)
    - regime/year=*.parquet         (STEP 2, v8 신규)
    - transition/                    (STEP 3, v8 신규)
      - transition_matrix.parquet
      - transition_count.parquet
      - transition_yearly.parquet
  - checks/

---

## 4. 본 세션 (#5) 주요 commit

- f105ff2  MSM STEP 3: transition matrix (market-wide, 1d, MLE, NaN drop, 4x4 + yearly sanity)
- be5d63d  MSM STEP 2: regime labeling (rule-based, z_r/z_sigma percentile, priority SHOCK>TREND>RANGE>TRANSITION)
- 3756e6d  MSM HANDOFF v7: STEP 1 완료 — LOCKED baseline
- 6979a1d  MSM STEP 1: state_vector year partitions

---

## 5. §8 실수 누적 (v7 #1~#32 + v8 신규)

v7 #29~#32 유지.

v8 신규:
- #33. 인계서 작성 시 외곽 triple-quote 사용 — 본문 내부에 markdown code fence 다수 포함되면 SyntaxError 발생.
- #34. %%writefile 매직도 본문에 markdown code fence 포함 시 셀 조기 종료 발생. 파일 절반만 기록됨. 재발 방지: 인계서 파일 작성은 반드시 bash heredoc (cat << UNIQUE_TOKEN) 사용. 본문에 backtick 3개 fence 절대 포함 금지. 코드 블록은 들여쓰기로 대체.

---

## 6. ★ MSM v1 진행 상태

- STEP 1: State Vector Construction   ✅ LOCKED (6979a1d)
- STEP 2: Regime Detection            ✅ LOCKED (be5d63d)
- STEP 3: Transition Estimation       ✅ LOCKED (f105ff2)
- STEP 4: Edge Field Calculation      ⏸ 다음
- STEP 5: Tradeable Region Extraction ⏸

---

## 7. 다음 세션 START GUIDE

### 7-1. 첫 메시지 권장

    MSM STEP 4 (Edge Field Calculation) 시작.
    MSM_HANDOFF_2026_06_04_v8.md 참고.

    환경: 태블릿
    현재: STEP 1~3 LOCKED
    다음: STEP 4 Edge Field 설계 → Q-E1~Q-E5 결정 → 구현

    §1 추측 X, §6 3번 검토 3축, §7 옵션→형 결정→실행, 단일 셀.
    v8 §7-3 setup 셀 사용. Q-E1 결정 요청.

### 7-2. Claude 첫 응답 할 것
1. v8 §0 절대 원칙 정독
2. v8 §1 LOCKED VALUES 검증 (state_vector + regime + transition 3종)
3. v8 §7-3 setup 셀 송부
4. STEP 4 방법론 옵션 Q-E1 제시 (3축 검토 포함)
5. 형 GO 받고 진행

### 7-3. ★ 전체 일괄 setup 셀 (다음 세션 복붙용)

    import os, subprocess
    from pathlib import Path
    import pandas as pd
    import numpy as np

    %cd /content
    !rm -rf /content/choonsimi-msm
    !git clone https://github.com/stanleyim/choonsimi-msm.git
    %cd /content/choonsimi-msm

    !pip install -q pykrx finance-datareader pyarrow requests
    import pykrx, pyarrow, FinanceDataReader, requests
    print(f'pykrx={pykrx.__version__} pyarrow={pyarrow.__version__} fdr={FinanceDataReader.__version__}')

    from google.colab import userdata
    secret_status = {}
    for k in ['KRX_ID', 'KRX_PW', 'ECOS_API_KEY', 'GH_TOKEN']:
        try:
            v = userdata.get(k)
            if v:
                if k in ('KRX_ID', 'KRX_PW'):
                    os.environ[k] = v
                secret_status[k] = True
            else:
                secret_status[k] = False
        except Exception:
            secret_status[k] = False
    print('Secrets:', secret_status)

    !git config user.email 'msm@stanleyim.local'
    !git config user.name 'stanleyim'

    from glob import glob
    sv_files = sorted(glob('data/state/state_vector/year=*.parquet'))
    df_sv = pd.concat([pd.read_parquet(f) for f in sv_files], ignore_index=True)
    assert df_sv.shape == (2793837, 12)
    assert df_sv['code'].nunique() == 1603

    rg_files = sorted(glob('data/state/regime/year=*.parquet'))
    df_rg = pd.concat([pd.read_parquet(f) for f in rg_files], ignore_index=True)
    assert df_rg.shape == (2793837, 4)

    df_tm = pd.read_parquet('data/state/transition/transition_matrix.parquet')

    df_sv = df_sv.merge(df_rg[['date', 'code', 'regime']], on=['date', 'code'], how='left')
    assert df_sv.shape == (2793837, 13)

    print(f'state_vector + regime shape: {df_sv.shape}')
    print(f'regime 분포: {df_sv.regime.value_counts(dropna=False).to_dict()}')
    !git log --oneline -5
    print('Setup OK — STEP 4 진입 준비')

---

## 8. STEP 4 사전 설계 (Edge Field Calculation)

### 8-1. 목표
- INPUT: state_vector + regime (2.79M rows)
- TRANSFORM: E(S_t) = E[ r_{t+k} | S_t ] expected return surface mapping
- OUTPUT: data/state/edge_field.parquet

### 8-2. 결정 필요 (Q-E1 ~ Q-E5)

| Q | 항목 | 옵션 |
|---|---|---|
| Q-E1 | Forward horizon k | A. 1d / B. 5d / C. 20d / D. 다중 |
| Q-E2 | Return 정의 | A. log(close_t+k / close_t) / B. simple / C. CAR vs market |
| Q-E3 | Edge 단위 | A. regime별 4 cells / B. regime × z-quintile / C. continuous |
| Q-E4 | 추가 입력축 | A. regime만 / B. + z_v / C. + z_v + z_f + z_ell |
| Q-E5 | 통계량 | A. mean / B. mean+std / C. mean+std+hit ratio+percentile |

### 8-3. 사전 리스크
- forward shift lookahead — code별 그룹 내 shift(-k) 강제
- delisted 마지막 k일 NaN 자연
- regime NaN + forward NaN 동시 처리 정책 필요

### 8-4. STEP 4 셀 구조
- Setup: v8 §7-3 setup 셀
- Step A: forward return 계산 (Q-E1, Q-E2)
- Step B: edge field aggregation (Q-E3, Q-E4)
- Step C: 통계량 산출 (Q-E5)
- Step D: 검증 (lookahead 0, NaN, sample size)
- Step E: 저장 + commit + push

---

## 9. 핵심 원칙 재공지

1. §1 추측 금지
2. §6 3번 검토 3축
3. §7 옵션 → 형 결정 → 실행
4. 단일 셀 통합
5. GitHub = truth
6. LOCKED VALUES 변경 금지
7. MSM = choonsimi-premium 독립

---

## 10. 핵심 한 줄

STEP 3 완료. Transition matrix LOCKED. TREND가 가장 unstable (persistence 0.141, entropy 1.094) → STEP 4 edge field의 핵심 타겟. 다음 = Q-E1~Q-E5 결정 → Edge Field Calculation.

---

**작성자**: Claude (MSM 세션 #5)
**상태**: MSM 5단계 중 STEP 3 완료
**다음 작업**: Q-E1~Q-E5 결정 → Edge Field 설계 → 구현 → edge_field.parquet

끝.
