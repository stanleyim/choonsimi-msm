# MSM 핸드오프 v17 — Phase 3 H4 완료 (Path D OOS 첫 진검증 + M6 정정)

**작성일**: 2026-06-07 (KST, MSM 세션 #11 종결)
**대상 repo**: stanleyim/choonsimi-msm
**최신 commit**: 11c7e15 (H4 Path D OOS axis recompute + strict eval)
**상태**: ★ Path D axis 정의 ground truth 확정 + OOS 2일 판정 완료 + M6 정의 정정 + 첫 disagreement 발견

---

## 0. 절대 원칙 (v16 §0 + v17 신규)

1. §1 추측 금지
2. §6 3번 검토 (정확성 + 사고 가능성 + 안전장치) — 셀 작성 전
3. §7 옵션 → 형 결정 → 실행
4. §13 매 단계 commit/push
5. MSM = choonsimi-premium 독립 (6/26 freeze)
6. 외부 검토자 3 원칙
7. 단일 셀 통합 코드
8. Signal ≠ Execution constraint
9. Selection asymmetry
10. Control manifold ≠ Alpha manifold
11. State manifold > Control manifold
12. Forward test가 in-sample 못 본 것 발견
13. **v17 신규**: 문서-구현 불일치 가능. axis 재계산 시 sanity (corr=1.0/MAE=0) 검증 의무

---

## 1. ★ Path D Axis 정의 LOCKED (corr=1.000000, MAE=0.000000)

window = 60d, reindex to biz_full

| axis | base series |
|---|---|
| M2_z_vkospi_delta | vkospi_ohlc["등락률"] |
| M8_z_inst_kospi | kospi_excl_etf[금융투자,보험,투신,사모,은행,기타금융,"연기금 등"].sum(axis=1) |
| M6_z_foreign_kospi_etf | (kospi_incl_etf − kospi_excl_etf)["외국인"+"기타외국인"]  ★ 외인합 |

Path D strict logic:
- M2 (T-1) > -1.0
- M8 (T-1) > 0.0
- M6 (T-1) < 0.0
- 3 모두 AND → LONG entry / 아니면 NO_TRADE

---

## 2. ★ OOS 판정 결과 (2026-06-04, 2026-06-05)

| entry | T-1 | M2 | M8 | M6 | strict | decision |
|---|---|---|---|---|---|---|
| 6/4 | 6/2 | -0.838 | **-0.309 ❌** | -0.245 | False | NO_TRADE |
| 6/5 | 6/4 | +0.386 | +0.783 | -0.266 | **True** | **LONG** |

**해석**:
- 6/4: M8 (기관 KOSPI 매도)이 LONG block. v12 LOCK signal (10 codes) 존재했으나 Path D가 회피
- 6/5: Path D LONG signal. 그러나 v12 LOCK signal 자체 부재 (T-2 6/2 잔고 fetch 실패, v13 §2-4 issue)
- **disagreement = Phase 3의 진검증 가치**

---

## 3. ★ Realized PnL (1점, 통계의미 0)

| 측정 | 값 |
|---|---|
| 6/4 LONG 10 EW 1d return (gross) | -424.9 bp |
| Path D 회피 결과 | 0 bp |
| ΔPnL (v12 - filtered) | -424.9 bp |

→ 1점만으로 결론 불가. 20~30 sample 누적 필요.

---

## 4. ★ M6 정의 정정 (실수 #66)

- `data/raw/web/12008/README.md` L98: `(kospi_incl - kospi_excl)["외국인"]` 단일 표기
- 실제 axis_candidates_19 구현: "외인합" = "외국인" + "기타외국인" (외국인 + 외국인등록 외 외국인)
- corr=0.999832 (외국인 only) vs corr=1.000000 (외인합) → 외인합 확정
- README 정정 필요 (다음 세션)

---

## 5. ★ 6/3 KRX 12008 raw 누락 (실수 #67)

- 6/3은 한국 영업일이지만 vkospi/kospi_excl/kospi_incl raw 3 source 모두 6/3 데이터 없음
- 6/4 entry biz T-1 = 6/2 (raw 기준)
- 원인 미확정 (KRX 12008 web data 일시 누락 또는 영업일 식별 오차)
- 다음 세션: 6/3 raw 재수집 시도 또는 영업일 list source 통일

---

## 6. ★ 다음 세션 우선순위

| 옵션 | 내용 | 시간 |
|---|---|---|
| **N1** | 6/8 (월) daily routine 실행 검증 (`forward_test/daily_routine.py`) | ~3분 |
| **N2** | M6 정의 정정을 axis_candidates_19 외 18 axis에도 sanity (전수 재현 corr=1.0 검증) | ~5분 |
| **N3** | 6/3 KRX 12008 raw 재수집 시도 | ~3분 |
| **N4** | OOS realized PnL log schema 확립 (entry × hold day × 종목 × PnL) | ~5분 |
| **N5** | choonsimi-premium 6/26 결과 시점 대기 (지금 시점 X) | — |

권장: N1 → N2 → N4

---

## 7. 파일 인벤토리 (HEAD 11c7e15 기준)

신규:
- forward_test/axis_oos/
  - axis_v3_oos_tail.parquet
  - axis_v3_oos_tail_T1.parquet
  - pathD_eval_oos.parquet
  - pathD_eval_oos.csv
  - README.md
- forward_test/realized/
  - realized_20260604_to_20260605.parquet
  - realized_20260604_to_20260605.csv
- forward_test/daily_routine.py

기존 핵심 유지:
- data/sim/v2_gamma_best.parquet (v12 LOCK)
- data/state/state_vector_v2/year=*.parquet
- data/state/axis_v3/axis_candidates_19.parquet
- data/state/axis_v3/sweep_C_filter_v12pnl.parquet

---

## 8. ★ 실수 누적 (v16 #1~#65 + v17 신규)

- **#66**: README.md (12008) L98 "외국인" 단일 표기 vs 실제 구현 "외인합" 불일치. 첫 H4 sanity assert FAIL (corr=0.9998 vs threshold 0.9999) 발생. 재발 방지: 새 axis 정의 시 base series는 sanity check (corr=1.0)로 ground truth 검증 의무. 문서 표기는 검증 후 정정.
- **#67**: 6/3 KRX 12008 raw 누락 확인. 6/4 biz T-1 = 6/2 (raw 기준). 영업일과 raw 일치성은 미보장 → biz_full = raw common dates union으로 처리하는 패턴 확립.

---

## 9. ★ 다음 세션 합본 setup 셀 (paste & run)

세션 #10/#11과 동일 구조. 갱신 사항:

```python
EXPECTED_HEAD_PREFIX = '11c7e15'   # ← v17 commit 이후 git push 시 갱신
```

(주의) 본 핸드오프 commit 시 hash 바뀜. 다음 세션 진입 시 `git log --oneline -3`로 실제 HEAD 우선 확인 후 prefix 갱신.

---

## 10. ★ 핵심 한 줄

v12 LOCK 유지. Path D axis 3개 (M2/M8/M6) 정의 corr=1.0 ground truth 확정 (M6=외인합). OOS 2일 판정 = 6/4 NO_TRADE / 6/5 LONG. v12와 첫 disagreement (6/4) 발견. Realized 1점 측정 (통계의미 0). Daily routine template 확립. 다음 세션 = 6/8 daily 실행 + 18 axis 전수 sanity + realized schema.

---

**작성자**: Claude (MSM 세션 #11, Phase 3 H4 완료)
**상태**: Path D OOS 검증 인프라 LOCK, axis 정의 검증 완료, 실제 누적 시작
**다음**: daily routine 실 운용 + OOS realized log 누적
