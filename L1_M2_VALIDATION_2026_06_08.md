# L1 검증 결과 — M2 (VKOSPI FLUC_RT) outlier validation

**작성일**: 2026-06-08 (KST, MSM 세션 #12)
**대상**: M2 axis (vkospi_delta) outlier 검증
**결과**: ★ CASE 1 확정 (M2 유지)

---

## 1. 검증 사실

7 test dates, 6 MATCH / 1 boundary issue:

| date | P_t | P_t-1 | calc_delta | FLUC_RT | match |
|---|---|---|---|---|---|
| 2024-08-05 | 45.86 | 21.77 | +110.657 | +110.660 | ★ MATCH |
| 2024-08-06 | 43.08 | 45.86 | -6.062 | -6.060 | ★ MATCH |
| 2024-08-07 | 30.17 | 43.08 | -29.968 | -29.970 | ★ MATCH |
| 2025-04-04 | 26.80 | 30.17 | -11.170 | +2.720 | ✗ boundary (t-1 fetch 누락) |
| 2025-04-07 | 44.23 | 26.80 | +65.037 | +65.040 | ★ MATCH |
| 2025-04-08 | 37.83 | 44.23 | -14.470 | -14.470 | ★ MATCH |
| 2025-04-09 | 40.97 | 37.83 | +8.300 | +8.300 | ★ MATCH |

---

## 2. 극단값 역사적 정합

- **2024-08-05 +110.66%**: 일본 캐리트레이드 청산 + 한국 사이드카 발동 (실제 panic)
- **2025-04-07 +65.04%**: 트럼프 관세 발표 (2025-04-03) 후 panic 정합

→ **KRX 데이터 정합. 데이터 오류 아님**.

---

## 3. M2 정의 확정

### Raw 정의
```python
M2_raw = FLUC_RT  # KRX idx/drvprod_dd_trd 원본 그대로
```

### Fallback (경계 케이스만)
```python
if t-1 not in dataset:
    M2_raw = (P_t / P_{t-1} - 1) * 100  # 재계산
```

### Scaled (kNN distance metric input)
```python
M2_scaled = (M2_raw - median) / IQR  # robust scaling
```

---

## 4. v4 architecture 적용

| 적용 위치 | 사용 정의 |
|---|---|
| STEP 1 STATE | M2_raw (보존) + M2_scaled (kNN용) |
| STEP 2 REGIME | shock_condition = (M1 > Q90) OR (abs(M2_raw) > Q95) |
| STEP 3 TRANSITION | M2 extreme value tail behavior 유지 |
| STEP 4 EDGE | M2 raw로 kNN, scaled로 distance |

---

## 5. K3 진입 조건 충족

- M2 정의 확정 ★
- 극단값 데이터 오류 0 ★
- 기존 463 row sanity OK ★

→ **K3 (9.4y backfill 1,800 dates) 별도 세션 진입 가능**.

---

## 6. 본 세션 종결 사유

- Colab free 런타임 약 1시간 사용
- K3 추정 5~6시간 = disconnect risk
- 별도 clean session에서 K3 진행 권장

---

**작성자**: Claude (MSM 세션 #12, L1 검증)
**다음 작업**: 새 세션 → K3 (9.4y backfill, 별도 hosted runtime 권장)
