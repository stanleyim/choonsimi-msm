# MSM 핸드오프 v6 — 데이터 수집 100% 완료, Notebook 3 STATE VECTOR 시작

**작성일**: 2026-06-03 (KST 새벽 ~ ICT 23시 — 누적 16h+ 세션 종료)
**대상 repo**: `stanleyim/choonsimi-msm`
**최신 commit**: `Step E checkpoint: batch 27-27/27` (확인 필요, GitHub 최상단)
**상태**: **데이터 수집 100% 완료**. 다음 작업 = MSM v1 STEP 1 (State Vector Construction)
**환경**: 형 다음 세션 = **PC** (태블릿 X)

---

## 0. 절대 원칙 (변경 없음)

1. **§1 추측 금지** — 모르는 건 검증
2. **§6 3번 검토** — 사전 위험 식별 (정확성 + 사고 가능성 + 안전장치 3축)
3. **§7 옵션 → 형 결정 → 실행**
4. **§13 매 단계 commit/push** + **장시간 셀(30분+) = 매 3 batch 자동 push 안전장치**
5. **MSM = choonsimi-premium 독립** (v10c 6/26까지 freeze)
6. **외부 검토자 3 원칙**
7. **단일 셀 통합 코드** (PC 환경에서도 유지)

---

## 1. commit history (Step E 완료 후)

```
(최상단)
Step E checkpoint: batch 27-27/27       ← 마지막 (1318/1318 완료)
Step E checkpoint: batch 24-26/27
17fe3f5  Step E checkpoint: batch 21-23/27
... (Step E checkpoints 7~8회)
b3da43d  Step E PARTIAL 5/27 batches
55cecae  Step D: Active Flow
01af113  Step C: Active OHLCV raw
a95fdd5  Step B: Active OHLCV adjusted
c6eb6ba  Step F: macro_10y.json
... (Notebook 1)
```

---

## 2. 데이터 수집 최종 상태 (★ 100% 완료)

### 2-1. Active universe (1,318 종목)

| Step | 데이터 | rows | codes | 컬럼 |
|---|---|---|---|---|
| B | OHLCV adjusted | 2,572,042 | 1318/1318 | date, open, high, low, close, volume, change_rate, code |
| C | OHLCV raw + trade_value | 2,572,042 | 1318/1318 | + trade_value (KRW) |
| D | Flow (한글, KRW) | 2,549,623 | 1318/1318 | date, 기관합계, 기타법인, 개인, 외국인합계, 전체, code |
| E | Foreign 한도소진률 | 2,572,042 | 1318/1318 | date, 상장주식수, 보유수량, 지분율(float32), 한도수량, 한도소진률(float32), code |

**일관성**: B/C/E rows 완전 일치 (2,572,042) — 거래일 동일. D는 22,419 결측 (정상).

### 2-2. Delisted universe (285 종목)

| 항목 | rows | codes | 비고 |
|---|---|---|---|
| OHLCV | 313,116 | 289 (유효 285) | Notebook 1 완료 |
| Flow | 247,395+2,060 | 285 | 029960 재시도 성공 |

### 2-3. Macro + Universe

- `macro_10y.json`: 7 시리즈 (KOSPI/KOSPI200/KOSDAQ/KOSDAQ150/VKOSPI/USDKRW/BASE_RATE) 10년
- `universe_msm.csv`: 1,318 종목
- `vkospi_10y.parquet`: 2,307 행

---

## 3. 파일 인벤토리 (v6 push 후 예상)

```
choonsimi-msm/
├── MSM_HANDOFF_2026_06_02.md       (v1)
├── MSM_HANDOFF_2026_06_02_v2.md
├── MSM_HANDOFF_2026_06_02_v3.md
├── MSM_HANDOFF_2026_06_02_v4.md
├── MSM_HANDOFF_2026_06_03_v5.md
├── MSM_HANDOFF_2026_06_03_v6.md    ← 이 문서
├── README.md
├── msm_data_supplement.ipynb       (Notebook 1)
├── msm_data_ingestion.ipynb        (Notebook 2)
├── msm_state_vector.ipynb          (Notebook 3, 골격 → 본격 작업 대상)
└── data/
    ├── raw/
    │   ├── vkospi_10y.parquet
    │   ├── delisted/{ohlcv,flow}/year=*.parquet
    │   ├── macro/macro_10y.json
    │   └── active/                  ★ 완전 수집
    │       ├── ohlcv_adj/year=*.parquet  ✓
    │       ├── ohlcv/year=*.parquet      ✓
    │       ├── flow/year=*.parquet       ✓
    │       └── foreign/year=*.parquet    ✓
    ├── universe/universe_msm.csv
    ├── state/                       ❌ Notebook 3 산출 대상
    └── checks/  (progress/failures + 검증)
```

