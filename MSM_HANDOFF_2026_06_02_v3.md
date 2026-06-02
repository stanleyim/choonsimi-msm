# MSM 핸드오프 v3 — 정밀 인계서

**작성일**: 2026-06-02 (세션 종료 시점)
**대상 repo**: `stanleyim/choonsimi-msm`
**상태**: Notebook 1 데이터 완료 + Active Universe 선정 완료. Notebook 2 데이터 수집 대기.

---

## 0. 절대 원칙 (이전 세션 누적)

1. **§1 추측 금지** — 모르는 건 검증. 적당히 가정 X.
2. **§6 모든 응답 전 3번 정밀 검토** — 형 명령. 한 번 검토는 위반.
3. **§7 옵션 → 형 결정 → 실행** — 질문 삼가. 옵션 명시 후 형 답 받고 진행.
4. **§13 데이터 백업** — 매 단계 commit/push. 컨테이너는 휘발성.
5. **MSM = choonsimi-premium과 완전 독립** — 데이터/코드 공유 X.
6. **외부 검토자 3 원칙** — v10c 6/26까지 freeze.

---

## 1. 현재 repo 상태 (commit history)

```
a52bfd5 ← HEAD: Active Universe v1 (1318 codes)
9674ee8  Notebook 3 skeleton
9cac8dc  Notebook 2 skeleton + handoff v2
29d86e8  handoff v1
f82dfb8  Delisted final (285 valid)
e1beb83  Delisted batch 4
aa9be79  Delisted batch 3
8299e5a  Delisted batch 2
0550a17  Delisted batch 1
cc14b6c  Delisted batch 0
2fcc0f4  VKOSPI 10y
```

---

## 2. 파일 인벤토리 (정확)

```
choonsimi-msm/
├── MSM_HANDOFF_2026_06_02.md       (v1, 일부 무효)
├── MSM_HANDOFF_2026_06_02_v2.md    (v2, 부분 무효)
├── MSM_HANDOFF_2026_06_02_v3.md    (v3, 최종 = 이 문서)
├── README.md
├── msm_data_supplement.ipynb       (Notebook 1, 실행 완료)
├── msm_data_ingestion.ipynb        (Notebook 2, 골격 + Step A 실행됨)
├── msm_state_vector.ipynb          (Notebook 3, 골격만)
└── data/
    ├── raw/
    │   ├── vkospi_10y.parquet      (2,307행, 2017-01-02 ~ 2026-06-02)
    │   ├── vkospi_10y_merged.csv   (원본 백업)
    │   ├── delisted/
    │   │   ├── ohlcv/year={2017..2026}.parquet  (289종목, 313,116행, adj)
    │   │   └── flow/year={2017..2026}.parquet   (285종목, 247,395+2,060행, 원)
    │   ├── active/                 (아직 비어있음 — Notebook 2 Step B~E)
    │   │   ├── ohlcv_adj/
    │   │   ├── ohlcv/
    │   │   ├── flow/
    │   │   └── foreign/
    │   └── macro/                  (비어있음 — Notebook 2 Step F)
    ├── universe/
    │   └── universe_msm.csv        ✓ 1,318종목 (596 KOSPI + 722 KOSDAQ)
    ├── state/                      (비어있음 — Notebook 3)
    └── checks/
        ├── delisted_codes.json       (291 후보)
        ├── delisted_excluded.json    (6 제외)
        └── delisted_validation.json
```

---

## 3. Q1~Q10 확정 셋 (락)

| Q | 결정 | 값 |
|---|---|---|
| Q1 | Universe | A: 전체 KRX 6축 필터 |
| Q2 | 수집 데이터 | A: OHLCV(adj+raw) + Flow + Foreign |
| Q3 | KOSPI200/지수 | A: 수집 (regime anchor) |
| Q4 | State Vector 수식 | A: 5축 그대로 (r, v, f, σ, ℓ) |
| Q5 | Normalization | C: dual (cross-sectional + time-series) |
| Q6 | 작업 분리 | B: Notebook 2 raw / Notebook 3 state |
| Q7 | Notebook 분리 | 2=ingestion, 3=state, normalization은 N3 |
| Q8 | 6축 필터 컷오프 | 1000억 / 3억 / 120d / FLAG / KOSPI+KOSDAQ / ETF·ETN 제외 |
| Q9 | BOK ECOS | A: 수집 (722Y001 한국 기준금리) |
| Q10 | 실행 시점 | 설계 단계는 X, 본실행은 다음 세션 |

