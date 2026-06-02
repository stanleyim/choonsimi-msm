# MSM 핸드오프 — Notebook 1 종료 → Notebook 2 시작

**작성일**: 2026-06-02
**대상 repo**: `stanleyim/choonsimi-msm`
**작성 사유**: Notebook 1 완료, Notebook 2 (state vector build) 시작 위한 인계

---

## 1. 현재 repo 상태

```
choonsimi-msm/
├── README.md
├── msm_data_supplement.ipynb       # Notebook 1 (완료)
└── data/
    ├── raw/
    │   ├── vkospi_10y.parquet      # 2,307행 (2017-01-02 ~ 2026-06-02)
    │   ├── vkospi_10y_merged.csv   # 원본 (백업)
    │   └── delisted/
    │       ├── ohlcv/year={2017..2026}.parquet  # 289종목, 313,116행
    │       └── flow/year={2017..2026}.parquet   # 285종목, 247,395+2,060행
    ├── macro/         # (Notebook 2에서 채움)
    ├── universe/      # (Notebook 2에서 채움)
    ├── state/         # (Notebook 2 산출)
    └── checks/
        ├── delisted_codes.json      # 291개 후보
        ├── delisted_excluded.json   # 6개 제외 사유
        └── delisted_validation.json # 무결성 리포트
```

**최종 commit**: `f82dfb8` — "Finalize delisted: 029960 flow recovered, 6 excluded. Final 285 valid codes."

---

## 2. Notebook 1 결과 요약

| 항목 | 결과 |
|---|---|
| VKOSPI 10년 (수동 KRX) | 2,307행, 종가 9.72~80.37 ✓ |
| 상폐 종목 OHLCV | 289/291 (유효 285) |
| 상폐 종목 Flow | 285/291 (029960 재시도 성공) |
| 제외 | 6개 (단기 거래 또는 데이터 0행) |

**제외 종목** (`data/checks/delisted_excluded.json`):
- 104110, 104120: OHLCV 0행
- 037620, 068870, 068875, 139200: 11~14일만 거래 (lookback 60일 미달)

---

## 3. §8 실수 목록 (오늘 발견, 반복 금지)

1. Colab 환경 망각 (sandbox 제약 가정)
2. 보유 자산 확인 안 하고 신규 수집 제안
3. 사용자 파일 전달·실행 경로 합의 없이 진행
4. pykrx 내부 모듈 경로 추측 (`pykrx.website.krx.core` 존재 X)
5. 셀 단위 가이드 — 환경 확인 안 하고 "다음 셀 실행" 반복
6. 출력 예시 텍스트와 실행 코드 구분 안 함 (`→ 상폐 후보` SyntaxError)
7. Exception 잡았는데 라이브러리 내부 stderr만 출력 → fail counter 신뢰 불가
8. 컨테이너 산출물 = 휘발성. 매 단계 commit 필수 (이전 세션 교훈)

---

## 4. §9 DATA_COLLECTION_MANUAL 수정 사항 (반영 필요)

### 4-1. §5.1 단위 정정
**오기:** `foreign_net`, `inst_net` 단위 "수량(주)"
**실측:** **원(KRW)**. pykrx `get_market_trading_value_by_date` = 금액

| 컬럼명 (한글) | 의미 | 단위 |
|---|---|---|
| 거래량 | volume | 주 |
| 거래대금 | trade_value | 원 |
| 기관합계 | inst_net | 원 |
| 외국인합계 | foreign_net | 원 |
| 개인 | indiv_net | 원 |
| 기타법인 | etc_net | 원 |
| 전체 | total (제로섬 검산) | 원 (≈0) |

→ MSM flow imbalance 계산 시 raw_close 곱하기 불필요. 금액 그대로 사용.

### 4-2. §9 새 발견 추가
**§9.10 pykrx 인증 자동 갱신**
- KRX 인증 1시간 만료 (`로그인 시간` + 1h)
- pykrx가 호출 도중 만료 감지 시 **자동 재로그인** 수행
- Batch 5에서 검증됨: `KRX 세션 만료, 재로그인 시도... KRX 세션 갱신 완료`
- → 장시간 작업에서 인증 만료 걱정 불필요 (환경변수만 set되어 있으면)

---

## 5. Notebook 2 설계서 (State Vector Build)

### 목적
MSM v1 STEP 2: **State Vector Construction**
- 보유 데이터 (premium repo) + 신규 데이터 (msm repo) 통합
- 5축 state vector 계산
- normalization → `data/state/state_vector.parquet`

### State Vector 정의

```
S_t = [r, v, f, σ, ℓ]
```