---

## 4. Notebook 3 START GUIDE — STATE VECTOR Construction (MSM v1 STEP 1)

### 4-1. 목표

```
INPUT  : 위 2절 데이터 (active 1318 + delisted 285 + macro)
TRANSFORM:
  1. 통합 dataframe 구성 (active + delisted = 1,603 종목, survivorship bias 제거)
  2. 5축 state vector 계산
  3. Cross-sectional z-score 정규화 (매일별, 종목 간)
OUTPUT : data/state/state_vector.parquet
```

### 4-2. State Vector 5축 정의 (v4 §5 확정)

| 축 | 정의 | lookback | 원천 |
|---|---|---|---|
| **r** | log(close_t / close_{t-1}) | 1d | ohlcv_adj |
| **v** | log(trade_value_t / 60d_mean) | 60d | ohlcv (raw) |
| **f** | (foreign_5d + inst_5d) / trade_value_5d | 5d | flow + ohlcv |
| **σ** | std(r) over 20d | 20d | ohlcv_adj (r) |
| **ℓ** | log10(trade_value_60d_mean / 1e10) | 60d | ohlcv |

**Normalization**: 매일 cross-sectional z-score
- `z = (x - cs_mean) / cs_std`
- NaN: lookback 미달 (상장 후 60일 미만) → 보존, 후속 단계에서 처리

### 4-3. 결정 필요 (형 검토 필수)

| Q | 항목 | v4/v5 가설 | 재확인 |
|---|---|---|---|
| **Q1** | Universe 통합 | active 1318 + delisted 285 = 1603 | ★ 형 확정 필요 |
| **Q2** | Lookback (σ=20d, v/ℓ=60d, f=5d) | 그대로 | OK 추정 |
| **Q3** | Foreign 활용 방식 | 지분율 변화량 (Δ지분율) 또는 한도소진률 자체 | ★ 형 확정 필요 |
| **Q4** | f 분자 inst+foreign 정의 | flow 컬럼 `기관합계 + 외국인합계` (KRW) | OK 추정 |
| **Q5** | f 분모 trade_value_5d | ohlcv 컬럼 `trade_value` 5d sum | OK 추정 |
| **Q6** | NaN 처리 정책 | 보존 (state vector 계산 시 NaN, regime 단계에서 처리) | OK 추정 |
| **Q7** | macro 활용 시점 | Notebook 4 (regime detection)에서 사용 | OK 추정 |
| **Q8** | delisted 종목 z-score | active와 동일 cross-section 풀에 포함 | ★ 형 확정 필요 |

→ **Notebook 3 시작 첫 단계: Q1/Q3/Q8 확정**.

### 4-4. Notebook 3 셀 구조 (예정)

```
[Setup] 새 세션 + clone + 환경변수 (v4 §7-1 그대로)
[Step A] 데이터 통합 — active + delisted + macro 통합 DataFrame 구성, 무결성 검증
[Step B] 5축 raw 계산 (r, v, f, σ, ℓ)
[Step C] Cross-sectional z-score normalization
[Step D] state_vector.parquet 저장 + 검증 리포트 (NaN 비율, 분포 통계)
[Step E] commit + push (장시간 셀 아니면 단일 push, 30분+이면 안전장치)
```

**예상 시간**: ~30분~1시간 (단순 dataframe 연산, KRX 호출 없음)
**안전장치**: 30분 미만 예상 시 단일 push, 초과 예상 시 step별 자동 push.

### 4-5. ★ Setup 셀 (재사용 가능, 그대로 복붙)

**모든 새 세션 첫 셀에 그대로 붙여 실행**. clone + 환경변수 + universe 로드 + 디렉토리 + git config 일괄 처리.