---

## 4. State Vector 정의 (Notebook 3)

```
S_t = [r, v, f, σ, ℓ]

r     = log(close_t / close_{t-1})              # adjusted close (매뉴얼 §9.3)
v     = log(trade_value_t / 60d_mean)            # raw trade_value (매뉴얼 §9.4)
f     = (foreign_5d + inst_5d) / trade_value_5d  # Flow 금액 그대로
σ     = std(r) over 20d
ℓ     = log10(trade_value_60d / 100억)
```

**Dual normalization:**
- `r_cs, v_cs, f_cs, sigma_cs, ell_cs` (cross-sectional z-score, 매일 시점)
- `r_ts, v_ts, f_ts, sigma_ts, ell_ts` (time-series z-score, 매 종목)

**산출**: `data/state/state_vector.parquet` (15 컬럼)

---

## 5. 데이터 인벤토리 vs 부족분

| 항목 | 보유 | 부족 |
|---|---|---|
| Universe (active) | ✓ 1,318종목 | — |
| Delisted OHLCV | ✓ 289종목 (adj) | raw 거래대금 (근사 사용) |
| Delisted Flow | ✓ 285종목 (원) | — |
| Active OHLCV adj | ❌ | Notebook 2 Step B |
| Active OHLCV raw | ❌ | Notebook 2 Step C |
| Active Flow | ❌ | Notebook 2 Step D |
| Active Foreign | ❌ | Notebook 2 Step E |
| VKOSPI | ✓ 10년 | — |
| KOSPI200 | ❌ | Notebook 2 Step F (pykrx 1028) |
| KOSPI 종합 | ❌ | Step F (pykrx 1001) |
| KOSDAQ 종합 | ❌ | Step F (pykrx 2001) |
| KOSDAQ150 | ❌ | Step F (pykrx 2203) |
| USD/KRW | ❌ | Step F (FDR) |
| 한국 기준금리 | ❌ | Step F (ECOS 722Y001) |

---

## 6. 다음 세션 — Notebook 2 실행 가이드

### 6-1. 시작 셀
```python
# Setup + 인증 + cd
import os, json, time
from datetime import datetime
from pathlib import Path
import pandas as pd
import numpy as np
import requests

from google.colab import userdata
os.environ["KRX_ID"] = userdata.get("KRX_ID")
os.environ["KRX_PW"] = userdata.get("KRX_PW")
ECOS_KEY = userdata.get("ECOS_API_KEY")
GH_TOKEN = userdata.get("GH_TOKEN")

%cd /content/choonsimi-msm
from pykrx import stock as krx
import FinanceDataReader as fdr

START = "20170101"
END = datetime.now().strftime("%Y%m%d")
ROOT = Path("data")

# Universe 로드
df_univ = pd.read_csv(ROOT / "universe" / "universe_msm.csv", encoding="utf-8-sig", dtype={"code": str})
df_univ["code"] = df_univ["code"].str.zfill(6)
codes = df_univ["code"].tolist()
print(f"대상: {len(codes)}종목")
```

### 6-2. 실행 순서 (Step B ~ G)
1. **Step B** — Active OHLCV adjusted (1318종목 × ~2.4초 = **약 50분**, batch 50)
2. **Step C** — Active OHLCV raw + 시총 (일자별 batch, 영업일 10년 × 0.9초 = **약 40분**)
3. **Step D** — Active Flow (1318종목 × ~2.4초 = **약 50분**)
4. **Step E** — Active Foreign (1318종목 × ~2.4초 = **약 50분**)
5. **Step F** — Macro (KOSPI200/KOSPI/KOSDAQ/KOSDAQ150/VKOSPI 합치기/USD-KRW/BASE_RATE) (**약 5분**)
6. **Step G** — 검증 + push

**총 시간: 약 3~4시간.** Colab 무료 세션 12시간 한도 내, 단 분할 권장.