| 축 | 정의 | 원천 데이터 | 단위 |
|---|---|---|---|
| **r (return)** | log(close_t / close_{t-1}) | OHLCV adjusted | unitless |
| **v (volume)** | log(trade_value_t / 60d_mean) | OHLCV raw | unitless (log ratio) |
| **f (flow imbalance)** | (foreign_5d + inst_5d) / trade_value_5d | Flow | unitless (ratio) |
| **σ (volatility)** | std(r) over 20d | OHLCV adjusted | unitless |
| **ℓ (liquidity)** | log10(trade_value_60d / 100억) | OHLCV raw | unitless (log scale) |

### Normalization
- **Cross-sectional z-score** (시점별, 종목 간 정규화)
- 매일: `z = (x - cross_section_mean) / cross_section_std`
- → state는 종목 간 상대값. regime detection에 적합.

### 입력 데이터 통합

**보유 (premium repo, 별도 clone 필요):**
- `data/ohlcv_adj/year=YYYY.parquet` (adjusted, 262종목)
- `data/ohlcv/year=YYYY.parquet` (raw + trade_value)
- `data/flow/year=YYYY.parquet`
- `data/foreign/year=YYYY.parquet` (외국인 지분율)
- `data/macro.json` (KOSPI200, etc — VKOSPI는 msm 신규 사용)

**신규 (msm repo, 본 노트북):**
- `data/raw/vkospi_10y.parquet`
- `data/raw/delisted/ohlcv/`
- `data/raw/delisted/flow/`

**Universe 통합:**
- premium 262 (active) + 신규 285 (delisted) = **547종목**
- → survivorship bias 제거

### Notebook 2 셀 구조 (예정)

```
[Setup]
  - repo clone (msm + premium 별도)
  - cwd /content/choonsimi-msm
  - import + 디렉토리 확인

[Step A] 데이터 통합
  - premium OHLCV adj 로드 (262종목)
  - premium OHLCV raw 로드
  - premium Flow 로드
  - msm delisted OHLCV 로드 (285종목)
  - msm delisted Flow 로드
  - merge → 547종목 통합 DataFrame
  - 무결성 검증 (날짜 범위, 종목수, dedup)

[Step B] State Vector 5축 계산
  - r = log return
  - v = log(turnover / 60d_mean)
  - f = (foreign_5d + inst_5d) / trade_value_5d
  - σ = 20d volatility
  - ℓ = log10(turnover_60d / 100억)

[Step C] Cross-sectional normalization
  - 매일별 z-score
  - NaN 처리 (상장 전, lookback 부족)

[Step D] 저장 + 검증
  - data/state/state_vector.parquet
  - 검증 리포트: NaN 비율, 분포 통계
  - data/checks/state_vector_validation.json

[Step E] Commit + Push
```

### 예상 산출물

`data/state/state_vector.parquet`:
```
date, code, r, v, f, sigma, ell,    z_r, z_v, z_f, z_sigma, z_ell
```

### 다음 단계 (Notebook 3 이후, MSM STEP 3+)
- STEP 3: Regime detection (trend/range/shock/transition)
- STEP 4: State space modeling (P(S_{t+1} | S_t))
- STEP 5: Edge field estimation
- STEP 6: Edge region extraction
- STEP 7: Trade signal generation

---

## 6. 새 세션 시작 가이드

### 첫 메시지 권장
```
MSM Notebook 2 (state vector build) 시작.
이 핸드오프 문서 참고.

현재 상태:
- choonsimi-msm repo 데이터 다 push됨
- VKOSPI 10y + 상폐 285종목 OHLCV/Flow 완료
- 다음: premium repo 데이터와 통합, state vector 계산

진행 방향 상의 부탁.
```

### Claude가 첫 응답에서 확인할 것
1. `MSM_HANDOFF_2026_06_02.md` 보유 (이 문서)
2. premium repo clone 방법 — Public인지 Private인지 확인 (이전 세션에서 Public 확인됨)
3. 메모리 한도 (Notebook 2는 큰 작업 — 여유 필요)

---

## 7. 핵심 원칙 (잊지 마)

1. **§1 추측 금지** — 모르는 건 검증
2. **§3 데이터 백업** — 매 단계 commit/push
3. **§7 옵션 → 형 결정 → 실행**
4. **컨테이너 휘발성** — Colab 끊겨도 GitHub에 살아있어야
5. **외부 검토자 3 원칙** — "안 바꾸는 능력" (v10c는 6/26까지 freeze)

---

**작성자**: Claude (MSM Notebook 1 작업 어시스턴트)
**작성 시각**: 2026-06-02 08:1X KST
**다음 작업 시점**: 형 결정 — 휴식 후 새 세션 / 즉시 이어서

끝.
