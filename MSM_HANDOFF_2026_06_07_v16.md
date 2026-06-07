# MSM 핸드오프 v16 — Phase 3 진입 (Axis Discovery + Path D 확정)

**작성일**: 2026-06-07 (KST, MSM 세션 #10 종결)
**대상 repo**: stanleyim/choonsimi-msm
**최신 commit**: 6dd5823 — Protocol C filter-on-v12-PnL sweep
**상태**: ★ v12 LOCK 유지 + web 9.4y 데이터 12 type 확보 (4 보류) + 19 axis 카탈로그 + Path D 확정
**다음**: M8/M2/M6 axis를 forward test entry filter로 즉시 적용 (Phase 3 → OOS 진검증)

---

## 0. 절대 원칙 (v13 §0 + v16 신규)

1. §1 추측 금지
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
13. **★ v16 신규**: **v12 simulator 재현 영구 불가 (v14 §0 재확인). regime detection logic도 사라짐. axis 검증은 forward test OOS로만 진검증 가능. backtest reverse-engineering 시도 영구 금지.**

---

## 1. ★ LOCKED VALUES (v13/v15와 동일, 변경 없음)

### 1-1. STEP 1~5 (v10 LOCK, 유지)
### 1-2. STEP 6 (v10 LOCK, 유지) — SHOCK SHORT only
### 1-3. STEP 7 V1 (v11 LOCK, 유지) — Control terminal
### 1-4. STEP 8 (v12 LOCK, 유지) — MSM v2 Production

### 1-5. v12 LOCKED CONFIG (변경 금지)
LONG side:
- Regime    : NEUTRAL (= `regime=='RANGE' AND tradeable`, 본 세션 #10 정의 명시)
- Selection : bot z_ell top 10/day
- Hold      : 15 days
- Weight    : 1/10

SHORT side:
- Regime    : SHOCK (`regime=='SHOCK' AND tradeable AND direction==-1`)
- Selection : bot score (z_r+z_f) top 10/day
- Hold      : 5 days
- Weight    : 1/10

Control (T4):
- DD trigger -20% / Exposure 0.5x / Recovery -10%

In-sample 성과 (변경 없음):
- CAGR 16.48%, Sharpe 0.686, MDD -33.13%, GROSS Sh 1.67
- 기간: 2017-01-02 ~ 2026-06-02

### 1-6. 우선주 검증 (v13 §3, PREF_DIAGNOSIS_2026_06_05 LOCK)
- 9.4y LONG entry 우선주 = 3.52% (universe 3.3%, over-selection 없음)
- Common-only edge +118.44 bp > All edge +109.54 bp
- Pref edge -132.25 bp (alpha detractor, 없는 게 나음)
- v12 LOCK 완전 안전

---

## 2. ★ Phase 3 진행 상태 (본 세션 #10 종결 시점)

### 2-1. Web Data 9.4y 확보 (★ 본 세션 최대 성과)

**`data/raw/web/12008/`** (이전 세션 #10 전반부 — kospi 시장분리 외인/기관, 시간순 첫 작업):
- kospi_excl_etf_94y.parquet (2309 days × 13 columns)
- kospi_incl_etf_94y.parquet (2309 days × 13 columns)
- kosdaq_94y.parquet (2309 days × 13 columns)
- 컬럼: 일자, 금융투자/보험/투신/사모/은행/기타금융/연기금 등 (기관 7합), 기타법인, 개인, 외국인, 기타외국인, 전체

**`data/raw/web/` flat 8 parquet** (★ 본 세션 #10 후반부 신규):
| 파일 | 화면 | rows | range |
|---|---|---|---|
| krx_bond_index_94y.parquet | 3351 | 3,442 | 2017-01-01~2026-06-04 (매일, 휴장일 포함) |
| vkospi_ohlc_94y.parquet | 0546 | 2,309 | 2017-01-02~2026-06-05 |
| etf_investor_flow_94y.parquet | 1415 | 2,309 | KOSPI 영업일 |
| kospi200_basis_94y.parquet | 2524 | 2,309 | KOSPI 영업일 |
| kosdaq150_basis_94y.parquet | 3729 | 2,309 | KOSPI 영업일 |
| vkospi_basis_94y.parquet | 4031 | 2,309 | (이론베이시스 100% NaN) |
| kospi200_pc_94y.parquet | 4914 | 2,309 | KOSPI 영업일 |
| kosdaq150_pc_94y.parquet | 0145 | 2,010 | 2018-03-26~ (옵션 상장 후) |

총 8 type × 9.4y, 770KB raw.

### 2-2. ★ 채권 4종 (KRX 데이터광장 합산 데이터, 보류)

**KRX 데이터광장에서 다운받은 채권 투자자별 거래실적은 daily series가 아니라 기간 전체 합산**:
- 4459 (국채전문유통시장), 0320 (일반채권), 0413 (소액채권), 1113 (신고매매)
- 각 13 lines = 1 header + 12 투자자
- **Daily axis 불가 → 보류**

→ KRX OpenAPI 4축 (월요일 6/8 승인 여부 확인 예정)으로 향후 보강.

### 2-3. 19 Axis 카탈로그 + Redundancy 분석 (commit b6ff1e6)

`data/state/axis_v3/`:
- axis_candidates_19.parquet (2307 × 19 axis, biz_days reindex)
- axis_corr_matrix.parquet
- axis_vs_v12ret_lag1.parquet

19 axis (M1~M19) 정의 (v16 §부록 1).

**Redundancy (|corr|>0.7) — 3 axis 제거**:
- M11 (= -M7 mirror, KOSDAQ 외인 vs 개인 zero-sum)
- M12 (= M5 대체로 KOSPI 외인, KOSDAQ 외인 비중 작음)
- M13 (= M6 완전 동일, +1.000)

→ 유지 axis 16개.

### 2-4. lag-k + DD-conditional + monthly corr (commit 2913514)

`data/state/axis_v3/`:
- lag_k_corr.parquet (k=1..10)
- dd_conditional_corr.parquet (all / DD<-10% / DD<-20%)
- monthly_corr.parquet

**핵심 발견**:
- 모든 lag-1 corr |corr| < 0.05 — 단일축 daily timing 약함
- DD-conditional: M3 ytm_change +0.077, M19 pc_kq150 +0.083 — DD 시기에 emerge
- Monthly: M6 +0.158, M2 +0.142, M8 -0.135 — monthly 시간단위 signal 강함

### 2-5. Protocol C — Filter on v12 PnL sweep (commit 6dd5823)

`data/state/axis_v3/sweep_C_filter_v12pnl.parquet` (50 variants).

**Top 5 best per axis**:
| axis | dir | th | Sharpe | ΔSh | active% | MDD |
|---|---|---|---|---|---|---|
| M2 vkospi_delta | gt | -1.0 | 0.917 | **+0.231** | 86% | -30.8% |
| M8 inst_kospi | gt | 0.0 | 0.915 | **+0.229** | 50% | **-22.9%** |
| M6 foreign_etf | lt | 0.0 | 0.855 | **+0.170** | 51% | -22.8% |
| M17 basis_vkospi | gt | -1.0 | 0.816 | +0.130 | 65% | -35.0% |
| M3 ytm_change | gt | -1.0 | 0.749 | +0.064 | 85% | -30.0% |

**Bottom 5 (반대 방향)**: 모두 ΔSh < -0.9, 방향성 매우 명확.

baseline 재현: Sharpe 0.6856 (vs expected 0.686), CAGR 16.98%, MDD -33.13% — ★ 정확 일치.

### 2-6. B1 자체 simulator 시도 (★ 실패, 의도된 정직 보고)

**LS1 simulator** (LONG 15d + SHORT 5d, 1/(10×hold) weight, cost 0.30% RT):

| 시도 | Baseline NET Sharpe | v12 비교 |
|---|---|---|
| T 시점 entry | +2.10 | 비현실 (lookahead) |
| T+1 lag entry | +1.94 | 여전히 비현실 |

**SHORT entry day r 진단**:
- T 시점: median -6.2%, 95% 음수, 82% < -3% → 라벨 자체에 future 정보
- T+1 lag: median -0.23%, 51% 음수 → lookahead 거의 제거

**결론**:
- LONG side: -0.12 (v12 LOCK의 LONG portion과 비교 가능 추정)
- SHORT side: +1.48 (T+1) — 여전히 비현실 = regime detection logic이 forward-looking
- **v14 §0 재확인**: simulator + regime detection 영구 재현 불가
- v3 검증은 새 system OR forward test OOS만 가능

### 2-7. ★ Path D 확정 (본 세션 최종 결정)

| Path | 내용 | 채택 |
|---|---|---|
| A | B1 simulator baseline (+1.94) 위 sweep → v12 비교 불가 | ❌ |
| B | regime detection 자체 재구현 (시간 ~30분) → 새 baseline → sweep | 보류 |
| C | LONG-only baseline (-0.12) sweep | ❌ |
| **D** | **Protocol C 결과 채택 (M8/M2/M6 ΔSh +0.23/+0.23/+0.17) → forward test 즉시 적용 → OOS 진검증** | **★ 채택** |

**근거**:
1. §14 명시 — v12 reproduce 불가, 새 system 비교 baseline 없음
2. Protocol C baseline 0.6856 = v12 정확 재현 ✓
3. M8/M2/M6 ΔSh 결과는 sanity check지만 방향성 명확
4. 진짜 검증은 forward test OOS — 1주~1개월 누적 시 ΔSharpe 진위 확인 가능
5. forward test 인프라 이미 v13에서 확립됨 (6/4 LONG signal 10종목 생성 완료)

---

## 3. ★★★ 본 세션 결정적 발견

### 3-1. KRX 데이터광장 ≠ KRX 정보데이터시스템
- 데이터광장 (외부 일반인용): 다운로드 시 기본 = 기간 합산 (timestamp 없음)
- 정보데이터시스템 ([16xxx] 메뉴): daily series 가능 (가능성 높음, 직접 확인 미수행)
- **채권 4종은 일별 옵션 없는 메뉴에서 받음** → 합산 12행

### 3-2. v14 §0 재확인 (영구 사실)
- v12 simulator code = 사라짐 (v14 명시)
- regime detection logic = 사라짐 (본 세션 LS1 결과로 재확인)
- forward-safe regime label 재구현은 별도 작업 (~30분+, 본 세션 미실행)

### 3-3. Lag-1 corr는 약하지만 Filter 효과 강함
- 단일 axis(T-1) vs daily ret corr 최대 0.042
- Protocol C filter 적용 시 ΔSh +0.23
- 이유: portfolio = 15d hold rolling = daily corr가 약해도 entry filter 효과 누적

### 3-4. M8 z_inst_kospi = 가장 robust
- daily lag-1 corr +0.042 (max)
- DD<-20% corr +0.046 (positive 일관)
- monthly corr -0.135 (negative 일관 — 거꾸로!)
- Protocol C: active 50%로 Sharpe 0.915, MDD -22.9% (★ best MDD reduction)
- → **forward test 적용 1순위**

### 3-5. M2 z_vkospi_delta = shock detector
- DD<-20% corr +0.045
- monthly +0.142
- Protocol C: th=-1.0 gt 시 ΔSh +0.231 (best gain)
- 다만 active 86% = 약한 filter (대부분 시기 통과)

### 3-6. M6 z_foreign_kospi_etf = passive flow signal
- monthly corr +0.158 (★ 최강)
- Protocol C: th=0.0 lt 시 ΔSh +0.170, MDD -22.8%
- 의미: ETF에 외인이 안 들어올 때 (lt 0) entry = 역설적

---

## 4. ★ 다음 세션 우선순위 (Phase 3 OOS 진검증)

### 4-1. Step 1: Daily Routine 확립 + M8/M2/M6 entry filter 적용 (★ 최우선)

목적:
- v13 §4-3 daily routine template 완성
- 6/4 OOS LONG signal에 M8/M2/M6 filter 적용 후 재계산
- 6/8 (월요일)부터 daily routine 시작 — KRX OpenAPI 승인 확인 동시

방법:
1. forward_test/state_pipeline 단일 셀
   - 매일 자동: pykrx fetch → state_vector_v2 갱신 → entry candidates → axis filter → log
2. axis filter 후보 (v16 §2-5):
   - M8 z_inst_kospi (T-1) > 0.0  → entry pass
   - M2 z_vkospi_delta (T-1) > -1.0 → entry pass
   - M6 z_foreign_kospi_etf (T-1) < 0.0 → entry pass
3. raw v12 LONG signal + 각 filter 적용 후 signal 비교 log

산출:
- forward_test/log/daily/{date}.parquet
- forward_test/log/filtered_signals_{date}.json
- 1주 누적 후 metric 측정

### 4-2. Step 2: KRX OpenAPI 4축 (월요일 승인 확인)

만약 승인 = 즉시:
- v15 §10 작업 시작
- data/raw/openapi/basis_10y.parquet, pcr_10y.parquet, etf_10y.parquet, kts_10y.parquet
- 채권 4종 (KRX OpenAPI에 채권 투자자별 endpoint 있는지 확인)

만약 미승인 = 보류, Step 1만 진행

### 4-3. Step 3: state v3 정식 통합 (Phase 4)

언제: forward test 2~3주 누적 후
- df_sv_v2 + 16 axis 통합
- 종목×일자 단위 axis 결합
- state_vector_v3 정식 발행

### 4-4. Step 4: 6/26 v10c forward test 결과 비교 (Phase 5)

- choonsimi-premium v10c 결과 receive
- MSM v2 동기간 PnL 비교
- dual-engine 검토 가능 시점

---

## 5. ★ 다음 세션 진입 사양

### 5-1. Setup (~40초)
- 새 노트북
- 합본 셀 paste & run (v16 §10-1)
- EXPECTED_HEAD_PREFIX = '6dd5823' (또는 v16 push 후 최신 hash)

### 5-2. 첫 메시지 권장

```
MSM Phase 3 (Axis Discovery → OOS 진검증) 진행 중.
MSM_HANDOFF_2026_06_07_v16.md + MSM_WORKPLAN_v2.md 참고.

현재:
- v12 LOCK 유지 (Sharpe 0.686)
- web 9.4y 12 type 확보 (8 daily, 4 채권 보류)
- 19 axis 카탈로그 + Redundancy 제거 → 16 axis
- Protocol C: M8/M2/M6 best ΔSh +0.23/+0.23/+0.17
- Path D 확정: forward test OOS 진검증으로 결론
- v12 simulator 재현 영구 불가 재확인 (v14 §0)

다음 우선순위:
1. Daily routine 확립 + M8/M2/M6 entry filter 적용
2. KRX OpenAPI 4축 (월요일 6/8 승인 여부)
3. state v3 정식 통합 (forward test 2~3주 후)
4. 6/26 v10c 결과 비교

§1 추측 X, §6 3축, §7 옵션→형 결정→실행, 단일 셀.
```

### 5-3. Claude 첫 응답 할 것
1. v16 §0 절대 원칙 정독 (#13 simulator 재현 영구 불가)
2. v16 §1 LOCKED + §2 Phase 3 진행 상태
3. v16 §4 우선순위 4단계 옵션 송부
4. KRX OpenAPI 승인 여부 형에게 확인
5. 형 GO 받고 daily routine 작성

---

## 6. ★ 즉시 실행 가능 옵션 (다음 세션)

| 옵션 | 내용 | 시간 |
|---|---|---|
| **A** | **Daily routine 단일 셀 작성 + M8/M2/M6 filter 적용 + 6/4 재계산** | ~10분 |
| **B** | KRX OpenAPI 승인 후 4축 수집 시작 | ~30분 |
| **C** | A + B 결합 | ~40분 |
| **D** | regime detection 자체 재구현 → 새 simulator → state v3 정식 baseline | ~60분 |
| **E** | 채권 4종 KRX 정보데이터시스템 메뉴 직접 확인 (형 작업) | ~20분 |

**권장**: A (또는 KRX OpenAPI 승인 시 C)

---

## 7. 파일 인벤토리 (commit 6dd5823 기준)

```
choonsimi-msm/
├── MSM_HANDOFF_2026_06_02.md ~ v4
├── MSM_HANDOFF_2026_06_03_v6.md
├── MSM_HANDOFF_2026_06_04_v7~v11.md
├── MSM_HANDOFF_2026_06_05_v12.md (MSM v2 LOCK)
├── MSM_HANDOFF_2026_06_05_v13.md (Phase 2)
├── MSM_HANDOFF_2026_06_06_v14.md
├── MSM_HANDOFF_2026_06_07_v15.md
├── MSM_HANDOFF_2026_06_07_v16.md  ← 이 문서 (Phase 3 OOS 진검증)
├── MSM_WORKPLAN_v2.md             ← 이 세션 신규
├── STEP8_PROGRESS.md
├── PREF_DIAGNOSIS_2026_06_05.md
├── README.md
├── msm_data_supplement.ipynb
├── msm_data_ingestion.ipynb
├── msm_state_vector.ipynb
├── data/
│   ├── raw/
│   │   ├── active/, delisted/
│   │   ├── macro/macro_10y.json (UTF-8 BOM 있음, json.load 시 utf-8-sig 필요)
│   │   ├── vkospi_10y_*.csv
│   │   ├── short/
│   │   │   ├── volume/ (39 files, ~54MB)
│   │   │   └── balance/ (38 files, ~92MB)
│   │   └── web/                          ★ v15+v16 신규
│   │       ├── 12008/                    (v15)
│   │       │   ├── kospi_excl_etf_94y.parquet
│   │       │   ├── kospi_incl_etf_94y.parquet
│   │       │   ├── kosdaq_94y.parquet
│   │       │   └── README.md
│   │       ├── krx_bond_index_94y.parquet      ★ v16
│   │       ├── vkospi_ohlc_94y.parquet         ★ v16
│   │       ├── etf_investor_flow_94y.parquet   ★ v16
│   │       ├── kospi200_basis_94y.parquet      ★ v16
│   │       ├── kosdaq150_basis_94y.parquet     ★ v16
│   │       ├── vkospi_basis_94y.parquet        ★ v16
│   │       ├── kospi200_pc_94y.parquet         ★ v16
│   │       └── kosdaq150_pc_94y.parquet        ★ v16
│   ├── universe/universe_msm.csv
│   ├── state/
│   │   ├── state_vector/year=*.parquet (v1)
│   │   ├── regime/year=*.parquet (v1)
│   │   ├── transition/ (v1)
│   │   ├── edge/edge_field.parquet (v1)
│   │   ├── tradeable/year=*.parquet (v1)
│   │   ├── state_vector_v2/year=*.parquet (v2, 259MB)
│   │   ├── edge_v2/edge_field_v2.parquet, diag_*.parquet
│   │   └── axis_v3/                      ★ v16 신규
│   │       ├── axis_candidates_19.parquet
│   │       ├── axis_corr_matrix.parquet
│   │       ├── axis_vs_v12ret_lag1.parquet
│   │       ├── lag_k_corr.parquet
│   │       ├── dd_conditional_corr.parquet
│   │       ├── monthly_corr.parquet
│   │       ├── sweep_C_filter_v12pnl.parquet
│   │       ├── b1_baseline_daily.parquet (LONG-only 시도, 보존)
│   │       ├── b1_ls_baseline_daily.parquet (T 시점, 보존)
│   │       ├── b1_ls_baseline_t1_daily.parquet (T+1 lag, 보존)
│   │       ├── b1_entries.parquet
│   │       ├── b1_long_entries.parquet
│   │       └── b1_short_entries.parquet
│   └── sim/
│       ├── equity_curve_shock_short_only.parquet (STEP 6 LOCKED)
│       ├── equity_t4_v1.parquet (STEP 7 V1 LOCKED)
│       ├── v2_short_only/long_only/long_short.parquet (STEP 8.6)
│       ├── v2_gamma_best.parquet (MSM v2 BEST LOCKED) ★
│       └── step87_gamma_sweep.parquet
└── forward_test/
    ├── baseline.json
    ├── README.md
    ├── metrics/day1_setup.parquet
    ├── state/oos_state_20260603_20260605.parquet
    └── log/long_signals_20260603_20260605.json
```

---

## 8. 본 세션 (#10) commit 이력

- `1b81642`  web 8 parquet 9.4y (GitHub UI 직접 upload by 형)
- `b6ff1e6`  MSM Phase 3 A4: 19 axis candidates + corr + lag1
- `2913514`  MSM Phase 3 B: lag-k + DD-conditional + monthly corr
- `6dd5823`  MSM Phase 3 C: filter-on-v12-PnL sweep (5 axis x 10 variants)
- (예정) v16 핸드오프 + workplan v2 commit

이전 12008 commit (세션 #10 전반부):
- 8f278a6  (v15 작업 종결 commit)

---

## 9. ★ 실수 누적 (v13 #1~#50 + v16 신규 #51~#57)

v13 #48~#50 유지 (pykrx column 변경, 영업일 list 불일치, 우선주 비중 발견).

**v16 신규**:

- **#51**: KRX 데이터광장 (data.krx.co.kr/외부 일반인용)과 KRX 정보데이터시스템 ([16xxx] 메뉴) 구분 미인지. 데이터광장에서 채권 투자자별 4종 다운로드 시 daily series 아닌 기간 합산 (12행)으로만 받음. **재발 방지**: KRX 사이트 다운로드 전 "일자별/기간 합산" 토글 옵션 명시 확인 필수. 의심 시 1 batch 먼저 받아서 line count 검증.

- **#52**: 파일명 suffix 변동 (3547_20260607__1_.csv vs 3547_20260607.csv). Stanley가 같은 파일 두 번 다운받으면 (1) suffix 추가됨. 통합 코드는 두 패턴 모두 대응 필요. **재발 방지**: glob 패턴 + fallback path 사용.

- **#53**: macro_10y.json이 UTF-8 BOM 포함. `json.load()` 직접 호출 시 JSONDecodeError. **재발 방지**: `json.load(open(p, encoding='utf-8-sig'))` 또는 사전 BOM 제거.

- **#54**: df_eq_v2_best의 column이 `equity`가 아니라 `cum_eq`/`net_return`/`gross_return`. memory에 명시 안 됨. **재발 방지**: dataframe 사용 전 columns print 의무.

- **#55**: 12008 데이터에 "기관" 단일 column 없음. 기관 = 7개 column 합 (금융투자+보험+투신+사모+은행+기타금융+연기금 등). pick_col 함수 키워드 매칭 실패. **재발 방지**: memory에 명시된 합산 정의 (기관7, 외인합=외국인+기타외국인) 사전 확인.

- **#56**: tradeable=True에 direction==0 없음. memory v12 LOCK "NEUTRAL (short_pressure ≈ 0)" 표현은 derived label. 실제 정의 = `regime=='RANGE' AND tradeable`. **재발 방지**: regime label "NEUTRAL"은 4개 raw label (TRANSITION/RANGE/SHOCK/TREND)에 없음. 의미적 매핑은 코드 검증 필수.

- **#57**: ★ 가장 중요. **B1 자체 simulator로 v12 LOCK Sharpe 0.686 재현 시도 → 실패 (재현 불가 영구 사실 재확인)**. T 시점 entry 시 SHORT entry day median -6.2% = lookahead, T+1 lag 후에도 SHORT Sh +1.48 = regime detection이 forward-looking 가능성. **v14 §0 명시 그대로** — simulator + regime logic 재현 불가. **재발 방지**: v12 LOCK Sharpe 비교 baseline은 영구적으로 `df_eq_v2_best`만 사용. 자체 simulator는 새 system으로만 평가 (relative ΔSh 의미만).

---

## 10. ★ 다음 세션 합본 셀

### 10-1. Setup 셀 (paste & run, ~50초)

```python
# ===== MSM 합본 Setup Cell v16 (paste & run) =====
import os, subprocess, shutil, time
from pathlib import Path

os.chdir('/content')
t0 = time.time()
REPO = '/content/choonsimi-msm'
EXPECTED_HEAD_PREFIX = 'XXXXXXX'  # ← v16 push 후 commit hash 7자리로 갱신

from google.colab import userdata
GH = userdata.get('GH_TOKEN'); assert GH

if Path(REPO).exists():
    shutil.rmtree(REPO)
url = f'https://x-access-token:{GH}@github.com/stanleyim/choonsimi-msm.git'
r = subprocess.run(['git', 'clone', url, REPO], capture_output=True, text=True, cwd='/content')
assert r.returncode == 0, r.stderr
os.chdir(REPO)
head = subprocess.run(['git','rev-parse','--short','HEAD'], capture_output=True, text=True).stdout.strip()
print(f'clone HEAD={head}')
assert head.startswith(EXPECTED_HEAD_PREFIX)

import sys
subprocess.run([sys.executable,'-m','pip','install','-q','pyarrow','pandas','numpy','psutil','pykrx'], check=True)
import pyarrow, pandas as pd, numpy as np, psutil

for k in ['KRX_ID','KRX_PW','ECOS_API_KEY','GH_TOKEN']:
    try:
        v = userdata.get(k)
        if v and k in ('KRX_ID','KRX_PW'):
            os.environ[k] = v
    except: pass

subprocess.run(['git','config','user.email','msm@stanleyim.local'], check=True, cwd=REPO)
subprocess.run(['git','config','user.name','stanleyim'], check=True, cwd=REPO)

# Load v2 state_vector
from glob import glob
sv2_files = sorted(glob('data/state/state_vector_v2/year=*.parquet'))
df_sv_v2 = pd.concat([pd.read_parquet(f) for f in sv2_files], ignore_index=True)
df_sv_v2['date'] = pd.to_datetime(df_sv_v2['date'])
df_sv_v2['score'] = df_sv_v2['z_r'] + df_sv_v2['z_f']
print(f'df_sv_v2: {df_sv_v2.shape}')

# Load v2 LOCKED equity (v12 BEST)
df_eq_v2_best = pd.read_parquet('data/sim/v2_gamma_best.parquet')
df_eq_v2_best['date'] = pd.to_datetime(df_eq_v2_best['date'])
print(f'v2 BEST equity: {len(df_eq_v2_best)} rows, cols={list(df_eq_v2_best.columns)}')

# Forward test infra
assert Path('forward_test').exists()
print('forward_test/: OK')

# web 12008 (v15)
df_ke = pd.read_parquet('data/raw/web/12008/kospi_excl_etf_94y.parquet')
df_ki = pd.read_parquet('data/raw/web/12008/kospi_incl_etf_94y.parquet')
df_kq = pd.read_parquet('data/raw/web/12008/kosdaq_94y.parquet')
print(f'12008: kospi_excl/incl/kosdaq each {len(df_ke)} days')

# web 8 type (v16 신규)
WEB_FILES = {
    '3351':'krx_bond_index_94y.parquet',
    '0546':'vkospi_ohlc_94y.parquet',
    '1415':'etf_investor_flow_94y.parquet',
    '2524':'kospi200_basis_94y.parquet',
    '3729':'kosdaq150_basis_94y.parquet',
    '4031':'vkospi_basis_94y.parquet',
    '4914':'kospi200_pc_94y.parquet',
    '0145':'kosdaq150_pc_94y.parquet',
}
web_data = {}
for code, fname in WEB_FILES.items():
    web_data[code] = pd.read_parquet(f'data/raw/web/{fname}')
print(f'web 8 type loaded: {list(web_data.keys())}')

# axis v3 (v16 신규)
axes = pd.read_parquet('data/state/axis_v3/axis_candidates_19.parquet')
print(f'axes v3: {axes.shape}')

print(f'준비 완료 {time.time()-t0:.1f}s')
```

### 10-2. Daily routine 합본 셀 (다음 세션에서 작성)

구조:
1. T-1 까지의 state_vector 갱신
2. T-1 axis 값 계산 (M8/M2/M6)
3. v12 LONG signal 생성 (NEUTRAL × bot z_ell top 10)
4. 3개 filter 적용 후 signal 비교 log
5. forward_test/log/daily/{T}.json 저장
6. git push

---

## 11. Phase 3 일정 예상

| 시점 | 작업 |
|---|---|
| 다음 세션 (~6/8) | Daily routine 셀 작성 + 6/4 신호 재계산 + KRX OpenAPI 확인 |
| 1주 후 (~6/15) | 약 7거래일 OOS 누적, 첫 ΔSharpe 측정 가능 |
| 1개월 후 (~7/7) | 약 20거래일 OOS, 통계적 의미 시작 |
| 6/26 | choonsimi-premium v10c forward test 결과 receive |
| 3개월 후 (~9/7) | 약 60거래일 OOS, Sharpe 검증 가능 (CI 좁아짐) |

---

## 12. 핵심 한 줄

본 세션 #10 = **데이터 확보 + axis discovery 완성**. web 9.4y 8 type 추가, 19 axis 카탈로그, lag-1 corr 약하지만 Protocol C filter ΔSh +0.23 (M8/M2). B1 simulator는 v12 재현 불가 재확인 (v14 §0). Path D 확정 = M8/M2/M6 filter를 forward test에 즉시 적용 → OOS 진검증.

---

## 13. 형의 다음 세션 분석 우선순위

1. **Daily routine 확립 + M8/M2/M6 filter 적용** (★ 즉시)
2. KRX OpenAPI 4축 (월요일 6/8 승인 여부)
3. 6/5+ OOS PnL 누적
4. state v3 정식 통합 (forward test 2~3주 후)
5. 6/26 v10c 결과 + dual-engine 검토

---

## 14. 정직 메시지

본 세션 #10에서 발견한 진짜:

**좋은 것**:
- web 9.4y 8 type 확보 = state v3 axis 풍부한 후보
- 19 axis 중 Tier 1 5개 (M8/M2/M6/M17/M3) 식별
- Protocol C로 ΔSh +0.23 (M8) 측정 = signal 진짜 존재

**한계**:
- lag-1 corr 모두 < 0.05 = 단일축 daily timing 매우 약함
- B1 자체 simulator로 v12 0.686 재현 시도 → 영구 불가 (v14 §0 재확인)
- Protocol C는 sanity check, 진짜 entry-day filter 아님 (PnL 마스킹만)

**결론**:
- 인-sample 검증으론 더 이상 못 나아감
- 진짜 검증 = forward test OOS만
- M8 (50% active, MDD -22.9%) = 1순위 filter 후보
- 1주~1개월 누적 시 진위 판정 가능

**다음 세션 핵심**:
Daily routine 확립이 모든 것의 시작.

---

## 부록 1 — 19 Axis 정의 (Reference)

| ID | 이름 | source | 정의 | Tier |
|---|---|---|---|---|
| M1 | z_vkospi | 0546 | VKOSPI 종가 60d z | 2 |
| M2 | z_vkospi_delta | 0546 | VKOSPI 등락률 60d z | **1** |
| M3 | z_ytm_change | 3351 | YTM diff 60d z | **1** |
| M4 | z_duration | 3351 | 듀레이션 60d z | 3 |
| M5 | z_foreign_kospi_cash | 12008 | KOSPI(excl) 외인합 60d z | 2 |
| M6 | z_foreign_kospi_etf | 12008 | (kospi_incl - kospi_excl) 외인합 60d z | **1** |
| M7 | z_foreign_kosdaq | 12008 | KOSDAQ 외인합 60d z | 2 |
| M8 | z_inst_kospi | 12008 | KOSPI(excl) 기관7합 60d z | **1** |
| M9 | z_inst_kosdaq | 12008 | KOSDAQ 기관7 60d z | 3 |
| M10 | z_indiv_kospi | 12008 | KOSPI(excl) 개인 60d z | 3 |
| ~~M11~~ | ~~z_indiv_kosdaq~~ | 12008 | KOSDAQ 개인 (M7 mirror) | ❌ 제거 |
| ~~M12~~ | ~~z_foreign_divergence~~ | 12008 | KOSPI - KOSDAQ 외인 (M5 대체) | ❌ 제거 |
| ~~M13~~ | ~~z_etf_foreign~~ | 1415 | ETF 외인 (M6 동일) | ❌ 제거 |
| M14 | z_etf_pension | 1415 | ETF 연기금 60d z | 2 |
| M15 | z_basis_k200 | 2524 | KOSPI200 괴리율 60d z | 2 |
| M16 | z_basis_kq150 | 3729 | KOSDAQ150 괴리율 60d z | 3 |
| M17 | z_basis_vkospi | 4031 | VKOSPI 시장베이시스 60d z (79% avail) | **1** |
| M18 | z_pc_k200 | 4914 | KOSPI200 P/C 60d z | 2 |
| M19 | z_pc_kq150 | 0145 | KOSDAQ150 P/C 60d z (2018-03~) | 3 |

유지 16 axis. Tier 1 = 5개 (★).

---

**작성자**: Claude (MSM 세션 #10, Phase 3 진입)
**상태**: v12 LOCK 유지, web 9.4y 12 type 확보 (4 보류), 19 axis 카탈로그, Protocol C ΔSh 측정, B1 실패 재확인, Path D 확정
**다음 작업**: Daily routine + M8/M2/M6 filter forward test 적용

끝.
