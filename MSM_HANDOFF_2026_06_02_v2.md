# MSM 핸드오프 v2 — 정정본

**작성일**: 2026-06-02
**대상 repo**: `stanleyim/choonsimi-msm`
**정정 사유**: v1 핸드오프 문서 §5에서 premium repo 참조 가정 잘못 적음. MSM은 단독 시스템.

---

## 0. 절대 원칙 (v1과 동일)

1. **§1 추측 금지** — 모르는 건 검증, 적당히 가정 X
2. **§7 옵션 → 형 결정 → 실행**
3. **§13 데이터 백업** — 매 단계 commit/push
4. **MSM은 choonsimi-premium과 완전 독립** — 참조·의존 X
5. **외부 검토자 3 원칙** — v10c는 6/26까지 freeze

---

## 1. MSM 시스템 정의 (확정)

**MSM = choonsimi-premium과 별개 독립 시스템**
- 데이터 공유 X
- 코드 공유 X
- 운영 영향 0

**MSM v1 목표:** 시장 state space에서 tradeable region 추출
- STEP 1: Data cleaning (survivorship 포함)
- STEP 2: State Vector Construction ← **Notebook 2 작업 대상**
- STEP 3: Regime detection
- STEP 4: Transition modeling
- STEP 5: Edge field estimation
- STEP 6: Edge region extraction
- STEP 7: Signal generation

---

## 2. 현재 보유 데이터 (정확한 인벤토리)

```
choonsimi-msm/
├── MSM_HANDOFF_2026_06_02.md       # v1 (premium 참조 가정 — 무효 부분 있음)
├── README.md
├── msm_data_supplement.ipynb       # Notebook 1
└── data/
    ├── raw/
    │   ├── vkospi_10y.parquet      # 2,307행, 2017-01-02 ~ 2026-06-02
    │   ├── vkospi_10y_merged.csv   # 원본 백업
    │   └── delisted/
    │       ├── ohlcv/year={2017..2026}.parquet  # 289종목, 313,116행 (adjusted)
    │       └── flow/year={2017..2026}.parquet   # 285종목, 247,395+2,060행
    └── checks/
        ├── delisted_codes.json      # 291 후보
        ├── delisted_excluded.json   # 6 제외 (104110,104120,037620,068870,068875,139200)
        └── delisted_validation.json # 무결성 리포트
```

**최종 commit**: `29d86e8`

---

## 3. 부족한 데이터 (Notebook 2 시작 전 결정 필요)

MSM = 단독이므로 premium에서 안 가져옴. 따라서:

| 데이터 | 보유 | 부족 |
|---|---|---|
| Active 종목 OHLCV (현재 거래 종목) | ❌ | 신규 수집 필요 |
| Active 종목 Flow | ❌ | 신규 수집 필요 |
| Active 종목 외국인 지분율 | ❌ | 신규 수집 필요 |
| Universe 정의 | ❌ | 6축 필터 또는 다른 방식 |
| KOSPI200 지수 | ❌ | 신규 수집 (regime 판정용) |
| 매크로 (SOX/VIX/USDKRW 등) | ❌ | 표시용 (필수 X) |
| 상폐 종목 (survivorship) | ✓ 285종목 | — |
| VKOSPI | ✓ 10년 | — |

---

## 4. Notebook 2 진행 전 결정 사항 (형 답변 필요)

### Q1. Active 종목 universe 정의
- **A)** KRX 전체 (KOSPI+KOSDAQ) → 6축 필터로 200~300종목 선정 (premium 방식 차용)
- **B)** 시점별 dynamic universe (매년 재선정, survivorship 더 강하게 제거)
- **C)** 다른 방식

### Q2. Active 종목 수집 범위
- **A)** OHLCV(adjusted+raw) + Flow + Foreign 지분율 — premium과 동일 데이터셋
- **B)** OHLCV + Flow만 (foreign 지분율 생략)
- **C)** 다른 조합

### Q3. KOSPI200 지수 필요 여부
- **A)** 수집 (regime detection에 사용)
- **B)** 생략 (state vector만으로 regime 판정)