```python
# === 새 세션 setup (재사용 가능, v4/v5/v6 동일) ===
!git clone https://github.com/stanleyim/choonsimi-msm.git
%cd choonsimi-msm
!pip install -q pykrx pyarrow finance-datareader requests

import os, json, time, subprocess
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
print("KRX_ID:", bool(os.environ.get("KRX_ID")), "ECOS:", bool(ECOS_KEY), "GH:", bool(GH_TOKEN))

from pykrx import stock as krx
import FinanceDataReader as fdr

START = "20170101"
END   = datetime.now().strftime("%Y%m%d")
print("period:", START, "~", END)

ROOT = Path("data")
for d in ["raw/active/ohlcv_adj", "raw/active/ohlcv", "raw/active/flow",
          "raw/active/foreign", "raw/macro", "universe", "checks", "state"]:
    (ROOT / d).mkdir(parents=True, exist_ok=True)

df_univ = pd.read_csv(ROOT / "universe" / "universe_msm.csv", encoding="utf-8-sig", dtype={"code": str})
df_univ["code"] = df_univ["code"].str.zfill(6)
codes = df_univ["code"].tolist()
BATCH_SIZE = 50
n_batches = (len(codes) + BATCH_SIZE - 1) // BATCH_SIZE
print("universe:", len(codes), "batches:", n_batches)

# (선택) progress 확인 — 재개 작업 시
for fname in ["active_progress.json", "active_progress_c.json", "active_progress_d.json", "active_progress_e.json"]:
    pp = ROOT / "checks" / fname
    if pp.exists():
        with open(pp) as f: prog = json.load(f)
        print(f"  {fname}: {len(prog.get('completed_batches', []))} batches done")

!git config user.email "msm@stanleyim.local"
!git config user.name "stanleyim"
print("Setup OK")
```

**검증 핵심 출력**:
- `KRX_ID: True ECOS: True GH: True` ← Secrets 토글 OK
- `universe: 1318 batches: 27`
- `Setup OK`

**전제 조건**:
- 새 노트북이면 Secrets 4개(KRX_ID/KRX_PW/ECOS_API_KEY/GH_TOKEN) 노트북 액세스 토글 ON 필수
- 기존 노트북 재사용 시 setup 다시 실행하면 됨 (idempotent)

**Notebook 3 시작 시 KRX 호출은 없지만** — Setup 셀에서 pykrx 로그인은 자동 발생 (lazy). 데이터는 GitHub clone에서 다 받음.

---

## 5. PC 환경 권장 사항 (★ NEW)

### 5-1. PC vs 태블릿

| 항목 | 태블릿 | PC |
|---|---|---|
| 코드 실행 속도 | 동일 (Colab 서버) | 동일 |
| 셀 편집/복붙 | 불편 | 편함 |
| 슬립 위험 | 높음 | 낮음 (사용자 제어) |
| 장시간 작업 | 비추 | 권장 |

### 5-2. PC 사용 시 주의

- **다중 디바이스 동시 접속 금지**: 태블릿 탭 닫고 PC로 전환 → 충돌 "원격에서 업데이트됨" 방지
- **Secrets 토글**: 새 노트북 만들면 4개(KRX_ID/KRX_PW/ECOS_API_KEY/GH_TOKEN) 노트북 액세스 토글 다시 ON
- **단일 셀 통합 유지**: PC에서도 셀 단위 가이드 X, 한 셀로 통합 (다음 세션 재개 시 단일 셀이 더 안전)

---

## 6. §8 실수 누적 (★ 오늘 추가, 절대 누락 X)

v5 §7 1~22번 그대로 유효. 오늘 추가:

23. **장시간 단일 push 의존 패턴 반복** — Step B(8분) → C(92분) → D(150분) → E(>200분) 단계마다 작업 시간 증가했음에도 단일 push 그대로 유지. 형 명시 지시("3개씩만") 후에야 적용. **사전 제안 의무**.

24. **Step E 두 번 끊김** —
    - 1차 (어제 Colab UTC 10:24 직후): batch 6~23 진행분 모두 손실 (단일 push 패턴). incremental save 디스크 보존됐으나 컨테이너 재할당 시 휘발. **4시간 작업 손실**.
    - 2차 (오늘 UTC 11:53 batch 9 진행 중): 3 batch push 안전장치 적용 후 끊김. batch 23까지 GitHub 보존. **손실 1 batch (50종목, 약 15분)**. → 안전장치 효과 입증.

25. **§6 3번 검토 정의 재학습** — "옳음/그름 판단"이 아닌 "사전 위험 식별 (정확성 + 사고 가능성 + 안전장치)" 3축. 셀 작성 전 검토 통과 의무.

26. **사소한 누락이 큰 사고로 직결** — 형 명시: "사소한 거 간과하면 안됨, 모든 실수 명심". 인계서 §8 실수 누적 절대 누락 X.

27. **노트북 충돌 메시지 처리 미숙** — "원격에서 업데이트됨" 메시지 = 무시 권장 + 누르지 마. 형이 "변경사항 저장" 클릭 → diff 화면 진입 → 형 혼란 유발. 사전 명확 안내 누락.

