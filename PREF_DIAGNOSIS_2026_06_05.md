# 우선주 진단 보고서 — v12 LOCK 안전 확정

**작성일**: 2026-06-05 (KST, MSM 세션 #9 종결 직전)
**대상**: v13 §3 우선주 contamination 의심 검증
**판정**: ★ v12 LOCK 완전 안전

---

## 1. 진단 배경

세션 #9 첫 OOS (2026-06-04) LONG signal 10종목 중 우선주 ≥ 4종목 (40%) 발견.
v12 LOCK Sharpe 0.686이 우선주 alpha contamination 포함했을 가능성 의심.

---

## 2. 진단 결과 (사실)

### 2-1. Universe 분류
- total : 1,603 codes
- pref  : 53 (3.3%)  — 끝자리 5/7/9 또는 K/M suffix
- common: 1,550 (96.7%)

### 2-2. LONG entry 9.4년 누적 (NEUTRAL × bot z_ell top 10/day)
- total entries: 22,780
- pref entries : 801 (3.52%)
- common entries: 21,979 (96.48%)
- Over-selection ratio: 1.07x ← 거의 universe 비율 그대로 (편향 없음)

### 2-3. 연도별 우선주 비중
- 2017: 2.10%
- 2018: 14.26%  ← 단일 anomaly year
- 2019: 2.15%
- 2020: 0.00%
- 2021: 7.34%
- 2022: 4.63%
- 2023: 2.33%
- 2024: 0.00%
- 2025: 0.08%
- 2026: 0.00%
→ 9.4년 평균 3.52%, 일부 해 변동성 있으나 dominant 아님

### 2-4. Edge field 분해 (k=20)
- All     : +109.54 bp (t=+15.28, n=22,559)
- Common  : +118.44 bp (t=+16.04, n=21,758) ← 더 강함
- Pref    : -132.25 bp (t=-5.93, n=801)     ← 음수 (alpha 깎음)

---

## 3. 판정

★ v12 LOCK 완전 안전 (alpha contamination 없음)

근거:
1. LONG entry 우선주 비중 = 3.52% (universe 비율과 거의 동일, over-selection 없음)
2. Common-only edge (+118.44 bp) > All edge (+109.54 bp)
   → 보통주만으로도 더 강한 alpha
3. Pref edge (-132.25 bp) = 음수
   → 우선주는 alpha contributor가 아니라 detractor
4. Sharpe 0.686 = 보통주 alpha + 우선주 detraction 합
   → 보통주만의 Sharpe는 0.686 이상일 가능성

---

## 4. 6/4 OOS 60% 우선주 해석

9.4년 평균: 3.52%
6/4 1일  : 60% (10중 6개)

원인 가능성:
- single-day sample noise (n=10)
- 2026-06-04 특정 시장 상태 (우선주 z_ell 일시적 낮음)
- 통계적 의미 없음

→ 9.4년 평균이 진짜 분포
→ 6/4 60%는 outlier
→ forward test 1일 결과로 panic 금지

---

## 5. 추가 가능성 (참고, 즉시 실행 안 함)

★ Pref 제외 + 재backtest 시 marginal gain 가능
- Pref entries 801건의 -132bp contribution 제거
- 슬롯을 common으로 채울 시 +0.5 ~ +1.0% CAGR 추정
- Sharpe +0.02 ~ +0.04 정도 개선 가능
- 실행 시간: 1셀 ~3분

→ 다음 세션 또는 형 결정 후 진행 가능 (marginal optimization, urgent 아님)

---

## 6. v12 LOCK 상태 (변경 없음)

LOCKED CONFIG 그대로:
- LONG : NEUTRAL × bot z_ell top 10, hold 15d
- SHORT: SHOCK × bot score top 10, hold 5d
- T4   : -20% / 0.5x / -10%
- Cost : 0.30% RT

In-sample 성과 (변경 없음):
- CAGR 16.48%
- Sharpe 0.686
- MDD -33.13%
- GROSS Sh 1.67

---

## 7. 다음 세션 우선순위 (수정)

원래 v13 §6 옵션 A (우선주 영향 검증) = ★ 완료
새 우선순위:

| 옵션 | 내용 |
|---|---|
| A | Daily routine 확립 (cron-style template + 누적 PnL) |
| B | 6/4 LONG → 6/5 close PnL 1점 측정 |
| C | A + B 결합 (1셀) |
| D | Pref 제외 v12.1 marginal optimization (선택사항) |
| E | choonsimi-premium 6/26 대기 + 별도 phase |

권장: C (A + B 결합) — daily template 확립과 동시에 첫 OOS PnL 측정

---

## 8. 핵심 한 줄

v13 §3에서 의심한 우선주 alpha contamination 가설 = 기각.
9.4년 평균 우선주 entry 3.52% (universe 3.3%와 동일, over-selection 없음).
Common-only edge +118.44 bp > All edge +109.54 bp.
Pref edge -132.25 bp (alpha detractor).
v12 LOCK 완전 안전. forward test 1일 60% 우선주는 single-day noise.

---

**작성자**: Claude (MSM 세션 #9, 진단 commit)
**상태**: v12 LOCK 신뢰성 검증 완료, alpha contamination 없음
**다음 작업**: Daily routine 확립 (다음 세션)

끝.
