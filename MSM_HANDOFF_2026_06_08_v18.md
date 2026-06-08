# MSM 핸드오프 v18 — Phase 4 진입 (v12 LOCK 보존 + v4 raw-state architecture)

**작성일**: 2026-06-08 (KST, MSM 세션 #12 종결)
**대상 repo**: stanleyim/choonsimi-msm
**v17 commit**: d869434
**v18 commit**: (본 push 후 확정)
**상태**: ★ v3 COMBO contaminated 폐기 / axis_v3 z-score 폐기 / KRX OpenAPI 10 endpoint 전부 PASS / raw-state v4 진입 / 500 date raw backfill 완료 (463 rows)
**다음**: K6 (fail 분석 + sanity) → K3 (9.4y backfill 1,800 dates) → v4 STEP 2 (regime)

---

## 0. 절대 원칙 (v17 §0 + v18 신규)

1. §1 추측 금지 (★ 본 세션 4회 위반 — #61~#68 참조, 형 지적 후 정정)
2. §6 3번 검토 (정확성 + 사고 가능성 + 안전장치)
3. §7 옵션 → 형 결정 → 실행
4. §13 매 단계 commit/push
5. MSM = choonsimi-premium 독립 (v10c 6/26 freeze)
6. 외부 검토자 3 원칙
7. 단일 셀 통합 코드
8. Signal ≠ Execution constraint
9. Selection asymmetry: edge_field universe ≠ realized top-K
10. Control manifold ≠ Alpha manifold
11. State manifold > Control manifold (v12)
12. v13: Forward test가 in-sample 못 본 것 발견
13. v14: v12 simulator + regime detection 재현 영구 불가
14. v17: REJECTED state도 STATE의 일부 (filter 거부 cash state 보존 필수)
15. **v18 신규**: build 코드 없는 산출물 = 영구 폐기 대상. cac047b commit (concentrated 3 parquet) 코드 변경 0 → contaminated 확정. axis_v3 z-score 정합 FAIL = build 코드 없음 → 폐기 → raw 기반 v4 진입.
16. **v18 신규**: 출력 숫자 보고 단정 금지. provenance (build commit + 코드) 확인 후만 결론. 본 세션 §1 위반 #61~#63은 모두 출력 숫자만 보고 단정한 패턴.

---

## 1. ★ LOCKED VALUES (v12 baseline 유지, 의미 변경)

### v12 baseline (불변)
- Sharpe IS 0.686 / CAGR 16.48% / MDD -33.13% (9.4y, n=2307)
- LONG: NEUTRAL × bot z_ell top 10, hold 15d, weight 1/10
- SHORT: SHOCK × bot score top 10, hold 5d, weight 1/10
- Cost: 0.30% RT (entry 0.15% + exit 0.15%)
- OOS boundary: 2026-06-04

### v18 의미 변경
- v12 LOCK = baseline for comparison only (재현 영구 불가, simulator 없음)
- 실제 forward test 진행 = v4 raw-state architecture
- realized_log v1.2 (schema TAKEN/REJECTED) 유지

---

## 2. ★ 본 세션 #12 핵심 결정

### 2-1. 폐기 결정
- **v3 COMBO 폐기**: cac047b commit 변경 file = handoff v14 .md 1개 (379 lines 추가)만, 코드 파일 변경 0 → in-sample build 확정 → contaminated
- **β1 walk-forward (LONG OOS 0.697) 재구현 불가**: build 코드 repo에 없음, parquet 결과만 존재
- **axis_v3 z-score 폐기**: 본 세션 I3 정합 검증 FAIL (max diff 2.18, mean 0.69) → build 로직 알 수 없음 → raw 전환

### 2-2. v4 architecture 채택 (J5)
- STEP 1 STATE: S_t = 18 axis raw value (no z-score)
- STEP 2 REGIME: rule-based (shock=hard filter)
- STEP 3 TRANSITION: kNN/kernel local P(S_{t+1}|S_t)
- STEP 4 EDGE: Edge(S_t) = mean(r_{t+1} over kNN)
- STEP 5 TRADEABLE: top/bot 5~10% by Edge
- STEP 6 PORTFOLIO: w_i ∝ Edge, dynamic leverage 0.5~2.0
- STEP 7 EXECUTION: cost 10~25bps, holding ≥ 3d
- 목표: Sharpe 1.0~1.15 안정 (상단 1.2 조건부)

### 2-3. KRX OpenAPI 10 endpoint 전부 PASS
- 확정 URL 8 (sto×2, bon×3, drv×2, etp) + idx 2 (Spec 기반 정확 URL)
- 18 axis source 매핑 완전 확정 (M12/M13 제거, M14 미해결)

---

## 3. ★ 18 axis source 매핑 (확정)

| axis | 정의 | source endpoint / file | 컬럼/계산 |
|---|---|---|---|
| M1 vkospi | VKOSPI 종가 | idx/drvprod_dd_trd | IDX_NM='코스피 200 변동성지수', CLSPRC_IDX |
| M2 vkospi_delta | VKOSPI 등락률 | idx/drvprod_dd_trd | 동일 row, FLUC_RT |
| M3 ytm | KRX 채권지수 평균 YTM | idx/bon_dd_trd | BND_IDX_GRP_NM='KRX 채권지수', BND_IDX_AVG_YD |
| M4 duration | KRX 채권지수 듀레이션 | idx/bon_dd_trd | AVG_DURATION |
| M5 foreign_kospi_cash | KOSPI excl ETF 외인 | web/12008/kospi_excl_etf_94y.parquet | 외국인 + 기타외국인 |
| M6 foreign_kospi_etf | KOSPI ETF 외인 | (kospi_incl - kospi_excl) | 외인 차이 |
| M7 foreign_kosdaq | KOSDAQ 외인 | web/12008/kosdaq_94y.parquet | 외국인 + 기타외국인 |
| M8 inst_kospi | KOSPI excl 기관7합 | web/12008/kospi_excl_etf_94y.parquet | 금융투자+보험+투신+사모+은행+기타금융+연기금 등 |
| M9 inst_kosdaq | KOSDAQ 기관7합 | web/12008/kosdaq_94y.parquet | 동일 7개 sum |
| M10 indiv_kospi | KOSPI excl 개인 | web/12008/kospi_excl_etf_94y.parquet | 개인 |
| M11 indiv_kosdaq | KOSDAQ 개인 | web/12008/kosdaq_94y.parquet | 개인 |
| ~~M12/M13~~ | redundancy 제거 | - | - |
| M14 etf_pension | ETF 연기금 | **미해결** | KRX OpenAPI 10개에 없음, 별도 source |
| M15 basis_k200 | KOSPI200 선물-현물 | drv/fut_bydd_trd | PROD_NM='코스피200 선물', MKT_NM='정규', nearest, TDD_CLSPRC - SPOT_PRC |
| M16 basis_kq150 | KOSDAQ150 선물-현물 | drv/fut_bydd_trd | PROD_NM='코스닥150 선물', 동일 |
| M17 basis_vkospi | VKOSPI 선물-현물 | drv/fut_bydd_trd | PROD_NM='변동성지수 선물', 동일 |
| M18 pc_k200 | KOSPI200 옵션 PCR | drv/opt_bydd_trd | PROD_NM='코스피200 옵션' (월물만, 위클리 제외), PUT/CALL ACC_TRDVOL ratio |
| M19 pc_kq150 | KOSDAQ150 옵션 PCR | drv/opt_bydd_trd | PROD_NM='코스닥150 옵션', 동일 |

**KRX OpenAPI base URL**: https://data-dbg.krx.co.kr/svc/apis
**Header**: AUTH_KEY (Apikey 아님)
**Param**: basDd=YYYYMMDD
**Response**: {"OutBlock_1": [...]}

---

## 4. ★ axis_raw_17axis.parquet 상태

- file: `data/state/axis_raw/axis_raw_17axis.parquet`
- shape: (463, 18)
- columns: date, M1, M2, M3, M4, M15, M16, M17, M18, M19, M5, M6, M7, M8, M9, M10, M11, _n_valid
- date range: 2024-07-08 ~ 2026-06-05
- backfill 결과: 463 / 500 (92.6% 성공)
- fail: 37 dates (`data/state/axis_raw/fail_log.json`)

**6/5 raw value (실측)**:
- M1 vkospi = 73.44 (panic 수준, 정상 15~25)
- M2 Δ% = 0.00
- M3 ytm = 3.957%, M4 dur = 5.022
- M5 foreign_kospi_cash = -2,763,793 (백만원, -2.76조)
- M6 foreign_kospi_etf = -22,122 (백만원)
- M7 foreign_kosdaq = -187,765
- M8 inst_kospi = -1,380,860
- M9 inst_kosdaq = +150,780
- M10 indiv_kospi = +4,223,997
- M11 indiv_kosdaq = +33,694
- M15 basis_k200 = +1.13
- M16 basis_kq150 = -1.42
- M17 basis_vkospi = -0.64
- M18 PCR k200 = 2.314
- M19 PCR kq150 = 1.377

★ VKOSPI 73 + PCR 2.31 = 강한 fear/hedge demand 시장.

---

## 5. ★ fail 37 dates — K6 분석 필요

fail_log.json에 저장. K6 셀에서 분류:
- 한국 공휴일 → 정상 skip (휴장)
- drv/opt timeout → 재시도 필요
- KRX server 일시 장애 → 재시도

---

## 6. ★ v4 architecture 진입 status

| STEP | 상태 |
|---|---|
| 1 STATE (raw S_t) | 463/500 완료, K3 이후 2,307 완성 예정 |
| 2 REGIME | 미진입 (K3 후) |
| 3 TRANSITION (kNN) | 미진입 |
| 4 EDGE | 미진입 |
| 5 TRADEABLE | 미진입 |
| 6 PORTFOLIO | 미진입 |
| 7 EXECUTION | 미진입 |

**현재 forward test (v12 기반, schema v1.2)**:
- 6/4 OOS#1 n=50 (TAKEN 30 + REJECTED 20)
- v12_RAW -440bp / M8 REJECT 0bp (n=1 통계 의미 0)
- mtm OPEN 30 (만기 6/25)

---

## 7. ★ 다음 세션 우선순위

### Step 1 (즉시): K6 (fail 분석 + sanity check, ~13분)
- fail 37 dates 한국 공휴일 vs 진짜 fail 분리
- 463 row sanity (axis 분포 / outlier / 완전성 / 결측)
- 진짜 fail 재시도

### Step 2: K3 (9.4y backfill 나머지 1,800 dates, ~5~6시간)
- 2017-01-02 ~ 2024-07-07
- batch 50 + auto-push (이미 검증된 H2 logic)
- 별도 세션 권장 (Colab 12시간 timeout 안전)

### Step 3: v4 STEP 2 REGIME (rule-based, ~10분)
- shock filter: M1 > 40 (또는 quantile 90%)
- trend: |M5/M7 net flow| 임계 + |M2| 작음
- range: |M2| 작음 + |basis| 작음
- transition: else

### Step 4: v4 STEP 3-4 (kNN + edge)
- normalize: robust (median/IQR)
- kNN k=50 (또는 50~200 sensitivity)
- Edge(S_t) = mean(r_{t+1} over neighbors)
- r_{t+1} source: state_v2 일별 평균 또는 KOSPI200 ETF

### Step 5: STEP 5-7 (tradeable + portfolio + execution)
- top/bot 5~10% by Edge
- shock regime hard filter (trade=0)
- walk-forward backtest

### Step 6: v10c 6/26 결과 + 비교
- choonsimi-premium 6/26 freeze 종결
- v4 forward test 결과 vs v10c forward test

---

## 8. ★ 즉시 실행 가능 옵션

| 옵션 | 내용 | 시간 |
|---|---|---|
| K6 | fail 분석 + sanity (본 핸드오프 §10 셀) | ~13분 |
| K3 | 9.4y 나머지 backfill | ~5~6시간 (별도 세션) |
| K4 | 463 row로 v4 STEP 2 sanity (regime classify) | ~10분 |
| K5 | 463 row로 v4 STEP 3-4 sanity (kNN+edge k=50) | ~15분 |

권장: K6 → K3 → (K4/K5는 9.4y 완성 후 의미)

---

## 9. ★ 실수 누적 (v17 #51~#60 + v18 신규 #61~#68)

v17 #51~#60 유지.

**v18 신규**:

- **#61**: 세션 #12 시작 시 userMemories "v3 COMBO Sharpe ~1.05" 사실 검증 없이 P1 즉시 권장 (즉시 LOCK 결정). v14 산출 build provenance 미확인 + parquet OOS Sharpe 실측 안 함. 형 지적: "내 생각엔, 너의 검증실력이 안되서 이 지경이 되었다". 재발 방지: 세션 시작 시 userMemories 수치는 fact 아닌 hypothesis로 다뤄야 함. build commit 확인 후만 결론.

- **#62**: P1 진단 후 출력 "v3_COMBO 전체 Sharpe 2.271" 보고 → "userMemories 1.05는 부정확" 단정 (§1 위반). 실제는 OOS 1.41 = userMemories 1.05 가까이 = 정합. Claude는 in-sample 전체 metric (2.271) 보고 단정. 형 지적: "이게 사실일수도 있잖아. 너 확신해". 재발 방지: 출력 숫자에 대해 "다른 metric (in-sample vs OOS / 다른 weight scaling)" 가능성 항상 검토 후 단정.

- **#63**: P1 출력 "같은 기간 ΔSharpe +1.583" 보고 → P1-D (v3_COMBO 즉시 LOCK) 권장 (§1 위반). 50% LONG + 50% SHORT weight 가정 / walk-forward 진위 미검증 / build code 미확인. 재발 방지: LOCK 결정 권장은 (1) build code 검증 (2) walk-forward 진위 (3) borrow feasibility 3축 통과 후만.

- **#64**: v17 작성 후 "다운로드 링크 제공"으로 끝, 형이 "자동 push 됐냐" 질문 → Claude가 명시 안 했음. /mnt/user-data/outputs/는 Claude 샌드박스, Colab/GitHub과 분리. 재발 방지: 파일 생성 시 "어디 저장됨 + GitHub 안 됨" 명시 의무.

- **#65**: KRX OpenAPI 추정 endpoint URL 7개 중 5개 정합 (sto/stk_bydd_trd, sto/ksq_bydd_trd, bon/kts_bydd_trd, drv/fut_bydd_trd, etp/etf_bydd_trd), 2개 추측 틀림 (idx/bon_bydd_idx → 실제 idx/bon_dd_trd, idx/drv_bydd_idx → 실제 idx/drvprod_dd_trd). 패턴 일반화 시도 → 실패. 재발 방지: URL prefix 추측 금지, Spec 문서 확인 후만 fetch.

- **#66**: drvprod IDX_NM에서 VKOSPI keyword 검색 ('V-KOSPI', 'VKOSPI') 시 NO MATCH. 실제 정식 명칭 "코스피 200 변동성지수". 영문 약칭 가정이 잘못. 재발 방지: 한국 KRX product 이름은 한국어 정식 명칭 사용 (drvprod IDX_NM 전체 list 출력 후 정확 매칭).

- **#67**: 본 세션 시작 시 P1 권장 = "이미 측정된 +0.36 Sharpe gain" 단정의 근본 원인 분석. userMemories는 이전 Claude 세션의 산출 — 사실 vs 가설 구분 안 됨. 새 세션 진입 시 userMemories의 모든 수치는 provenance 미확인 = 가설로 시작해야 함. 재발 방지: setup cell 후 첫 작업 = userMemories 수치 중 핵심 metric의 source parquet build provenance 확인.

- **#68**: axis_v3 build code 부재 발견 (I3 정합 검증 FAIL). z-score 계산 방식 (rolling window / contract 선택 / Δ vs level) 알 수 없음 → reverse engineering 불가. 폐기 결정. 재발 방지: 모든 산출물 build script (.py 또는 .ipynb)와 함께 commit. parquet only commit 금지.

---

## 10. ★ 다음 세션 합본 셀

### 10-1. Setup cell (paste & run, ~50초)

setup cell은 v18 push 후 새 commit hash 사용. EXPECTED_HEAD_PREFIX는 push 결과 hash 7자리로 갱신.

핵심:
- GH_TOKEN, KRX_ID, KRX_PW, KRX_OPENAPI_AUTH_KEY, ECOS_API_KEY 환경변수 export
- repo clone, HEAD 검증
- engine.py import (14 항목)
- axis_raw_17axis.parquet load (463 rows)
- flow 3 parquet load
- fail_log.json load

### 10-2. K6 실행 셀 (fail 분석 + sanity check, ~13분)

다음 세션 진입 후 별도 셀로 제공. 구성:
- K1: fail_log.json 분석, 한국 공휴일 vs 진짜 fail 분리, real fail 재시도
- K2: 463 row sanity (NaN per column / 분포 quantile / outlier |z|>5 / date gap)

### 10-3. 첫 메시지 권장

```
MSM Phase 4 진입.
MSM_HANDOFF_2026_06_08_v18.md 참고.

상태:
- v12 LOCK baseline (Sharpe 0.686 IS) 유지 (재현 영구 불가)
- v3 전부 폐기 (contaminated 확정)
- axis_v3 z-score 폐기 → raw v4 architecture
- axis_raw_17axis.parquet: 463/500 (2024-07-08 ~ 2026-06-05)
- KRX OpenAPI 10 endpoint 전부 PASS

다음 작업:
1. K6: fail 37 분석 + 463 row sanity (~13분)
2. K3: 9.4y 나머지 1,800 dates backfill (~5~6시간)
3. v4 STEP 2 REGIME (9.4y 완성 후)

§1 추측 X (본 세션 #12 §1 4회 위반 #61~#68 참고).
§6 3축 (정확성/사고/안전).
§7 옵션→형 결정→실행.
```

---

## 11. 파일 인벤토리 (v18 push 직전)

```
choonsimi-msm/
- MSM_HANDOFF_2026_06_02_v1~v4.md
- MSM_HANDOFF_2026_06_03_v6.md
- MSM_HANDOFF_2026_06_04_v7~v11.md
- MSM_HANDOFF_2026_06_05_v12~v13.md
- MSM_HANDOFF_2026_06_07_v14~v17.md
- MSM_HANDOFF_2026_06_08_v18.md  ← 이 문서
- PREF_DIAGNOSIS_2026_06_05.md
- MSM_WORKPLAN_v1~v2.md
- STEP8_PROGRESS.md
- README.md
- engine.py  ★ (v17 산출, 14 항목 정합)
- *.ipynb (data_ingestion / data_supplement / state_vector)
- data/
  - raw/ (active/delisted/macro/short/web/12008)
  - universe/universe_msm.csv
  - state/
    - state_vector_v2/year=*.parquet (v2, 259MB)
    - axis_v3/axis_candidates_19.parquet  ★★ 폐기 결정 (z-score 정합 FAIL)
    - axis_raw/                              ★★ v18 신규
      - axis_raw_17axis.parquet (463 rows, 18 cols)
      - fail_log.json (37 dates)
    - regime/edge/tradeable (v1)
    - edge_v2/edge_field_v2.parquet
  - sim/
    - v2_gamma_best.parquet (v12 LOCK baseline)
  - sim_v3/                                  ★★ 폐기 (cac047b contaminated)
    - concentrated_long/short/combined.parquet
- forward_test/
  - schema/realized_log_v1.json (v1.2, signal_status)
  - log/realized/realized_log.parquet (n=50, 6/4 OOS#1)
  - log/axis_daily/axis_raw_20260605.json (H1 산출)
  - diag/                                    ★★ v18 신규
    - krx_openapi_smoke.parquet (10 endpoint smoke)
    - krx_openapi_schemas.json (8 endpoint + axis_resolution_v2)
    - krx_drv_fut_20260605.parquet
    - krx_drv_opt_20260605.parquet
    - krx_idx_drvprod_20260605.parquet
    - i3_raw_60d_to_20260602.parquet
    - i3_zscore_match.csv
  - baseline.json, README.md
```

---

## 12. 본 세션 (#12) commit 이력

이전 v17: d869434 (engine.py + v17 핸드오프 upload)
본 세션 누적:
- MSM H2 backfill batch × 10 (auto-push, axis_raw_17axis.parquet 갱신)
- 본 핸드오프 v18 push

---

## 13. 핵심 한 줄

본 세션 #12 = 잘못된 path 차단의 세션. v3 COMBO contaminated 폐기 / β1 재현 불가 / axis_v3 z-score 폐기. 진짜 진전 = KRX OpenAPI 10 endpoint 전부 PASS + axis_raw 18 axis source 확정 + 2년치 raw 463 rows 확보. 다음 세션 = K6 → K3 → v4 STEP 2 REGIME.

---

## 14. 정직 메시지

**좋은 것**:
- KRX OpenAPI 10 endpoint 전부 작동 확인 = M14 외 18 axis daily fetch 가능
- 463 row raw backfill = 2년치 v4 STEP 1 input 부분 확보
- contamination 발견 = 잘못된 LOCK 결정 사전 차단
- engine.py + schema v1.2 production-ready

**한계**:
- 본 세션 §1 4회 위반 (#61~#68) — Claude 검증 능력 부족 명확
- 9.4y backfill 미완 (463/2,307 = 20%)
- v4 STEP 2~7 미진입 (regime/transition/edge/tradeable 미검증)
- 진짜 성능 향상 = 0 (인프라만)
- v12 baseline (Sharpe 0.686 IS / 0.494 OOS) 외 실투자 가능 시스템 = 0

**결론**:
- v4 진입 자격은 확보 (raw S_t pipeline)
- 실투자 가능 시점 = 9.4y backfill + v4 walk-forward + OOS 1.5~3개월 후
- 빠르면 2026-09~12

**다음 세션 핵심**: K6 (13분) → K3 결정. 9.4y 완성이 v4 진입 전제.

---

**작성자**: Claude (MSM 세션 #12 종결, Phase 4 진입)
**상태**: v3 폐기 / axis_v3 z-score 폐기 / raw v4 진입 / KRX OpenAPI 18 axis source 확정 / 463 rows backfill
**다음 작업**: K6 (fail 분석 + sanity) → K3 (9.4y backfill)

끝.