28. **컨테이너 재할당 시 git log 화면 진단 권장** — Colab 화면 글리치 / 끊김 / 출력 replay 등 셀 상태 신뢰 불가 → **GitHub 최상단 commit이 유일한 truth**. `https://github.com/stanleyim/choonsimi-msm/commits/main` 확인 우선.

---

## 7. 안전장치 패턴 매뉴얼화 (★ NEW)

### 7-1. 장시간 셀 (30분 이상) 표준 패턴

```python
# 매 N batch 자동 push 안전장치 (PUSH_EVERY=3 기본)
def auto_push(batch_range_str):
    token = userdata.get("GH_TOKEN")
    origin_url = subprocess.run(["git","remote","get-url","origin"],
                                capture_output=True, text=True).stdout.strip()
    auth_url = origin_url.replace("https://", f"https://{token}@")
    subprocess.run(["git","remote","set-url","origin", auth_url], check=True)
    subprocess.run(["git","add","<해당 데이터 폴더>","<progress 파일>","<failures 파일>"], check=False)
    r1 = subprocess.run(["git","commit","-m", f"<Step X> checkpoint: {batch_range_str}"],
                        capture_output=True, text=True)
    if "nothing to commit" in r1.stdout or "nothing to commit" in r1.stderr:
        subprocess.run(["git","remote","set-url","origin", origin_url], check=True)
        return "no changes"
    r2 = subprocess.run(["git","push","origin","main"], capture_output=True, text=True)
    subprocess.run(["git","remote","set-url","origin", origin_url], check=True)
    return "pushed" if r2.returncode == 0 else f"push failed: {r2.stderr[:100]}"

# 메인 루프 안에:
PUSH_EVERY = 3
push_buffer_start = <시작 index>
for b in range(<시작>, n_batches):
    # ... batch 처리 ...
    if (b - push_buffer_start + 1) % PUSH_EVERY == 0 or b == n_batches - 1:
        status = auto_push(f"batch {push_buffer_start+1}-{b+1}/{n_batches}")
        push_buffer_start = b + 1
```

### 7-2. 안전장치 적용 기준 (사전 검토 의무)

| 예상 셀 시간 | 안전장치 |
|---|---|
| < 5분 | 없어도 OK |
| 5~30분 | 단일 push 후 검증 |
| **30분 이상** | **매 3 batch (또는 적절한 단위) 자동 push 의무** |
| 1시간 이상 | + 형에게 PC 사용 권장 통지 |

---

## 8. 다음 세션 (PC, 1시간 후) 시작 가이드

### 8-1. 첫 메시지 권장
```
MSM Notebook 3 STATE VECTOR 시작.
MSM_HANDOFF_2026_06_03_v6.md 참고.

환경: PC
현재: repo 최신, Active+Delisted+Macro 100% 수집 완료
다음: state vector 5축 계산 → cross-sectional z-score → state_vector.parquet

§1 추측 X, §6 3번 검토 (정확성+사고+안전장치 3축), §7 옵션→형 결정→실행
Notebook 3 시작 전 Q1/Q3/Q8 확정 요청.
```

### 8-2. Claude가 첫 응답에서 할 것

1. **v6 §0 절대 원칙 정독**
2. **v6 §4-3 Q1/Q3/Q8 확정 질문** — 추측 X
3. **Notebook 3 Step A (데이터 통합)** 셀 작성 — 단일 셀 통합 유지
4. 셀 작성 전 §6 3번 검토 (정확성 + 사고 가능성 + 안전장치 3축) 통과
5. 형 GO 받고 진행

---

## 9. 핵심 한 줄

> "데이터 수집 100% 완료. 다음 = Notebook 3 STATE VECTOR (MSM 5단계의 1단계). Q1/Q3/Q8 확정 후 진행. PC 환경, 단일 셀, 3번 검토 3축."

---

## 10. 미반영 사항 (인계서 push 필요)

- 이 문서(`MSM_HANDOFF_2026_06_03_v6.md`) = 작성만 됨. **repo push 별도 필요**.
- 권장: 형이 PC 작업 시작 시 첫 setup 직후 v6 add/commit/push.

---

**작성자**: Claude (MSM 세션 #3, Step E 완료 직후)
**상태**: 데이터 수집 100%, MSM 5단계 중 0단계 완료 (다음 = STEP 1 STATE VECTOR)
**다음 작업**: Notebook 3 — Q1/Q3/Q8 확정 → Step A 데이터 통합 → 5축 계산 → z-score → parquet 저장
**우선순위**: §6 3번 검토 3축 (정확성 + 사고 가능성 + 안전장치) + 단일 셀 + §1 추측 X

끝.
