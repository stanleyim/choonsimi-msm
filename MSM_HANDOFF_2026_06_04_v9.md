# MSM 핸드오프 v9 — STEP 1~4 완료 (Edge Field LOCKED) → STEP 5 진입 대기

**작성일**: 2026-06-04 (KST)
**대상 repo**: stanleyim/choonsimi-msm
**최신 commit**: 66c0e52 — MSM STEP 4 edge field
**상태**: ★ MSM v1 STEP 4 (Edge Field Calculation) 완료 — LOCKED
**다음**: STEP 5 (Tradeable Region Extraction) — 설계 LOCKED, 실행만 남음
**환경**: 태블릿 (Colab), 단일 셀 통합 유지
**다음 세션 시점**: 4시간 후 (메모리 85% 도달, 휴식)

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

## 1. ★ LOCKED VALUES (v9 누적 immutable)

### 1-1. STEP 1 (v7에서 LOCK)
- state_vector.parquet (PT_year, 10 partitions)
- shape: (2,793,837, 12)
- universe: 1,603 codes
- period: 2017-01-02 ~ 2026-06-02
- columns: date, code, r, sigma, v, ell, f, z_r, z_sigma, z_v, z_ell, z_f
- commit: 6979a1d

### 1-2. STEP 2 (v8에서 LOCK)
- regime.parquet (PT_year, 10 partitions)
- shape: (2,793,837, 4)
- 분포: TRANSITION 56.00% / RANGE 25.22% / SHOCK 12.70% / TREND 5.51% / NaN 0.57%
- commit: be5d63d

### 1-3. STEP 3 (v8에서 LOCK)
- transition_matrix.parquet (4x4 MLE)
- transition_count.parquet, transition_yearly.parquet
- Diagonal: SHOCK 0.7674 / TREND 0.1410 / RANGE 0.5195 / TRANSITION 0.7211
- Entropy: SHOCK 0.6125 / TREND 1.0942 / RANGE 0.9560 / TRANSITION 0.8326
- commit: f105ff2

### 1-4. STEP 4 (v9 신규 LOCK)
- edge_field.parquet (12 rows = 4 regime × 3 horizon)
- columns: regime, horizon_k, n_obs, mean, std, t_stat, hit_ratio, p10, p25, p50, p75, p90
- size: 7.6 KB
- commit: 66c0e52

Edge field — mean (bp = 1e-4):

|            | k=1    | k=5    | k=20   |
|------------|--------|--------|--------|
| SHOCK      | -18.36 | -75.19 | -150.01|
| TREND      |   3.58 |  12.20 |   60.11|
| RANGE      |   2.16 |  13.70 |   60.82|
| TRANSITION |   1.58 |   8.33 |   44.99|

Edge field — t-stat:

|            | k=1    | k=5    | k=20   |
|------------|--------|--------|--------|
| SHOCK      | -15.37 | -28.00 | -35.35 |
| TREND      |   4.42 |   6.79 |  17.00 |
| RANGE      |   8.36 |  21.72 |  45.06 |
| TRANSITION |   6.06 |  13.52 |  36.92 |

Hit ratio:

|            | k=1    | k=5    | k=20   |
|------------|--------|--------|--------|
| SHOCK      | 0.4460 | 0.4430 | 0.4303 |
| TREND      | 0.4570 | 0.4781 | 0.4846 |
| RANGE      | 0.4487 | 0.4870 | 0.4963 |
| TRANSITION | 0.4547 | 0.4778 | 0.4835 |

Sample size min: 152,233 (TREND k=20)
Additivity max_diff: 0.00e+00 (log additive 완전)
마지막행 NaN: 모든 k에서 1.0 (lookahead 0)

---

## 2. ★ STEP 4 5대 핵심 발견 (해석 LOCKED)

### 발견 1: SHOCK 회복 가설 기각
- 사전 가설: SHOCK k=1 음수 → k=5 회복
- 실제: -18 → -75 → -150 bp 지속 악화 (monotonic 하락)
- 의미: SHOCK = 단발 이벤트 X, 지속 하락 클러스터
- transition matrix persistence 0.767과 정합

### 발견 2: TREND 지속성 (반전된 직관)
- transition matrix: TREND persistence 0.141 (단명)
- forward return: k=20까지 monotonic 증가 (+3.6 → +60 bp)
- 해석: TREND 자체 단명해도 TREND를 만든 momentum 잔향 20일 지속