### Q4. State Vector 5축 수식 — 형 동의?
```
r = log(close_t / close_{t-1})
v = log(trade_value_t / 60d_mean)
f = (foreign_5d + inst_5d) / trade_value_5d
σ = std(r) over 20d
ℓ = log10(trade_value_60d / 100억)
```
- **A)** 그대로
- **B)** 수정 (어떻게?)

### Q5. Normalization
- **A)** Cross-sectional z-score (시점별, 종목 간)
- **B)** Time-series z-score (종목별, 시간 축)
- **C)** 둘 다 계산해서 비교

### Q6. 작업 순서
- **A)** Notebook 2 = active 수집 + state vector 통합 (큰 노트북)
- **B)** Notebook 2 = active 수집만, Notebook 3 = state vector (분리)

---

## 5. 권장 작업 흐름 (참고용, 형이 Q1~Q6 답하면 확정)

가정: Q1=A, Q2=A, Q3=A, Q4=A, Q5=A, Q6=B

**Notebook 2: Active Universe + 데이터 수집** (1~2시간)
```
Step A: Universe 선정 (KRX 6축 필터)
Step B: Active OHLCV adjusted 수집
Step C: Active OHLCV raw + 시총 수집
Step D: Active Flow 수집
Step E: Active Foreign 지분율 수집
Step F: KOSPI200 지수 수집
Step G: 검증 + commit/push
```

**Notebook 3: State Vector Build** (30분~1시간)
```
Step A: 데이터 통합 (active + delisted = 약 500~570종목)
Step B: 5축 계산 (r, v, f, σ, ℓ)
Step C: Normalization
Step D: state_vector.parquet 저장
Step E: 검증 + commit/push
```

---

## 6. §8 실수 목록 (Notebook 1 누적 + v1 추가)

1. Colab 환경 망각
2. 보유 자산 확인 안 하고 신규 수집 제안
3. 사용자 파일 전달·실행 경로 합의 없이 진행
4. pykrx 내부 모듈 경로 추측 (`pykrx.website.krx.core` 존재 X)
5. 셀 단위 가이드 — 환경 확인 안 하고 "다음 셀 실행" 반복
6. 출력 예시 텍스트와 실행 코드 구분 안 함
7. Exception 잡았는데 라이브러리 내부 stderr만 출력 → fail counter 신뢰 X
8. 컨테이너 산출물 = 휘발성. 매 단계 commit 필수
9. **(v1 추가) Notebook 2 설계 시 premium repo 참조 가정 — 형과 합의 없이 핸드오프 문서에 명시. MSM 단독 정책 위배.**

---

## 7. §9 DATA_COLLECTION_MANUAL 수정 사항

### 7-1. §5.1 단위 정정
- 거래량 (volume): **주**
- 거래대금 (trade_value): **원**
- 기관/외국인/개인/기타 net: **원** (매뉴얼 "수량" 오기)
- pykrx `get_market_trading_value_by_date` = 금액

### 7-2. §9.10 pykrx 인증 자동 갱신
- 만료 1시간
- pykrx 호출 도중 자동 재로그인 ("KRX 세션 만료, 재로그인 시도... 갱신 완료")
- 환경변수만 살아있으면 개입 불필요
- 런타임 재시작 후엔 환경변수 재set 필요 (모듈 reload X)

---

## 8. 새 세션 시작 가이드

### 첫 메시지 권장
```
MSM Notebook 2 시작.
MSM_HANDOFF_2026_06_02_v2.md 참고.

이전 세션 종료 상태:
- choonsimi-msm repo에 VKOSPI 10y + 상폐 285종목 push 완료
- MSM 단독 시스템 확정 (premium 참조 X)

진행 전 §4 Q1~Q6 결정 필요. 형이 답할 차례.
```

### Claude가 첫 응답에서 할 것
1. 핸드오프 v2 로드 확인
2. **§1 추측 금지** — Q1~Q6 확정 전 코드 작성 X
3. 형 답 받은 후 Notebook 2 설계
4. 메모리 한도 확인 (active 수집은 큰 작업)

---

**작성자**: Claude (MSM Notebook 1 어시스턴트)
**상태**: Notebook 1 완료, Notebook 2 진행 전 결정 대기
**다음 작업**: §4 Q1~Q6 형 답 → Notebook 2 설계 → 실행

끝.