### 6-3. 분할 권장 (KRX 1시간 인증 만료 대비)
```
세션 1: Step B (50분) + Step F (5분) + push
세션 2: Step C (40분) + push
세션 3: Step D (50분) + push
세션 4: Step E (50분) + Step G (검증) + push
```
**pykrx 자동 재로그인 확인됨** (§9.10) — 한 세션 안에서 1시간 초과해도 자동 처리. 단 분할은 안전 마진.

### 6-4. 각 step 종료 시 push 패턴
```python
import subprocess
token = userdata.get("GH_TOKEN")
origin_url = subprocess.run(["git", "remote", "get-url", "origin"], capture_output=True, text=True).stdout.strip()
auth_url = origin_url.replace("https://", f"https://{token}@")
!git remote set-url origin {auth_url}
!git add data/raw/active/{step_name}/
!git commit -m "Active {STEP}: ..."
!git push origin main
!git remote set-url origin {origin_url}
```

---

## 7. Notebook 3 실행 가이드 (Notebook 2 완료 후)

### 전제
- `data/raw/active/` 4개 디렉토리 다 채워짐
- `data/raw/macro/macro_10y.json` 존재

### 셀 순서
1. 보유 데이터 점검 (Step 0)
2. Step A — delisted + active 통합 (5축 입력 패널)
3. Step B — 5축 계산 (r, v, f, σ, ℓ)
4. Step C — Dual normalization (CS + TS)
5. Step D — 저장 + 검증
6. Step E — Commit/push

**예상 시간: 30~60분** (메모리 큰 작업 — 547종목+ × 10년 일별)

