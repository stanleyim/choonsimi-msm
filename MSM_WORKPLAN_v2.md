# MSM 작업계획 v2 — Phase 3 OOS 진검증 로드맵

**작성일**: 2026-06-07 (KST, MSM 세션 #10 종결)
**Supersedes**: MSM_WORKPLAN_v1.md
**핵심 변경 (v1 → v2)**: Path D 확정 (forward test OOS 진검증) + state v3 axis 정식 통합 일정 명시

---

## 0. Mission Statement (v1과 동일)

MSM 시스템의 최종 목적:
→ "시장에서 돈이 되는 상태 영역을 구조적으로 추출하는 것"

5-STEP pipeline:
1. STATE VECTOR (S_t = price, volume, flow, volatility, liquidity)
2. REGIME (trend / range / shock / transition)
3. TRANSITION P(S_{t+1} | S_t)
4. EDGE FIELD (expected return surface)
5. TRADEABLE REGION (positive EV)

---

## 1. 현재 상태 (2026-06-07 종결)

### 1-1. LOCKED Systems
| System | Status | Locked Sharpe |
|---|---|---|
| STEP 1~5 v10 | LOCK | — |
| STEP 6 SHOCK SHORT | LOCK | — |
| STEP 7 V1 T4 Control | LOCK | — |
| **STEP 8 MSM v2 Production** | **LOCK** | **0.686 NET, 1.67 GROSS** |

### 1-2. Data 자산
| Asset | Coverage | Size |
|---|---|---|
| state_vector_v2 | 2017~2026.06 (2307 days) | 259MB, 2.79M rows × 26 cols |
| short volume/balance | 9.4y | 146MB |
| macro_10y | 7 series 9.4y | small |
| web/12008 | KOSPI 시장분리 외인/기관 3 file | 560KB |
| **web/8 type** | **bond_idx, vkospi_ohlc, etf_flow, basis×3, pc×2** | **770KB** |
| axis_v3 카탈로그 | 19 axis + corr matrices | small |
| v2_gamma_best.parquet | v12 LOCK daily PnL | small |

### 1-3. Forward Test 인프라
- baseline.json
- 6/4 LONG 10종목 (OOS Day-1)
- daily routine template 미완성 (다음 세션 작업)

### 1-4. 보류 항목
- 채권 4종 (투자자별 거래실적) — KRX 데이터광장 합산 데이터, daily 못 받음
- KRX OpenAPI 4축 — 월요일 6/8 승인 여부 확인 예정

---

## 2. ★ Phase 3 — OOS 진검증 (현재 진행 중)

### 2-1. Path D 확정 사유

**v14 §0 명시 + 본 세션 #10 B1 시도 결과**:
- v12 simulator code = 영구 사라짐
- regime detection logic = 영구 사라짐
- 자체 simulator로 v12 LOCK 0.686 재현 → **불가능**
- in-sample 검증은 Protocol C (sanity)에서 멈춤
- **유일한 진검증 = forward test OOS**

### 2-2. Phase 3 작업 list

**Phase 3.1 — Daily Routine 확립** (다음 세션, ~10분)
- forward_test/pipeline_daily.py 단일 셀 작성
- 매일 자동: state_vector_v2 갱신 → entry candidates → axis filter → log → push
- 6/4 OOS LONG signal에 M8/M2/M6 filter 적용 후 재계산
- 6/5+ daily PnL 측정 시작

**Phase 3.2 — OOS PnL 누적** (1주~1개월)
- 매일 1셀 실행 = entry + realized return log
- 7거래일 후 1차 점검
- 20거래일 후 1차 통계 의미

**Phase 3.3 — Axis Filter 진검증** (1개월 후)
- M8 (z_inst_kospi > 0.0): in-sample ΔSh +0.229, MDD -22.9%
- M2 (z_vkospi_delta > -1.0): in-sample ΔSh +0.231, active 86%
- M6 (z_foreign_kospi_etf < 0.0): in-sample ΔSh +0.170, MDD -22.8%
- OOS ΔSharpe vs in-sample 비교 → axis validity 판정

**Phase 3.4 — KRX OpenAPI 4축** (월요일 승인 후)
- v15 §10 작업 진행 (basis_10y, pcr_10y, etf_10y, kts_10y)
- 채권 4종 endpoint 존재 시 추가 수집

---

## 3. Phase 4 — State v3 정식 통합 (Phase 3 후 2~3주)

### 3-1. 진입 조건
- Phase 3.3 결과 axis 1~3개 OOS 검증 PASS
- 또는 Phase 3 2개월 누적 시점

### 3-2. 작업
- df_sv_v2 (2.79M rows × 26 col) + 16 axis 통합
- axis는 market-wide (date × axis) 라 종목×일자에 broadcast
- state_vector_v3 정식 발행 (date × code × 26+16 = 42 columns)
- v12 LOCK config (LONG: NEUTRAL × bot z_ell, SHORT: SHOCK × bot score) 그대로 유지
- axis는 entry filter로만 작동, weight/selection 변경 X

### 3-3. 산출
- data/state/state_vector_v3/year=*.parquet
- forward_test/v3_signals/{date}.json (axis-filtered signals)
- 이전 forward_test/log와 비교 가능

---

## 4. Phase 5 — Dual-Engine 검토 (6/26 이후)

### 4-1. 진입 조건
- choonsimi-premium v10c 6/26 forward test 결과 receive
- MSM v2 동기간 OOS PnL 누적

### 4-2. 작업
- v10c vs MSM v2 동기간 비교
  - Sharpe, MDD, CAGR
  - 종목 overlap 비율
  - regime별 성과
- dual-engine 가능성 검토:
  - v10c (cross-sectional 5축 rank) + MSM v2 (state space regime) = 독립 alpha 가능성
  - 같은 universe에서 둘 다 신호 강한 종목 → 가중치 강화
  - 반대 신호 → 보류

### 4-3. 산출
- dual_engine_v1.md (검토 보고서)
- comparison_v10c_vs_msm.parquet

---

## 5. Phase 6 — STEP 9 (state v3+ 추가 axis, 미정)

### 5-1. 진입 조건
- Phase 4 state v3 안정화 후
- 새 axis 후보 (sector / market regime / uptick 등) 식별 필요

### 5-2. 작업 (v13 §4-1 참조)
- sector axis (KOSPI/KOSDAQ industry classification)
- market_regime (KOSPI200 trend strength)
- uptick rule effect
- short squeeze indicator

---

## 6. 즉시 실행 Backlog (다음 1~3 세션)

### 6-1. 즉시 (다음 세션)
- [ ] Daily routine 단일 셀 작성
- [ ] M8/M2/M6 filter 6/4 신호에 적용
- [ ] KRX OpenAPI 승인 확인
- [ ] forward_test/log/daily/ 디렉토리 시작

### 6-2. 1주 내
- [ ] 6/8~6/15 daily PnL 누적
- [ ] 7거래일 첫 점검 (axis filter 작동 여부)
- [ ] KRX OpenAPI 4축 일부 수집 시작

### 6-3. 1개월 내
- [ ] 20거래일 OOS 누적
- [ ] 1차 통계 의미 시작
- [ ] 채권 4종 path 결정 (KRX OpenAPI / 정보데이터시스템 / 영구 보류)
- [ ] 6/26 v10c 결과 receive 준비

---

## 7. 위험 관리 원칙 (v1과 동일)

### 7-1. v12 LOCK 절대 변경 금지
- Sharpe 0.686, MDD -33.13% 그대로 유지
- weight / selection / hold / regime 정의 변경 X
- axis는 entry filter로만 추가 가능

### 7-2. simulator 재현 시도 금지
- v14 §0 + v16 §57 명시
- backtest reverse-engineering 영구 금지
- v12 비교 baseline = `df_eq_v2_best`만 사용

### 7-3. forward test 인프라 최우선
- daily routine = 모든 검증의 기반
- 1셀 실행, 누락 0
- log 누적 + git push 매일

### 7-4. 채권 4종 = 강행 금지
- 일별 daily 받을 path 명확해질 때까지 보류
- 합산 데이터로 axis화 불가능 (재시도 X)

---

## 8. KPI (각 Phase 종료 시점)

### Phase 3 종료 KPI (1개월 후 ~7/7)
- 약 20 OOS 거래일 누적
- axis-filtered Sharpe vs raw Sharpe (in-sample 0.686 baseline)
- M8 filter MDD 개선 측정 가능
- 통계 신뢰도: 낮지만 방향성 확인 가능

### Phase 4 종료 KPI (Phase 3+2주, ~7/21 예상)
- state_vector_v3 정식 발행
- axis 통합된 종목×일자 패널
- forward_test 산출물에 v3 signal 추가

### Phase 5 종료 KPI (6/26 이후)
- v10c vs MSM v2 비교 보고서
- dual-engine 가능성 판정

---

## 9. Open Questions (다음 세션 결정 필요)

### 9-1. M8/M2/M6 중 forward test 1순위?
- M8 best risk-adjusted (MDD -22.9%)
- M2 best gain (+0.231) but weak filter (86% active)
- M6 second-best risk (MDD -22.8%)
- 권장: M8 단독 적용 OR M8 ∩ M6 교집합

### 9-2. KRX OpenAPI 승인 시 우선순위?
- 4축 (basis / pcr / etf / kts) 동시 수집 vs 1축씩
- 권장: 1주 1 axis (안전, batch push)

### 9-3. 채권 4종 영구 보류 vs 재시도?
- KRX 정보데이터시스템 [16xxx] 메뉴 확인 (형 작업)
- 또는 KRX OpenAPI 채권 endpoint 확인
- 권장: 이번 주 정보 받고 결정

---

## 10. 정직 메시지

본 작업계획 v2의 핵심:
- **v12 LOCK이 진짜 alpha인지 OOS로만 알 수 있다**
- Protocol C로 in-sample 검증 끝났음 (M8/M2/M6 ΔSh +0.23/+0.23/+0.17)
- 자체 simulator는 v12 재현 불가 (v14 §0 영구 사실)
- → **daily routine 확립 + 1~3개월 OOS 누적**이 유일한 path

Phase 3.1 = 모든 것의 시작. 다음 세션 즉시 daily routine 셀 작성.

---

**작성자**: Claude (MSM 세션 #10)
**Supersedes**: MSM_WORKPLAN_v1.md
**다음 갱신**: Phase 3.1 완료 시 (Daily routine 확립)
**검토 주기**: 매 1주 (forward test 누적 시점)

끝.
