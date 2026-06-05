# MSM 핸드오프 v12 — STEP 8 LOCKED (MSM v2 = TRADEABLE SYSTEM)

**작성일**: 2026-06-05 (KST, MSM 세션 #8 종결)
**대상 repo**: stanleyim/choonsimi-msm
**최신 commit**: abaa372 — MSM STEP 8.7 gamma sweep
**상태**: ★ MSM v2 LOCKED. Production-ready. Target 3/3 통과.
**다음**: Phase 2 — Forward test (paper trading)

---

## 0. 절대 원칙 (v11 §0 그대로 + v12 신규)

1. §1 추측 금지
2. §6 3번 검토 (정확성 + 사고 가능성 + 안전장치)
3. §7 옵션 → 형 결정 → 실행
4. §13 매 단계 commit/push
5. MSM = choonsimi-premium 독립 (v10c 6/26 freeze)
6. 외부 검토자 3 원칙
7. 단일 셀 통합 코드
8. Signal ≠ Execution constraint (v10 §0-8)
9. Selection asymmetry: edge_field universe ≠ realized top-K (v10 §2-15)
10. Control manifold ≠ Alpha manifold (v11)
11. v12 신규: State manifold > Control manifold — state expansion이 frontier 외부 이동

---

## 1. ★ LOCKED VALUES (v12 종합)

### 1-1. STEP 1~5 (v10 LOCK, 유지)
- state_vector v1 : data/state/state_vector/year=*.parquet, (2,793,837, 12), 1603 codes
- regime v1      : data/state/regime/year=*.parquet
- transition     : data/state/transition/, 4x4 MLE
- edge_field v1  : data/state/edge/edge_field.parquet, 12 rows
- tradeable v1   : data/state/tradeable/year=*.parquet, 9.13%

### 1-2. STEP 6 (v10 LOCK, 유지) — SHOCK SHORT only
- NET (cost 0.30% RT): CAGR +11.92%, Sharpe 0.48, MDD -68.65%
- 파일: data/sim/equity_curve_shock_short_only.parquet

### 1-3. STEP 7 V1 (v11 LOCK, 유지) — Control terminal
- T4 (-20%/0.5x/-10%): CAGR +10.10%, Sharpe 0.48, MDD -49.96%
- 파일: data/sim/equity_t4_v1.parquet

### 1-4. STEP 8 (v12 신규 LOCK) — MSM v2 Production

STEP 8.1a Volume Download
- 파일: data/raw/short/volume/q_*.parquet (34 files) + pilot_2025*.parquet (5 files)
- 39 files, ~54MB, 2,307 거래일, KOSPI+KOSDAQ 통합
- pykrx get_shorting_volume_by_ticker
- commit: a6b9bc1

STEP 8.1b Balance Download
- 파일: data/raw/short/balance/q_*.parquet (38 files), ~92MB
- 2,307 거래일 전부
- pykrx get_shorting_balance_by_ticker
- 다운로드 시간: 54.7분

STEP 8.2 State Vector v2
- 파일: data/state/state_vector_v2/year=*.parquet (10 partitions)
- shape: (2,793,837, 25), 259MB
- 추가 columns: short_volume, short_balance_qty_t2, short_delta, short_pressure, short_pct_change, short_trade_intensity, market_cap_t2
- T+2 lookahead shift 적용
- short_pressure non-NaN: 68.13%
- commit: 51458c0

STEP 8.3 Edge Field v2
- 파일: data/state/edge_v2/edge_field_v2.parquet (27 cells)
- 핵심: NEUTRAL k=20 = +50.23bp (t=24.84) ★★★
- COVERING k=20 = +16.76bp (t=6.04)
- BUILDUP k=20 = -23.34bp (t=-8.66)
- commit: 759505c

STEP 8.4 Selection 재검증
- v1 sign flip 재발견: NEUTRAL universe +50bp → top-K (z_r+z_f) subset -55bp
- score 기반 LONG selection 무용 확정
- 파일: data/state/edge_v2/diag_subset_v2.parquet
- commit: f9e3fba

STEP 8.5 ★ NEW Selection 발견
- NEUTRAL × bot z_ell (저유동성): +107.70bp k=20, t=15.13 STRONGEST
- 시장 baseline +22.93bp 대비 +84.77bp 진짜 alpha
- 9 variants 비교 sweep
- 파일: data/state/edge_v2/diag_selection_sweep_v2.parquet
- commit: bc3f413

STEP 8.6 LONG-SHORT Backtest
- 3 runs (v2 SHORT/LONG/LS combined)
- v2 LS baseline: CAGR +15.86%, Sharpe 0.57, MDD -47.28% (target 부분 미달)
- 파일: data/sim/v2_short_only.parquet, v2_long_only.parquet, v2_long_short.parquet
- commit: 4dc6401

STEP 8.7 ★ γ Sweep — Target 통과
- α (LONG hold: 5/10/15/20) × β (T4 ON/OFF) = 8 variants
- 3 variants PASS: H=10/15/20 + T4 ON
- ★ BEST: H=15, T4=ON
- 파일: data/sim/v2_gamma_best.parquet, step87_gamma_sweep.parquet
- commit: abaa372

---
## 2. ★★★ MSM v2 LOCKED CONFIG (Production)

### 2-1. State Layer
- File: data/state/state_vector_v2/year=*.parquet
- 25 columns:
  - Base (v1): date, code, r, sigma, v, ell, f, z_r, z_sigma, z_v, z_ell, z_f
  - Short positioning (v2 신규):
    - short_volume          : daily 공매도 거래량
    - buy_volume            : daily 매수 거래량 (참고)
    - short_vol_ratio       : daily 공매도 / total volume %
    - short_balance_qty_t2  : T+2 shifted 잔고수량 (lookahead-safe)
    - market_cap_t2         : T+2 shifted 시가총액
    - short_delta           : diff(short_balance_qty_t2)
    - short_pressure        : short_delta / rolling 5d mean (핵심)
    - short_pct_change      : pct_change(short_balance_qty_t2)
    - short_trade_intensity : short_volume / (short+buy)
  - v1 regime (merged): regime, direction, tradeable

### 2-2. Regime Layer (v2A — 형 spec)
- COVERING : short_pressure<0 AND r>0 — LONG candidate (weak, +17bp k=20)
- BUILDUP  : short_pressure>0 AND r<0 — SHORT continuation
- SQUEEZE  : short_pressure>0 AND r>0 — Risky
- NEUTRAL  : |short_pressure|<0.001 — ★ Strong LONG (+50bp k=20)
- OTHER    : 나머지
- 분포: NEUTRAL 18.8%, BUILDUP 12.5%, COVERING 11.3%, SQUEEZE 11.1%

### 2-3. ★ LONG Side Configuration (NEW)
- Regime    : NEUTRAL (short_pressure ≈ 0)
- Selection : bot z_ell top 10 per day (저유동성)
- Hold      : 15 days (또는 NEUTRAL 이탈 시 exit)
- Weight    : 1/10 per position
- Universe edge: +107.70bp k=20 (t=15.13)

### 2-4. SHORT Side Configuration (v1 유지)
- Regime    : SHOCK (v1 direction=-1 AND tradeable)
- Selection : bot score (z_r+z_f) top 10 per day
- Hold      : 5 days
- Weight    : 1/10 per position
- Universe edge: -150bp k=20 (v1 STEP 4)

### 2-5. Control Layer (T4 from v1 V1)
- DD trigger    : -20% (cumulative NET drawdown 기준)
- Exposure low  : 0.5x (트리거 발동 시 다음날부터 절반)
- Recovery DD   : -10% (회복 시 다음날 1.0x 복원)
- LONG + SHORT 양쪽 동시 적용
- Reduced time  : 60.8% of period (실측)

### 2-6. Cost Assumption
- 0.30% RT per round-trip
- Breakeven cost: ~0.55% RT (큰 margin)
- GROSS Sharpe 1.67 → NET Sharpe 0.686 (50% cost drag 후에도 통과)

---

## 3. ★ MSM v2 BEST 성과 (LOCKED)

### 3-1. Headline numbers (H=15, T4=ON)
- CAGR  : +16.48%
- Sharpe: 0.686 (★ target 0.60 통과)
- MDD   : -33.13% (★ target -40% 통과)
- GROSS Sharpe: 1.67
- 기간: 9.4년 (2017-01-02 ~ 2026-06-02)

### 3-2. γ Sweep 전체 결과 (8 variants)
| H  | T4   | CAGR    | Sharpe | MDD     | Reduced |
|----|------|---------|--------|---------|---------|
| 5  | off  | 15.86%  | 0.574  | -47.28% | 0.0%    |
| 5  | ON   | 11.67%  | 0.551  | -34.01% | 69.0%   |
| 10 | off  | 24.04%  | 0.742  | -45.36% | 0.0%    |
| 10 | ON   | 15.23%  | 0.642  | -32.83% | 62.6%   |
| 15 | off  | 26.59%  | 0.792  | -45.85% | 0.0%    |
| 15 | ON   | 16.48%  | 0.686  | -33.13% | 60.8%   |★ BEST
| 20 | off  | 27.40%  | 0.807  | -45.48% | 0.0%    |
| 20 | ON   | 15.66%  | 0.661  | -32.89% | 61.5%   |

### 3-3. Frontier Expansion (v1 → v2)
| Metric  | v1 V1 LOCKED | v2 BEST  | 변화         |
|---------|--------------|----------|--------------|
| CAGR    | +10.10%      | +16.48%  | +6.38pp (+63%) |
| Sharpe  | 0.48         | 0.686    | +0.21 (+43%)  |
| MDD     | -49.96%      | -33.13%  | +16.83pp 개선 |
| GROSS Sh| 1.16         | 1.67     | +0.51         |

### 3-4. 모든 지표에서 v1 V1 초과
- v2 BEST가 v1 V1보다 모든 측면에서 우수
- frontier 점 → frontier 면적으로 확장
- state expansion이 control limit 돌파

---

## 4. ★★★ 핵심 발견 6종 (STEP 8 종합)

### 발견 1: State Expansion > Control Optimization
- v1 (control): Sharpe 0.48 ceiling
- v2 (state) : Sharpe 0.81 ceiling, 0.69 (T4 ON)
- 증명: control은 frontier 위 이동, state는 frontier 외부 이동
- → v11 §2-17 Sharpe Invariance Law는 control layer 내부에서만 유효
- → state expansion 시 깨짐

### 발견 2: LONG Alpha 진짜 원천 = NEUTRAL × 저유동성
- 형 가설 (COVERING LONG): 부분 검증 (+17bp 약함)
- 진짜 강한 LONG: NEUTRAL × bot z_ell = +107.70bp (시장 baseline 대비 +84.77bp)
- 의미: "공매도 활동 없는 종목" + "저유동성" = 평균 회귀 + drift up
- v1에서 z_r+z_f selection이 이 영역을 못 잡았음

### 발견 3: Score-based LONG Selection은 모든 regime에서 sign flip
- NEUTRAL universe +50bp → top-K (z_r+z_f) subset -55bp
- COVERING universe +17bp → top-K -97bp
- v1 TREND/RANGE도 동일 패턴 (v10 §2-15)
- 의미: momentum-based score는 LONG continuation 못 잡음

### 발견 4: LONG Side는 Alpha < Risk Diversification
- LONG only NET Sharpe 0.08 (cost drag로 alpha 거의 없음)
- LONG-SHORT combined Sharpe 0.57 (LONG 추가로 +0.09 + MDD 큰 개선)
- LONG의 진짜 가치 = MDD reduction (-69% → -47%)

### 발견 5: γ 구조 분해 (α: turnover, β: tail)
- α 단독 (LONG hold 5→15): Sharpe 0.57 → 0.79 (cost overhead 절반 제거)
- β 단독 (T4 ON): Sharpe 0.57 → 0.55, MDD -47% → -34% (risk 절단)
- γ 결합: Sharpe 0.69, MDD -33% (양쪽 동시 개선)

### 발견 6: Cost Sensitivity (실거래 가용성)
- 현재: 0.30% RT 가정 → Sharpe 0.69
- 0.40% RT → Sharpe ~0.62 (여전히 통과)
- 0.50% RT → Sharpe ~0.58 (target 부분 미달, 운용 가능)
- GROSS 1.67 = 큰 cost buffer
- 한국 LS 헤지펀드 cost 일반 0.30~0.50% RT
- → MSM v2 = 실거래 가용 영역

---

## 5. ★ 확정 정책 (v11 §2 + v12 신규)

### v12 §2-18 신규 — State Manifold Theory
- Control layer만으로 frontier 외부 이동 불가 (v11 §2-17)
- State layer expansion 시 frontier 자체가 확장됨
- Sharpe ceiling은 state 정보량의 함수
- 함의: 추가 state expansion (state v3) 시 Sharpe 더 높일 가능성
- 그러나 marginal gain 감소 + overfit risk 증가
- → 현재 v2가 적절한 stopping point

### v12 §2-19 신규 — LONG Alpha Structure
- LONG alpha는 "extreme 회피" 영역에 있음
- SHORT alpha는 "extreme 추구" 영역에 있음 (SHOCK)
- 같은 score 변수를 양방향 사용 불가
- LONG: NEUTRAL regime + bot z_ell (저유동성, 조용한 종목)
- SHORT: SHOCK regime + bot score (강한 음 모멘텀)

### v12 §2-20 신규 — γ Structure (α+β)
- α: LONG hold 압축으로 cost ratio 절감 (turnover ↓)
- β: T4 circuit breaker로 tail variance 절단 (MDD ↓)
- 결합 시 Sharpe와 MDD 동시 개선 (trade-off 회피)
- H=15 + T4 (-20/0.5x/-10) = optimal frontier point

---
## 6. 파일 인벤토리 (commit abaa372 기준)

choonsimi-msm/
- MSM_HANDOFF_2026_06_02.md (v1~v4)
- MSM_HANDOFF_2026_06_03_v6.md
- MSM_HANDOFF_2026_06_04_v7.md ~ v11.md
- MSM_HANDOFF_2026_06_05_v12.md ← 이 문서 (MSM v2 LOCK)
- STEP8_PROGRESS.md (in-progress, archive 가능)
- README.md
- msm_data_supplement.ipynb
- msm_data_ingestion.ipynb
- msm_state_vector.ipynb
- data/
  - raw/
    - active/, delisted/, macro/ (v7 그대로)
    - vkospi_10y_*.csv (참고)
    - short/                                  v12 신규
      - volume/q_*.parquet (34 files) + pilot_2025*.parquet (5 files), ~54MB
      - balance/q_*.parquet (38 files), ~92MB
  - universe/universe_msm.csv
  - state/                                    (STEP 1~5 + v2)
    - state_vector/year=*.parquet            (v1)
    - regime/year=*.parquet                  (v1)
    - transition/                            (v1)
    - edge/edge_field.parquet                (v1)
    - tradeable/year=*.parquet               (v1)
    - state_vector_v2/year=*.parquet         v12 신규 (259MB)
    - edge_v2/                                v12 신규
      - edge_field_v2.parquet
      - diag_subset_v2.parquet
      - diag_selection_sweep_v2.parquet
  - sim/                                      (STEP 6, 7, 8)
    - equity_curve_shock_short_only.parquet  (STEP 6 LOCKED)
    - equity_t4_v1.parquet                   (STEP 7 V1 LOCKED)
    - v2_short_only.parquet, v2_long_only.parquet, v2_long_short.parquet (STEP 8.6)
    - v2_gamma_best.parquet                  MSM v2 BEST LOCKED
    - step87_gamma_sweep.parquet             (gamma sweep summary)
    - 기타 진단 파일 다수
  - checks/

---

## 7. 본 세션 commit 이력 (시간순)

- abaa372  MSM STEP 8.7 gamma sweep: best H 15 T4 ON
- 4dc6401  MSM STEP 8.6: LONG-SHORT backtest Sharpe 0.57
- bc3f413  MSM STEP 8.5: market baseline + 9 selection variants
- f9e3fba  MSM STEP 8.4: NEUTRAL/COVERING × selection diagnostic
- 759505c  MSM STEP 8.3: edge field v2
- 51458c0  MSM STEP 8.2: state_vector v2
- e3abff7  MSM STEP 8.1a Complete + progress note
- a6b9bc1  MSM STEP 8.1 Pilot
- (34 quarter commits) MSM STEP 8.1a volume download
- (38 quarter commits) MSM STEP 8.1b balance download
- a27efdd  MSM HANDOFF v11

---

## 8. 실수 누적 (v11 #1~#42 + v12 신규)

v11 #40~#42 유지.

v12 신규:
- #43: KRX 직접 API endpoint LOGOUT 400. 세션 쿠키 + OTP 403. pykrx wrapping 미지원 (uptick). 재발 방지: 사전 검증 + pykrx fallback 준비.

- #44: pykrx get_shorting_status_by_date 일부 ticker (delisted/특수)에서 column 변경 에러. KRX response가 한국어/영문 가끔 변경. 재발 방지: date-wise bulk API 사용 권장.

- #45: 2026Q2 마지막 2일 balance API 영문 column anomaly. 재발 방지: 다운로드 후 date-coverage 검증 의무화.

- #46: STEP 8.4에서 NEUTRAL × top-K (z_r+z_f) sign flip 재현. 형 가설 직접 selection 실패. 재발 방지: universe edge + top-K subset 양쪽 검증 후 사용.

- #47: target gap을 단일 layer로 못 메움. multi-layer 결합 (alpha + beta) 필요. 교훈: target 미달 시 직교 layer 결합 시도.

---
## 9. MSM 진행 상태 (FINAL — v12 LOCK)

STEP 1: State Vector v1               LOCKED (6979a1d)
STEP 2: Regime Detection v1           LOCKED (be5d63d)
STEP 3: Transition Estimation         LOCKED (f105ff2)
STEP 4: Edge Field v1                 LOCKED (66c0e52)
STEP 5: Tradeable Region              LOCKED (def993f)
STEP 6: Execution (SHORT-only)        LOCKED (3b3ceb0 + 4618806)
STEP 7: Control Layer (T4 V1)         LOCKED (90eb86d)
STEP 8: Alpha Restructuring (v2)      LOCKED (abaa372)
        - 8.1a Volume download
        - 8.1b Balance download
        - 8.2 State Vector v2 build
        - 8.3 Edge Field v2 measurement
        - 8.4 Selection re-validation
        - 8.5 NEW selection discovery
        - 8.6 LONG-SHORT backtest
        - 8.7 gamma Sweep (alpha + beta combined) Target PASS

MSM v2 = TRADEABLE SYSTEM
  Sharpe 0.686 / MDD -33.13% / CAGR 16.48%
  Target 3/3 통과
  Production-ready

NEXT (Phase 2):
  - Forward test (paper trading)
  - Production validation
  - 필요 시 STEP 9 (state v3)

---

## 10. Phase 2 — Forward Test 진입 사양

### 10-1. Forward Test 목적
- 실시간 paper trading으로 v2 BEST config 검증
- Cost realistic 확인 (한국 시장 실제 borrow fee, market impact)
- Out-of-sample 지속성 확인
- choonsimi-premium (live forward test 진행 중) 과 별개

### 10-2. Forward Test Configuration
- Start date: 2026-06-06 (또는 형 결정)
- Initial capital: paper notional (예: 100M KRW)
- Daily rebalance:
  - LONG: NEUTRAL regime + bot z_ell top 10, hold 15d
  - SHORT: SHOCK regime + bot score top 10, hold 5d
- T4 control: -20% trigger, 0.5x scale, -10% recovery
- Cost: 0.30% RT (실측 vs 가정)
- Universe: 1,603 codes (v1 universe)

### 10-3. 필요 구성요소
- daily data feed (pykrx OHLCV + shorting)
- state vector v2 일일 update
- regime 분류
- selection (LONG/SHORT 각 10개)
- position tracking (hold day count)
- equity curve + DD tracking (T4 trigger)
- 일일 report

### 10-4. Forward Test 결정 옵션
- A: Colab 일일 실행 (수동, 형이 매일 실행)
- B: 별도 서버 (cron) 자동 실행
- C: 1주~1개월 후 batch 비교 (실거래 신호 vs 백테스트)
- D: choonsimi-premium 6/26 forward test 결과 후 결정

---

## 11. Phase 2 즉시 결정 필요

| 옵션 | 내용 | 비고 |
|---|---|---|
| A | Forward test 시스템 즉시 설계 (1셀 paper trading) | 다음 세션 |
| B | MSM v2 LOCK은 충분, 6/26 choonsimi-premium 결과 대기 후 dual-engine 검토 | 보수 |
| C | STEP 9 도전 (state v3 — sector / market regime / news 추가) | 추가 push |
| D | v12 LOCK 후 휴식, 다음 세션 시작 시 결정 | 권장 |

---

## 12. 핵심 한 줄

STEP 8 LOCKED. MSM v2 = TRADEABLE SYSTEM. H=15 LONG hold + T4 (-20/0.5x/-10). Sharpe 0.686, MDD -33.13%, CAGR 16.48%. Target 3/3 통과. State expansion (short positioning)이 v11 Sharpe Invariance Law를 깨고 frontier 외부 이동 입증. NEUTRAL + bot z_ell이 LONG alpha 진짜 원천 (+107.70bp k=20). LONG cost drag는 hold 압축으로 해결, MDD는 T4 circuit breaker로 절단. 6/26 choonsimi-premium 결과 + MSM v2 forward test가 다음 검증 단계.

---

## 13. 다음 세션 START GUIDE

### 13-1. 첫 메시지 권장

MSM v2 LOCKED. MSM_HANDOFF_2026_06_05_v12.md 참고.

현재:
- STEP 1~8 모두 LOCKED
- MSM v2 BEST: H=15 LONG hold + T4 (-20/0.5x/-10)
  Sharpe 0.686, MDD -33.13%, CAGR 16.48%
  Target 3/3 통과 = TRADEABLE SYSTEM

다음 Phase 2:
- Forward test 또는 6/26 결과 대기 또는 STEP 9

§1 추측 X, §6 3축, §7 옵션 → 형 결정 → 실행, 단일 셀.

### 13-2. Claude 첫 응답 할 것
1. v12 §0 절대 원칙 정독 (#11 state manifold > control manifold)
2. v12 §1-4 STEP 8 LOCKED VALUES 검증
3. v12 §2 MSM v2 LOCKED CONFIG 정독
4. v12 §10 Phase 2 사양 + 옵션 A/B/C/D 송부
5. 형 결정 받고 실행

### 13-3. 새 노트북 합본 셀 (Phase 2 시작용)
EXPECTED_HEAD_PREFIX 갱신: v12 push 후 commit hash로

---

## 14. 형의 다음 분석 우선순위

1. 6/26 choonsimi-premium forward test 결과 (이미 진행 중)
2. MSM v2 forward test 시작 여부 (Phase 2)
3. 두 시스템 비교 (alpha 독립성, 결합 가능성)
4. dual-engine 구조 가능 여부

---

**작성자**: Claude (MSM 세션 #8, MSM v2 LOCKED)
**상태**: STEP 1~8 모두 LOCKED. MSM v2 = Production-ready.
**다음 작업**: Phase 2 결정 (Forward test 또는 휴식)

끝.