### 주의
- **§9.4**: delisted는 raw trade_value 없어서 `close × volume` 근사 사용. v/ℓ 정확도 일부 손실. → 더 정확하게 하려면 Notebook 2에서 delisted raw도 별도 수집 (Step B' 추가 옵션, 형 결정 필요)
- **§9.6**: NaN 보간 X. 상장 전, lookback 부족은 NaN 유지
- **§9.8**: CA 종목 (분할 등) flag 처리 미적용. 현재 adjusted close 사용으로 영향 작음

---

## 8. Notebook 4+ 계획 (MSM STEP 3~7)

### Notebook 4 — Regime Detection (MSM STEP 3)
- 입력: state_vector.parquet
- 분류: trend / range / shock / transition
- 방법: volatility + flow + return clustering
- 매크로 anchor: KOSPI200 200MA + VKOSPI 임계값

### Notebook 5 — Transition Modeling (MSM STEP 4)
- P(S_{t+1} | S_t)
- Markov approximation 또는 embedding similarity

### Notebook 6 — Edge Field Estimation (MSM STEP 5)
- E(S_t → S_{t+1}) = expected return surface

### Notebook 7 — Tradeable Region Extraction (MSM STEP 6~7)
- Positive EV region 필터
- BUY/SELL/HOLD signal

**※ 각 Notebook 시작 전 형 Q&A 필수.**

---

## 9. §8 실수 목록 (오늘 세션 누적, 다음 세션 반복 금지)

1. Colab 환경 망각 (sandbox 제약 가정)
2. 보유 자산 확인 안 하고 신규 수집 제안
3. 사용자 파일 전달·실행 경로 합의 없이 진행
4. pykrx 내부 모듈 경로 추측 (`pykrx.website.krx.core` 존재 X)
5. 셀 단위 가이드 — 환경 확인 안 하고 "다음 셀 실행" 반복
6. 출력 예시 텍스트와 실행 코드 구분 안 함 (→ SyntaxError 유발)
7. Exception 잡았는데 라이브러리 내부 stderr만 출력 → fail counter 신뢰 X
8. 컨테이너 산출물 = 휘발성. 매 단계 commit 필수
9. Notebook 2 설계 시 premium repo 참조 가정 — 형 합의 없이 핸드오프 v1에 명시
10. git push 결과 검증 안 함. "Everything up-to-date"인데 완료 메시지 출력
11. listed_days 필터 — lookback 자체가 짧아 컷오프 효과 약화. 매뉴얼 §3 의도와 다름
12. **3번 정밀 검토 명령 미이행** — 매 응답 1번 검토. 형이 지적해야 재검토. **가장 심각**
13. "검토했나" 질문 후에야 검토 — 능동적 검토 부재
14. 추측 답변 ("거의 없을 것" 등) — 정확한 수치 없이 단정

---

## 10. §9 DATA_COLLECTION_MANUAL 수정 사항 (다음 세션 적용)

### 10-1. §5.1 단위 정정 (필수)
| 컬럼명 (한글) | 단위 |
|---|---|
| 거래량 | 주 |
| 거래대금 | 원 |
| 기관합계 | **원** (매뉴얼 "수량" 오기) |
| 외국인합계 | **원** |
| 개인 | **원** |
| 기타법인 | **원** |
| 전체 | 원 (≈0, 제로섬 검산) |

→ MSM flow 계산 시 raw_close 곱하기 불필요.

### 10-2. §6.1 KOSPI200 + 지수 코드 확정 (오늘 검증)
- 코스피 종합: `1001`
- 코스피 200: `1028`
- 코스닥 종합: `2001`
- 코스닥 150: `2203`
- VKOSPI: `1330` + `name_display=False`

### 10-3. §9.10 pykrx 자동 재인증 (오늘 추가)
- KRX 인증 1시간 만료
- pykrx 호출 도중 자동 감지 → 환경변수로 재로그인
- 메시지: `"KRX 세션 만료, 재로그인 시도... KRX 세션 갱신 완료"`
- 환경변수만 살아있으면 형 개입 불필요
- ⚠ 런타임 재시작 후엔 환경변수 재set 필요 (모듈 reload는 불필요)
- ⚠ `pykrx.website.krx.core` 같은 내부 경로 reload 시도 X (존재 안 함)

### 10-4. Universe 6축 필터 약점 (오늘 발견)
- listed_days 컷오프는 lookback 기간 자체에 의존
- 200달력일 lookback → 약 133영업일 max → 신규상장 <6개월만 효과적 제외
- state vector 계산 시 NaN 자동 처리로 보완

---

## 11. 환경 설정 체크리스트

### Colab Secrets (좌측 🔑 아이콘)
- ✓ `KRX_ID`
- ✓ `KRX_PW`
- ✓ `ECOS_API_KEY`
- ✓ `GH_TOKEN`

### 패키지
```
pip install pykrx pyarrow finance-datareader requests
```

### Repo clone (새 세션 시작 시)
```python
!git clone https://github.com/stanleyim/choonsimi-msm.git
%cd choonsimi-msm
```

---

## 12. 새 세션 시작 가이드

### 첫 메시지 권장
```
MSM Notebook 2 실행 시작.
MSM_HANDOFF_2026_06_02_v3.md 참고.

현재:
- choonsimi-msm repo 최신 (commit a52bfd5)
- Universe 1318종목 선정 완료
- Notebook 2 골격 push됨

다음:
- Step B (Active OHLCV adj) 50분
- 매 step 후 commit/push
- 분할 권장 (B → F → C → D → E)

§1 추측 X, §6 3번 검토 매번, §7 옵션 → 형 결정 → 실행 준수.
```

### Claude가 첫 응답에서 할 것
1. 핸드오프 v3 정독 (이 문서)
2. **§6 3번 정밀 검토 후 응답** — 1번 검토는 형 명령 위반
3. §1 추측 금지 — 모르는 건 묻거나 검증
4. Notebook 2 실행 시작 전 형 확인 (분할 방식, 시작 step)
5. 매 step 후 commit/push 필수

---

## 13. 메모리 관리 (Claude 세션)

- 오늘 세션 시작 → 종료: 약 8시간
- 메모리 사용: 75~80% 도달
- **권장: Notebook 2 실행은 새 세션 (Claude 메모리 클린).** 이번 세션은 설계까지만.

---

## 14. 핵심 한 줄

> "MSM은 STEP 1 데이터 수집의 active universe까지 완료. 다음은 active 데이터 본수집 (Notebook 2 Step B~G) 및 state vector 통합 (Notebook 3)."

---

**작성자**: Claude (MSM 세션 #1 어시스턴트)
**상태**: 데이터 수집 50% (delisted + universe 완료, active 데이터 미수집)
**다음 작업**: Notebook 2 Step B 실행 (active OHLCV adj 수집)
**우선순위**: 새 세션 시작 시 §6 3번 검토 매번 준수

끝.
