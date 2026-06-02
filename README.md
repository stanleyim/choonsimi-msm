# choonsimi-msm

**Market Structure Model v1** — 시장 데이터를 state space로 변환하고, regime을 분리하고, transition을 추정하고, 기대수익이 양(+)인 tradeable region만 추출하는 시스템.

> `choonsimi-premium`(v10c)과 **완전 독립** repo. 데이터·코드 공유 없음.

---

## 1. 목적

```
시장 데이터  →  state vector  →  regime 분류  →  transition 추정  →  edge field  →  tradeable region
```

오직 **돈이 되는 상태 영역을 구조적으로 추출**하는 것이 유일한 목표.

---

## 2. MSM 5 STEP

| STEP | 내용 | 산출물 |
|---|---|---|
| 1 | State Vector 생성 `S_t = (r, v, f, σ, ℓ)` | `data/state/state_vector.parquet` |
| 2 | Regime 분류 (trend / range / shock / transition) | `data/regime/` |
| 3 | Transition 추정 `P(S_{t+1} \| S_t)` | `data/transition/` |
| 4 | Edge Field 계산 (expected return surface) | `data/edge/` |
| 5 | Tradeable Region 추출 (positive EV) | `data/tradeable/` |

---

## 3. State Vector 정의

```
S_t = [r, v, f, σ, ℓ]

r  = log(close_t / close_{t-1})                  # adjusted close
v  = log(trade_value_t / 60d_mean)                # raw trade_value
f  = (foreign_5d + inst_5d) / trade_value_5d      # flow imbalance (원)
σ  = std(r) over 20d                              # 20d realized vol
ℓ  = log10(trade_value_60d / 100억)               # liquidity (log scale)
```

**Dual normalization** (Notebook 3에서 적용):
- Cross-sectional z-score: `r_cs, v_cs, f_cs, sigma_cs, ell_cs`
- Time-series z-score: `r_ts, v_ts, f_ts, sigma_ts, ell_ts`

---

## 4. Universe

**6축 필터** 적용 (KOSPI + KOSDAQ 전체 기준):

| 축 | 컷오프 |
|---|---|
| 시가총액 | ≥ 1,000억 원 |
| 일평균 거래대금 (60d) | ≥ 3억 원 |
| 상장기간 | ≥ 120 영업일 |
| 관리/거래정지 FLAG | 제외 |
| 시장 | KOSPI + KOSDAQ |
| 종류 | ETF · ETN 제외 |

**현재**: 1,318종목 (596 KOSPI + 722 KOSDAQ)
→ `data/universe/universe_msm.csv`

**Delisted (생존편향 제거용)**: 285종목 추가 보유 (2017~2026).

---

## 5. 데이터 출처

| 항목 | 소스 |
|---|---|
| OHLCV (adj + raw) | pykrx (KRX) |
| Flow (외국인/기관/개인/기타, 원 단위) | pykrx |
| Foreign 지분율 | pykrx |
| KOSPI / KOSPI200 / KOSDAQ / KOSDAQ150 | pykrx (1001 / 1028 / 2001 / 2203) |
| VKOSPI | pykrx (1330, `name_display=False`) + KRX 수동 보강 |
| USD/KRW | FinanceDataReader |
| 한국 기준금리 | BOK ECOS (722Y001) |

**기간**: 2017-01-02 ~ 현재 (10년).

---

## 6. 디렉토리 구조

```
choonsimi-msm/
├── README.md
├── MSM_HANDOFF_2026_06_02_v3.md      # 최신 인계서 (작업 재개 시 정독)
├── msm_data_supplement.ipynb         # Notebook 1: VKOSPI + delisted (완료)
├── msm_data_ingestion.ipynb          # Notebook 2: active universe 수집 (실행 대기)
├── msm_state_vector.ipynb            # Notebook 3: state vector 빌드
└── data/
    ├── raw/
    │   ├── vkospi_10y.parquet
    │   ├── delisted/
    │   │   ├── ohlcv/year=YYYY.parquet
    │   │   └── flow/year=YYYY.parquet
    │   ├── active/                   # Notebook 2 산출
    │   │   ├── ohlcv_adj/
    │   │   ├── ohlcv/
    │   │   ├── flow/
    │   │   └── foreign/
    │   └── macro/                    # Notebook 2 Step F
    ├── universe/
    │   └── universe_msm.csv          # 1,318종목
    ├── state/                        # Notebook 3 산출
    └── checks/                       # 무결성 리포트
```

---

## 7. 진행 상태

| Notebook | 상태 |
|---|---|
| 1. Data Supplement (VKOSPI + delisted) | ✓ 완료 |
| Universe 선정 (1,318종목) | ✓ 완료 |
| 2. Data Ingestion (active OHLCV/Flow/Foreign/Macro) | 골격 push, 본실행 대기 |
| 3. State Vector Build | 골격만 |
| 4. Regime Detection | 미착수 |
| 5. Transition Modeling | 미착수 |
| 6. Edge Field | 미착수 |
| 7. Tradeable Region | 미착수 |

---

## 8. 실행 환경

- **플랫폼**: Google Colab
- **인증**: Colab Secrets에 `KRX_ID`, `KRX_PW`, `ECOS_API_KEY`, `GH_TOKEN` 등록 필수
- **패키지**: `pykrx`, `pyarrow`, `finance-datareader`, `requests`
- **KRX 세션**: 1시간 자동 만료 → pykrx 자동 재로그인 지원 (환경변수만 살아있으면 OK)

---

## 9. 절대 원칙

1. **추측 금지** — 모르는 건 검증. 가정 X.
2. **3번 정밀 검토** — 모든 응답 전.
3. **옵션 → 형 결정 → 실행** — 임의 진행 X.
4. **매 단계 commit/push** — Colab 컨테이너는 휘발성.
5. **premium repo와 독립** — 데이터/코드 공유 X.
6. **목적 외 확장 금지** — state → regime → transition → edge → tradeable 외 전부 샛길.

---

## 10. 다음 작업

**Notebook 2 Step B** (Active OHLCV adjusted 수집, 약 50분) → 분할 실행 (B → F → C → D → E).
세부 절차는 `MSM_HANDOFF_2026_06_02_v3.md` §6 참조.

---

**Repo**: `stanleyim/choonsimi-msm`
**Owner**: stanleyim
**Status**: 데이터 수집 50% — active universe 본수집 대기
