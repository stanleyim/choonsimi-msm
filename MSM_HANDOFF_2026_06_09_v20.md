# MSM 핸드오프 v20 — STATE freeze COMPLETE (9.4y axis_raw + 3 flags)

**작성일**: 2026-06-09 (KST, MSM 세션 #15 종결)
**대상 repo**: stanleyim/choonsimi-msm
**최신 commit**: cfa4aa6 — MSM v20 fix: M16_expiry_flag day range 6→5 (60/60 outlier cover)
**상태**: ★ STATE VECTOR v20 LOCKED. REGIME 분류 진입 가능.
**다음 작업**: REGIME 분류 (v4 STEP 2)

---

## 0. 절대 원칙 (v19 §0 동일)

1. §1 추측 금지
2. §6 3번 검토 (정확성 + 사고 가능성 + 안전장치)
3. §7 옵션 → 형 결정 → 실행
4. §13 매 단계 commit/push
5. MSM = choonsimi-premium 독립
6. 단일 셀 통합 코드
7. Long-running 작업 batch + auto-push 의무
8. forward test 발견 진실 즉시 진단

---

## 1. ★ LOCKED VALUES

### 1-1. v12 LOCK (불변)
- commit 559a65e, NET Sharpe 0.686

### 1-2. v18~v19 LOCK (불변)
- build_axis.py SSOT (195750f, 9.4y 검증)
- M17 = front-month (deterministic), M15/M16 = max_vol
- 5월 cross-val 19/19 PASS

### 1-3. v20 NEW LOCK ★

**axis_raw_17axis.parquet (raw, 무변경)**
- shape: (2309, 18)
- range: 2017-01-02 ~ 2026-06-05
- fail count: 0

**axis_raw_v20.parquet (raw + 3 flags) ★**
- shape: (2309, 21)
- 추가 flag:
  - M17_missing: 470 (VKOSPI 선물 거래 단절)
  - M19_missing: 331 (KOSDAQ150 옵션 미상장)
  - M16_expiry_flag: 256 (3/6/9/12월 5~14일)
- M16 outlier cover: 60/60 (100%)

---

## 2. ★ 본 세션 (#15) 진행 내역

### 2-1. Setup
- CWD 잔존 문제 → os.chdir('/content') 추가
- handoff v19 commit (660ccfd) 발견 → HEAD 갱신

### 2-2. K3 영업일 source
- 옵션 C 채택 (ohlcv parquet unique dates)
- 1,846 dates 확보 (2017-01-02 ~ 2024-07-05)

### 2-3. K3 9.4y backfill ★
- 138.2분 (예상 3~5h 대비 단축)
- **fail 0** — v19 §11 risk 완전 해소
- 최종 axis_raw: 2,309 rows

### 2-4. Sanity 결과
- 16/19 axes NaN = 0
- M17 NaN 470 (20.4%) / M19 NaN 331 (14.3%) / M16 outlier 60 → 진단 진입

### 2-5. Anomaly 진단 (raw level)

**M19 = KOSDAQ150 옵션 PCR** (build_axis L160 직접 read)
- 2017년 100% NaN = 옵션 미상장 (2018-03-26 이후 정상)

**M17 = front-month VKOSPI 거래 단절** (20 dates raw dump)
- 20/20 sample = CLS_MISSING (vol=0, cls=빈문자열, spot 정상)
- candidates=6 (contract listing OK)
- → 시장 정보 (저변동성 + 거래 동결)

**M16 outlier = 분기 만기 cluster**
- 60 dates 전부 3/6/9/12월 5~14일
- 2025년 이후 std 4 (vs 2017~2024 std 165~324) — 미시구조 변화

### 2-6. STATE freeze 정책 LOCK

| Axis | 정책 | flag |
|---|---|---|
| M17 | KEEP + flag | M17_missing |
| M19 | KEEP + flag | M19_missing |
| M16 | RAW 유지 + flag | M16_expiry_flag |

### 2-7. M16_expiry_flag 정의 보정
- 1차: day 6~14 → 58/60 cover
- 2차: day 5~14 → 60/60 (100%) ★

---

## 3. ★ STATE VECTOR v20 정의