### 발견 3: RANGE의 의외성 (★)
- 사전 가설: mean ~= 0, hit_ratio ~= 0.5
- 실제: mean 양수 + t=45 (k=20) — 가장 강한 양의 edge
- 해석: p50=0이지만 right-skewed distribution
- 드물게 큰 양의 일자가 평균을 끌어올림

### 발견 4: TRANSITION = market noise
- mean 작음 (+1.6 ~ +45 bp), 56% 비중
- 시장 평균 = baseline

### 발견 5: SHOCK / 양수 regime asymmetry
- SHOCK k=20: -150 bp vs 최대 양수 +60 bp
- |negative| / |positive| ~= 2.5x
- → SHOCK short이 long보다 절대값 큰 edge

---

## 3. ★ STEP 5 LOCKED 설계 (실행 대기)

### 3-1. 5개 결정 (Q-X1 ~ Q-X5)

| Q | 결정 | 옵션 |
|---|---|---|
| Q-X1 | B | Entry timing: t+1 (lookahead 회피, STEP 4 정의와 정합) |
| Q-X2 | A | Signal strength: binary {-1, 0, +1} (sizing 분리) |
| Q-X3 | A | Liquidity filter: z_ell >= P50 (daily cross-section median) |
| Q-X4 | B | Flow filter: direction과 z_f 동방향 일치 (long → z_f >= 0, short → z_f <= 0) |
| Q-X5 | A | No sizing in STEP 5 (signal binary만, sizing은 별도 layer) |

### 3-2. SHOCK 처리: A (SHORT = -1)

근거:
- SHOCK k=20: -150 bp, t=-35 (가장 강한 single signal)
- 제외 시 전체 alpha의 절반 손실 (절대값 기준)
- MSM = signal engine, execution constraint는 별도 layer
- Signal ≠ Execution constraint 원칙

### 3-3. Direction LOCKED

    SHOCK      → -1 (SHORT)
    TREND      → +1 (LONG)
    RANGE      → +1 (LONG)
    TRANSITION →  0 (NEUTRAL)

### 3-4. STEP 5 산출물 사전 설계

data/state/tradeable/year=*.parquet (PT_year, 10 partitions)
- shape: (2,793,837, ~7)
- columns:
  - date, code
  - regime (참고용)
  - direction: -1 / 0 / +1 / NaN
  - liquidity_pass: bool (z_ell >= daily P50)
  - flow_pass: bool (direction × z_f >= 0, NEUTRAL은 True)
  - tradeable: bool (direction != 0 AND liquidity_pass AND flow_pass)

### 3-5. 강제 체크 (STEP 5 실행 시 의무 포함)

1. Signal balance:
   - long_ratio = (direction == +1).mean()
   - short_ratio = (direction == -1).mean()
   - neutral_ratio = (direction == 0).mean()
   - 기대: long 25-35%, short 10-15%, rest neutral
2. Tradeable ratio after filters
3. 연도별 tradeable density 안정성
4. 100MB 가드
5. Round-trip

---

## 4. ★ 확정 정책 (v7 §2 + v8 §2-10/11 + v9 §3 신규)

### v7 §2-1 ~ §2-9 (변경 없음)
### v8 §2-10 (Regime 정의) — 변경 없음
### v8 §2-11 (Transition 추정) — 변경 없음

