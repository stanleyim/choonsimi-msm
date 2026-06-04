# MSM STEP 8 Progress Note — Short Data Ingestion (in progress)

**작성일**: 2026-06-05 (KST, MSM 세션 #8)
**상태**: STEP 8.1a Volume Download 완료
**다음**: STEP 8.1b Balance Download → 8.2 Merge → 8.3~8.6

---

## 1. STEP 8.1a — Short Volume Download (완료)

### Source
- pykrx get_shorting_volume_by_ticker(date, market)
- KOSPI + KOSDAQ 통합

### Coverage
- 기간 : 2017-01-02 ~ 2026-06-02 (df_sv 전체 거래일)
- 거래일: 2,307일 = 2025 pilot (242일) + 2017-2024+2026 (2,065일)
- 시장 : KOSPI + KOSDAQ
- universe match: 1,369 / 1,603 active (delisted 234는 historical만)

### Schema
- columns: 티커, 공매도, 매수, 비중, date
- 공매도   = short volume (주)
- 매수     = ordinary buy volume (주, 참고)
- 비중     = short % of total (already calculated)
- non-zero ratio 공매도: 83.59%

### Storage
- data/raw/short/volume/q_*.parquet (34 files, 2017-2024 + 2026)
- data/raw/short/volume/pilot_2025*.parquet (5 files, 2025 + consolidated)
- Total size: ~54MB

### Execution
- 시간: 52.9분 (분기별 1.5분 평균)
- Push: 분기별 즉시 (34회 + 4회 pilot = 38회 push)
- KRX 세션 만료 1회 발생 (2022Q1) → pykrx 자동 재로그인 → 무중단 진행
- Failed dates: 0

### Commits (download 동안)
- a6b9bc1: pilot 2025
- 이후 분기별 34 commits

---

## 2. STEP 8.1b — Short Balance Download (대기)

### 목적
- 형 spec §2-3: short_balance_qty, short_balance_value
- short_pressure 계산 핵심 변수 (= short_delta / rolling 잔고)
- COVERING regime 식별 (LONG edge 후보)

### API
- pykrx get_shorting_balance_by_ticker(date, market)
- 검증 완료 (앞 pilot에서 작동 확인)
- columns = 공매도잔고, 상장주식수, 공매도금액, 시가총액, 비중
- KOSPI + KOSDAQ 통합

### 예상
- 시간: ~55분 (volume과 유사, 분기별 push)
- 크기: ~50~60MB
- Failure mode: KRX 세션 만료 시 자동 재로그인 검증됨

### Storage 예정
- data/raw/short/balance/q_*.parquet (34 files)
- data/raw/short/balance/pilot_2025*.parquet (2025 별도 다운로드 필요)

---

## 3. STEP 8.2 — Merge & Feature Engineering (대기)

### 입력
- df_sv (state_vector v1, 2,793,837 × 12)
- short_volume aggregated (39 files → 1 consolidated DataFrame)
- short_balance aggregated

### 작업
1. consolidate volume + balance → single DataFrame per date×ticker
2. universe filter (1,603 codes)
3. Merge with df_sv on (date, ticker)
4. Lookahead 처리: short_balance_qty.shift(2~3) — KRX 잔고 T+2/T+3 공시 지연
5. Derived features 연산:
   - short_delta = short_balance_qty.diff()
   - short_pressure = short_delta / short_balance_qty.rolling(5).mean()
   - short_pct_change = short_balance_qty.pct_change()
   - short_ratio = short_volume / total_volume

### 산출
- data/state/state_vector_v2/year=*.parquet
- 추가 columns: short_volume, short_balance_qty, short_pressure, short_pct_change

---
## 4. STEP 8.3 — Regime v2 Reclassification (대기)

### 형 spec §7 (그대로)
- BUILD-UP   : short_pressure > 0 AND ret < 0
- COVERING   : short_pressure < 0 AND ret > 0  ★ LONG EDGE 후보
- SQUEEZE    : short_pressure > 0 AND ret > 0
- NEUTRAL    : |short_pressure| <= threshold

### 결정 필요
- threshold for NEUTRAL (e.g., abs(z(short_pressure)) <= 0.5?)
- 기존 4 regime (TREND/RANGE/SHOCK/TRANSITION) vs 신규 4 regime 통합 방식
- 옵션:
  - A. 신규 4 regime 단독 사용 (기존 regime 폐기)
  - B. 8-regime cube (4 × 2 = 기존 × short_pressure sign)
  - C. 기존 + short_pressure 별도 feature로

---

## 5. STEP 8.4 — Edge Field v2 (대기)

### 가설 검증
- HYP1: E[r_{t+1..t+20} | regime=COVERING] > 0, |t|>4
- HYP2: COVERING universe edge ≈ realized top-K edge (no sign flip, 1.0x ratio)

### STEP 4 + G-1 방법론 재적용
- 12 regime × horizon cells 측정
- universe-wide vs realized top-K subset 비교 (selection asymmetry 재검증)

---

## 6. STEP 8.5 — Edge Field 비교 (v1 vs v2)

### Critical comparison

v1 (state v1):
- LONG side: universe +60bp k=20 → realized -7~-12bp (sign flip)
- SHORT side: universe -150bp k=20 → realized -174bp (amplified 1.16x)

v2 (state v2, short_pressure 추가):
- LONG (COVERING): universe ?bp → realized ?bp
- 기대: sign flip 사라지고 universe ≈ realized
- 검증: ratio 0.8~1.2x 영역

---

## 7. STEP 8.6 — LONG side salvage backtest (대기)

### 옵션 (STEP 8.4 결과에 따라)
- P1: COVERING LONG + SHOCK SHORT 결합 Long-Short
- P2: COVERING LONG only
- P3: STEP 7 V1 baseline 위에 COVERING entry 추가

### Target (재정의)
- Sharpe > 0.6 (V1 0.48 대비 +0.12)
- MDD < -40% (V1 -49.96 대비 +10pp)
- CAGR >= 10% (V1 수준)

---

## 8. 핵심 발견 (Session #8 중)

- KRX MDCSTAT API 직접 = 차단됨 (LOGOUT 400)
- pykrx fallback = volume + balance 4 cols 가능, uptick 제외
- universe 1,603 중 active 1,369 만 KRX 응답 — 234 delisted 정상 처리
- 분기별 매번 push = §7 #36 학습 적용, 손실 최대 15분으로 축소
- Total download time 추정 정확 (예상 67분 → 실제 53분)
- KRX 세션 만료시 pykrx 자동 재로그인 작동 확인 (2022Q1 사례)

---

## 9. 진행 일정 (예상)

- STEP 8.1a Volume       : 완료 (53분)
- STEP 8.1b Balance      : 다음 (~55분)
- STEP 8.2 Merge         : ~10분
- STEP 8.3 Regime v2     : ~10분 (옵션 결정 + 실행)
- STEP 8.4 Edge v2       : ~20분 (G-1 방법론)
- STEP 8.5 비교/검증     : ~10분
- STEP 8.6 LONG salvage  : ~30분 (P1 sweep)
- v12 핸드오프           : ~30분
- 합계                   : 약 3시간

---

## 10. 다음 작업 즉시 명령

STEP 8.1b Balance Download:
- pykrx get_shorting_balance_by_ticker 사용
- 동일 분기별 푸시 패턴
- 2017-2024 + 2025 + 2026 (2025 미수집)
- 단일 셀 ~55분

→ 형 GO 시 즉시 실행.