### v9 §2-12 신규 — Edge Field 계산 (STEP 4)
- Forward return: r_fwd_k = sum_{i=1..k} r.shift(-i) [code별 그룹]
- log additive: r_fwd_k = log(close_adj_{t+k} / close_adj_t) 수학적 동일
- Horizons: k ∈ {1, 5, 20}
- 추정: regime별 mean/std/t_stat/hit_ratio/percentile (P10/P25/P50/P75/P90)
- NaN: dropna (forward shift는 자연히 마지막 k row NaN)
- 구현: groupby.shift 벡터화 (transform(lambda) 금지, #35 참조)

### v9 §2-13 신규 — Tradeable Region (STEP 5 예정)
- Direction: SHOCK -1, TREND +1, RANGE +1, TRANSITION 0
- Entry: t+1 (lookahead 회피)
- Liquidity filter: z_ell >= daily P50 cross-section
- Flow filter: direction × z_f >= 0 (NEUTRAL은 True 처리)
- Sizing: STEP 5에서 미포함 (signal binary)

---

## 5. 파일 인벤토리 (commit 66c0e52 기준)

choonsimi-msm/
- MSM_HANDOFF_2026_06_02.md (v1~v4)
- MSM_HANDOFF_2026_06_03_v6.md
- MSM_HANDOFF_2026_06_04_v7.md
- MSM_HANDOFF_2026_06_04_v8.md
- MSM_HANDOFF_2026_06_04_v9.md ← 이 문서
- README.md
- msm_data_supplement.ipynb
- msm_data_ingestion.ipynb
- msm_state_vector.ipynb
- data/
  - raw/ (v7 그대로)
  - universe/universe_msm.csv
  - state/
    - state_vector/year=*.parquet   (STEP 1)
    - regime/year=*.parquet         (STEP 2)
    - transition/                    (STEP 3)
      - transition_matrix.parquet
      - transition_count.parquet
      - transition_yearly.parquet
    - edge/                          (STEP 4, v9 신규)
      - edge_field.parquet
    - tradeable/                     (STEP 5 예정)
  - checks/

---

## 6. 본 세션 (#5) 주요 commit (누적)

- 66c0e52  MSM STEP 4: edge field (regime x horizon {1,5,20}, log-return additive, full stats)
- 92a2b67  MSM HANDOFF v8: STEP 1~3 완료 (state_vector + regime + transition LOCKED)
- f105ff2  MSM STEP 3: transition matrix (market-wide, 1d, MLE, NaN drop, 4x4 + yearly sanity)
- be5d63d  MSM STEP 2: regime labeling (rule-based, z_r/z_sigma percentile, priority SHOCK>TREND>RANGE>TRANSITION)
- 3756e6d  MSM HANDOFF v7: STEP 1 완료 — LOCKED baseline
- 6979a1d  MSM STEP 1: state_vector year partitions

---

## 7. §8 실수 누적 (v8 #1~#34 + v9 신규)

v8 #29~#34 유지.

v9 신규:
- #35. groupby.transform(lambda: rolling.sum.shift) 사용 시 1000+ groups에서 Python callback 호출이 GIL bound로 사실상 무한 대기. 본 세션 STEP 4 첫 시도에서 발생. 재발 방지: 1000+ groups 대규모 forward shift는 groupby.shift(-i) 누적 합 또는 named function/numpy ufunc 사용. transform(lambda)는 소규모 group에만.
- #36. 셀 누적 충돌 — 동일 노트북에서 셀 다수 누적 시 환경 꼬임 발생. 형 지적: "셀이 많으면 어제처럼 엉키는 경우 발생". 재발 방지: 장시간 작업 후 새 노트북에서 합본 셀 1개로 실행. 멈춘 셀은 강제 종료보다 새 노트북이 더 빠르고 안전.

---

## 8. ★ MSM v1 진행 상태

- STEP 1: State Vector Construction   ✅ LOCKED (6979a1d)
- STEP 2: Regime Detection            ✅ LOCKED (be5d63d)
- STEP 3: Transition Estimation       ✅ LOCKED (f105ff2)
- STEP 4: Edge Field Calculation      ✅ LOCKED (66c0e52)
- STEP 5: Tradeable Region Extraction ⏸ 설계 LOCKED, 실행만 남음

---

## 9. 다음 세션 START GUIDE (★)

### 9-1. 첫 메시지 권장

    MSM STEP 5 (Tradeable Region Extraction) 시작.
    MSM_HANDOFF_2026_06_04_v9.md 참고.

    환경: 태블릿 (새 노트북 권장)
    현재: STEP 1~4 LOCKED
       - state_vector: 2.79M × 12, universe 1603
       - regime: 4 categories + NaN
       - transition: 4×4 MLE
       - edge_field: 12 rows (4 regime × 3 horizon)
    다음: STEP 5 Tradeable Region — 설계 LOCKED, 실행만

    §1 추측 X, §6 3번 검토 3축, §7 옵션→형 결정→실행, 단일 셀.
    v9 §9-3 합본 셀 사용. 새 노트북에서 1셀 실행.

### 9-2. Claude 첫 응답 할 것
1. v9 §0 절대 원칙 정독
2. v9 §1 LOCKED VALUES 검증 (state_vector + regime + transition + edge 4종)
3. v9 §3 STEP 5 LOCKED 설계 정독 (Q-X1~X5, SHOCK A, liquidity P50)
4. v9 §9-3 합본 셀 송부 (3축 사전 검토 포함)
5. 형 GO 받고 실행

### 9-3. ★ 새 노트북 합본 셀 (다음 세션 복붙용)

    import os, subprocess, shutil, time
    from pathlib import Path

    t0 = time.time()
    REPO = '/content/choonsimi-msm'
    EXPECTED_HEAD_PREFIX = '92a2b67'  # v9 push 후엔 v9 commit hash로 갱신 필요

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

    # [4] git config
    subprocess.run(['git','config','user.email','msm@stanleyim.local'], check=True, cwd=REPO)
    subprocess.run(['git','config','user.name','stanleyim'], check=True, cwd=REPO)

    # [5] STEP 1~4 LOCKED load
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

    df_sv = df_sv.merge(df_rg[['date','code','regime']], on=['date','code'], how='left')
    assert df_sv.shape == (2793837, 13)
    print(f'[5] load OK shape={df_sv.shape}, mem {psutil.virtual_memory().percent:.1f}%')

    print(f'준비 완료 — {time.time()-t0:.1f}s. STEP 5 실행 셀 대기.')

### 9-4. STEP 5 실행 셀 사전 구조

STEP 5 단일 셀은 위 setup 합본 + 아래 추가:

    DIRECTION_MAP = {'SHOCK': -1, 'TREND': +1, 'RANGE': +1, 'TRANSITION': 0}

    # entry timing B: t+1 (signal at t, executed at t+1)
    # → STEP 5 산출은 t에 기록된 signal. 실제 entry는 t+1.
    # → 따라서 STEP 5 자체는 t에 direction 기록하면 됨 (STEP 4 정의가 이미 t+1 기준 forward이므로)

    df_sv['direction'] = df_sv['regime'].map(DIRECTION_MAP).astype('Int8')

    # liquidity filter: z_ell >= daily P50
    p50_zell = df_sv.groupby('date')['z_ell'].transform(lambda x: x.quantile(0.5))
    df_sv['liquidity_pass'] = df_sv['z_ell'] >= p50_zell

    # flow filter: direction × z_f >= 0 (NEUTRAL은 True)
    # NaN z_f는 False (conservative)
    df_sv['flow_pass'] = (
        (df_sv['direction'] == 0) |
        ((df_sv['direction'] * df_sv['z_f']) >= 0)
    ).fillna(False)

    # tradeable
    df_sv['tradeable'] = (
        (df_sv['direction'] != 0) &
        df_sv['liquidity_pass'] &
        df_sv['flow_pass'] &
        df_sv['regime'].notna()
    )

    # 강제 체크
    # 1. Signal balance
    # 2. Tradeable ratio
    # 3. 연도별 stability
    # 4. 100MB 가드 (PT_year 저장)
    # 5. Round-trip

→ Q-X3 lambda 사용 주의: 1603 group이 아니라 ~2300 group (date) → 무거움. 대안: rank() 또는 transform('quantile')의 효율적 패턴 사전 검토 필요.

---

## 10. 핵심 원칙 재공지

1. §1 추측 금지
2. §6 3번 검토 3축
3. §7 옵션 → 형 결정 → 실행
4. 단일 셀 통합 (새 노트북 우선)
5. GitHub = truth
6. LOCKED VALUES 변경 금지
7. MSM = choonsimi-premium 독립
8. Signal ≠ Execution constraint (STEP 5 SHOCK SHORT 결정 근거)

---

## 11. 핵심 한 줄

STEP 4 완료. Edge field 12/12 cell 모두 |t|>4 통계적 유의. SHOCK -150bp / TREND +60bp / RANGE +61bp / TRANSITION +45bp (k=20). 모든 monotonicity 100%. STEP 5 설계 LOCKED (Q-X1~X5 + SHOCK SHORT + liquidity P50). 다음 세션 = 새 노트북 합본 셀 1개로 STEP 5 실행.

---

## 12. 형의 다음 세션 분석 우선순위 (인용)

> "STEP 5 결과 나오면 바로:
>  → signal density → 실제 포트폴리오 구성 가능성 → turnover 구조
>  까지 이어서 검증한다."

→ STEP 5 산출 후 분석 3축:
1. Signal density (long/short/neutral 비율 + 일별 신호 종목 수)
2. Portfolio feasibility (P50 liquidity 통과 후 실거래 가능 종목 수)
3. Turnover 구조 (regime 전환 빈도 → 실제 거래 빈도)

---

**작성자**: Claude (MSM 세션 #5)
**상태**: MSM 5단계 중 STEP 4 완료, STEP 5 설계 LOCKED
**다음 작업**: 새 노트북 → 합본 셀 → STEP 5 실행 → signal density 분석

끝.
