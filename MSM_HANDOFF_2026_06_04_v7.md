# MSM 핸드오프 v7 — STEP 1 (State Vector Construction) 완료

**작성일**: 2026-06-04 (KST 새벽)
**대상 repo**: `stanleyim/choonsimi-msm`
**최신 commit (push 직전)**: `6979a1d` — MSM STEP 1 state_vector year partitions
**상태**: ★ **MSM v1 STEP 1 (State Vector Construction) 완료 — LOCKED**
**다음**: STEP 2 (Regime Detection)
**환경**: PC 또는 태블릿 (단일 셀 통합 유지)
**다음 세션**: 4시간 후

---

## 0. 절대 원칙 (변경 없음, v6 §0 그대로)

1. §1 추측 금지 — 모르는 건 검증
2. §6 3번 검토 — 사전 위험 식별 (정확성 + 사고 가능성 + 안전장치 3축)
3. §7 옵션 → 형 결정 → 실행
4. §13 매 단계 commit/push + 장시간 셀(30분+) = 매 3 batch 자동 push
5. MSM = choonsimi-premium 독립 (v10c 6/26까지 freeze)
6. 외부 검토자 3 원칙
7. 단일 셀 통합 코드

---

## 1. ★ LOCKED VALUES (immutable baseline)

```
state_vector.parquet (year partition, 10개)
  path:     data/state/state_vector/year={2017..2026}.parquet
  shape:    (2,793,837, 12)
  universe: 1,603 codes (active 1318 + delisted 285)
  period:   2017-01-02 ~ 2026-06-02
  columns:  date, code, r, sigma, v, ell, f, z_r, z_sigma, z_v, z_ell, z_f
  dtype:    float32 (10 numeric cols)
  size:     162.06 MB total, max single 17.91 MB
```

NaN 비율 (LOCKED, 검증값):
- r:     0.0574% (first-row per code)
- sigma: 0.5734% (G1: 20d valid < 10)
- v:     1.6611% (G1: 60d valid < 30)
- ell:   1.6611% (G1: 60d valid < 30)
- f:     0.1148% (G1: 5d valid < 3)
- z_*:   raw와 동일 (std=0 가드 발동 0회)

---

## 2. ★ 확정 정책 (변경 금지)

### 2-1. R1: 거래정지일 행 제거 (raw 기준)
```
mask = (volume != 0) AND (trade_value != 0)
- active raw: 2,572,042 → 2,545,604 (drop 26,438)
- delisted raw: 309,753 → 248,233 (drop 61,520)
- adj는 raw 키로 INNER (동기 drop)
```

### 2-2. U1: Universe 유지 = 1603
- active 1318 + delisted 285 = 1603
- 좀비 종목 lookback NaN으로 자동 자연 제외
- ★ universe 변경 시 STEP 2 재현성 붕괴 → 절대 변경 금지

### 2-3. G1: lookback 50% 가드
```
r:     가드 없음 (1d 차분)
sigma: 20d 중 min_periods=10
v:     60d 중 min_periods=30
ell:   60d 중 min_periods=30
f:     5d 중 min_periods=3
```

### 2-4. P_R5: r 극단값 무처리
- root cause: 거래정지 재개일 가격 갭 + corp.action (CASE 3)
- 빈도: |r|>1.0 = 158/2.79M = 0.0057%
- 최악 day (2018-09-28): 11/1603 = 0.69%
- 정책: 데이터 오류 0건 → 무처리 = §1 추측 X 부합

### 2-5. r 계산 source
```
r = log(close_adj_t / close_adj_{t-1})
v/f/ell source = raw.trade_value
```

### 2-6. f 정의
```
f = (inst_5d + foreign_5d) / trade_value_5d
- inst_5d:    flow.기관합계 (KRW) 5d rolling sum
- foreign_5d: flow.외국인합계 (KRW) 5d rolling sum
- trade_value_5d: ohlcv.trade_value 5d rolling sum
```

### 2-7. Foreign 한도소진률 — 미사용 (Q3=D)
- 데이터 수집 완료, parquet 보존
- STEP 1 5축에 미포함, STEP 4+ 옵션 보존

### 2-8. Cross-sectional z-score
```
매일 (groupby('date')):
  z = (x - day_mean) / day_std
  std == 0 → NaN
  inf → NaN
```

### 2-9. 저장 형식: PT_year
- GitHub 단일 파일 100MB 한도 회피
- data/state/state_vector/year=*.parquet (10 partitions)

---

## 3. 파일 인벤토리 (commit 6979a1d 시점)

```
choonsimi-msm/
├── MSM_HANDOFF_2026_06_02.md (v1~v4)
├── MSM_HANDOFF_2026_06_03_v6.md
├── MSM_HANDOFF_2026_06_04_v7.md ← 이 문서
├── README.md
├── msm_data_supplement.ipynb (Notebook 1)
├── msm_data_ingestion.ipynb (Notebook 2)
├── msm_state_vector.ipynb (Notebook 3)
└── data/
    ├── raw/
    │   ├── vkospi_10y.parquet
    │   ├── delisted/
    │   │   ├── ohlcv/year=*.parquet (adj, 289 codes, 313,116 rows)
    │   │   ├── ohlcv_raw/year=*.parquet (raw+tv, 285 codes, 309,753 rows) ★ v7 신규
    │   │   └── flow/year=*.parquet (285 codes, 249,455 rows)
    │   ├── macro/macro_10y.json
    │   └── active/
    │       ├── ohlcv_adj/year=*.parquet (1318 codes, 2,572,042 rows)
    │       ├── ohlcv/year=*.parquet (1318 codes, 2,572,042 rows)
    │       ├── flow/year=*.parquet (1318 codes, 2,549,623 rows)
    │       └── foreign/year=*.parquet (1318 codes, 2,572,042 rows)
    ├── universe/universe_msm.csv
    ├── state/state_vector/year=*.parquet ★ v7 신규 (STEP 1 산출)
    └── checks/ (progress + failures + validation)
```

---

## 4. STEP 1 진행 기록 (감사 추적)

### 4-1. 주요 commit
```
6979a1d  MSM STEP 1: state_vector year partitions (PT_year)
f593b59  Delisted raw checkpoint: batch 4-6/6
4fb65d2  Delisted raw checkpoint: batch 1-3/6
bf15695  Add files via upload (v6 인계서)
069d8e5  Step E checkpoint: batch 27-27/27 (Active foreign 완료)
```

### 4-2. 작업 단계 (Notebook 3 = state_vector 빌드)

| Step | 작업 | 시간 | 결과 |
|---|---|---|---|
| 사전 | F8 진단: delisted OHLCV에 trade_value 없음 | - | 재수집 결정 |
| 수집 | delisted ohlcv_raw 285 codes | 12.3분 | 309,753 rows, 검증 5항 통과 |
| A-1 | Inspect (스키마 가정 0) | - | 컬럼 매핑 확정 |
| A-2 | Merge (R1+U1+G1) | ~5분 | df_all (2,793,837 × 24), V1~V9+ABC 통과 |
| 사전 | F14 진단: r 극단값 root cause | - | CASE 3 확정, P_R5 무처리 |
| B | 5축 raw 계산 | ~2분 | r/σ/v/ℓ/f 추가, inf 0건 |
| C | Cross-sectional z-score | ~2분 | day-mean=0, day-std=1 수학적 완벽 |
| D | 저장 + 검증 + push | ~1분 | 단일 파일 실패 (127MB > 100MB) |
| D-FIX | PT_single → PT_year 전환 | ~1분 | 10 partitions, max 17.91MB, push ✓ |

### 4-3. 핵심 발견 (F8~F18)
- F8: delisted OHLCV adj에 trade_value 없음 → raw 285 재수집
- F9: active raw 거래정지일 행 26,438개 (1.03%) pykrx 보존 패턴
- F9-2: active 거래정지 종목 334개, top 007610 = 1005일 정지
- F10: R1+U1+G1 정책 (좀비 종목 자동 자연 제외)
- F11: volume_adj==0 479행 (raw R1로 영향 없음)
- F12: close_raw/close_adj ratio min=0.0019, max=78 (corp.action 정상)
- F13: delisted bottom 5 rows = 7~26 (G1 자동 제외)
- F14: r 극단값 158개 — root cause = 거래정지 재개
- F14-3: 2018-09-28 11 extreme 모두 184~407일 정지 후 재개 (CASE 3)
- F14-4: raw/adj 방향 불일치 27건 모두 corp.action 정상
- F18: 032040, 026260 의심 해소 (수정주가 정상)

---

## 5. §8 실수 누적 (v6 #1~28 유지 + v7 신규 4건)

v6: 추측 금지, Colab 환경 망각, 셀 단위 가이드, pykrx 추측, 환경 확인 누락, exception 미숙, GitHub=truth, 3번 검토 3축, 안전장치 사전 제안, 인계서 §8 누락 X, 노트북 충돌 처리 등.

### v7 신규
- **#29. Setup 통합 셀 작성 시 pip install 누락** — clone + Secrets만 했고 pip install 빠뜨림. ModuleNotFoundError. 재발 방지: 새 세션 첫 setup 셀에 pip install 반드시 포함.
- **#30. merge suffix 적용 후 컬럼 참조 검증 누락** — adj↔raw merge 후 volume → volume_adj/_raw 분리. V5 검증 코드 KeyError. 재발 방지: merge suffix 후 컬럼 참조 전수 검증.
- **#31. C4 pool=0 정상 패턴(lookback warm-up) 비교 누락 위험** — Step C 후 일별 풀 크기 min=0 자동 무시 가능. G1 warm-up과 정확 일치 사전 확인 필수.
- **#32. GitHub 단일 파일 100MB 한도 사전 점검 누락** — state_vector.parquet 127.20MB push 실패. 재발 방지: parquet 저장 시 100MB 검증 의무.

---

## 6. 다음 세션 (4시간 후) START GUIDE

### 6-1. 첫 메시지 권장
```
MSM STEP 2 (Regime Detection) 시작.
MSM_HANDOFF_2026_06_04_v7.md 참고.

환경: PC/태블릿
현재: STEP 1 완료, state_vector.parquet LOCKED
   - 2,793,837 rows × 12 cols
   - universe 1603 (LOCKED)
   - z 5축 정규화 완료
다음: STEP 2 Regime Detection 설계 → 방법론 결정 → 구현

§1 추측 X, §6 3번 검토 3축, §7 옵션→형 결정→실행, 단일 셀.
v7 §6-3 전체 일괄 setup 셀 사용. Q-R1 결정 요청.
```

### 6-2. Claude 첫 응답 할 것
1. v7 §0 절대 원칙 정독
2. v7 §1 LOCKED VALUES 확인 (state_vector.parquet 검증)
3. v7 §6-3 setup 셀 송부
4. STEP 2 방법론 옵션 Q-R1 제시 (추측 X)
5. §6 3번 검토 통과 후 형 GO 받고 진행

### 6-3. ★ 전체 일괄 setup 셀 (다음 세션 복붙용)

```python
# === 새 세션 setup (v7 표준) ===
import os, json, subprocess
from pathlib import Path
import pandas as pd
import numpy as np

# [0] cwd + 기존 디렉토리 제거
%cd /content
!rm -rf /content/choonsimi-msm

# [1] Clone
!git clone https://github.com/stanleyim/choonsimi-msm.git
%cd /content/choonsimi-msm

# [2] pip install (★ #29 재발 방지)
!pip install -q pykrx finance-datareader pyarrow requests
import pykrx, pyarrow, FinanceDataReader, requests
print(f'pykrx={pykrx.__version__} pyarrow={pyarrow.__version__} fdr={FinanceDataReader.__version__}')

# [3] Secrets
from google.colab import userdata
secret_status = {}
for k in ['KRX_ID', 'KRX_PW', 'ECOS_API_KEY', 'GH_TOKEN']:
    try:
        v = userdata.get(k)
        if v:
            if k in ('KRX_ID', 'KRX_PW'):
                os.environ[k] = v
            secret_status[k] = True
        else:
            secret_status[k] = False
    except Exception:
        secret_status[k] = False
print('Secrets:', secret_status)

# [4] git config
!git config user.email 'msm@stanleyim.local'
!git config user.name 'stanleyim'

# [5] state_vector load (STEP 1 LOCKED)
from glob import glob
sv_files = sorted(glob('data/state/state_vector/year=*.parquet'))
df_sv = pd.concat([pd.read_parquet(f) for f in sv_files], ignore_index=True)
print(f'state_vector shape: {df_sv.shape}')  # (2793837, 12)
print(f'universe: {df_sv.code.nunique()}')   # 1603
assert df_sv.shape == (2793837, 12)
assert df_sv['code'].nunique() == 1603

# [6] git log
!git log --oneline -3
print('Setup OK')
```

---

## 7. STEP 2 사전 설계 (Regime Detection)

### 7-1. 목표
```
INPUT  : state_vector.parquet (z 5축, 2.79M rows, 1603 codes)
TRANSFORM:
  매일 또는 종목별 state → regime label
  regime ∈ {trend, range, shock, transition}
OUTPUT : data/state/regime.parquet (date, code, regime_label, regime_score)
```

### 7-2. 결정 필요 (Q-R1 ~ Q-R6)

| Q | 항목 | 옵션 |
|---|---|---|
| Q-R1 | 방법론 | A. Rule-based / B. Clustering (KMeans/GMM/HDBSCAN) / C. HMM / D. Vol regime 단순 규칙 |
| Q-R2 | regime 정의 | trend/range/shock/transition 수학적 정의 명시 |
| Q-R3 | universe 단위 | per-stock vs market-wide vs hybrid |
| Q-R4 | 입력 축 | z 5축 전부 vs 일부 |
| Q-R5 | 시계열 처리 | 매일 독립 vs sticky |
| Q-R6 | macro 활용 | VKOSPI/KOSPI200 등 macro_10y.json 입력 추가 여부 |

### 7-3. STEP 2 셀 구조
```
[Setup] v7 §6-3 setup 셀
[Step A] state_vector + macro load + sanity (z 분포 재확인)
[Step B] regime 정의 + 라벨링 (Q-R1 채택)
[Step C] regime label 무결성 검증
[Step D] regime.parquet 저장 + commit + push
```

예상 시간: 30분~1시간

---

## 8. 핵심 원칙 (재공지)

1. §1 추측 금지
2. §6 3번 검토 3축: 정확성 + 사고 가능성 + 안전장치
3. §7 옵션 → 형 결정 → 실행
4. 단일 셀 통합
5. GitHub = truth
6. LOCKED VALUES 변경 금지 (state_vector.parquet 1603 × 12 × 2.79M)
7. MSM = choonsimi-premium 독립 (v10c 6/26까지 freeze)

---

## 9. 핵심 한 줄

> STEP 1 완료. state_vector.parquet LOCKED. 다음 = STEP 2 Regime Detection. Q-R1~Q-R6 결정 후 진입.

---

**작성자**: Claude (MSM 세션 #4, STEP 1 완료 직후)
**상태**: MSM 5단계 중 STEP 1 완료
**다음 작업**: Q-R1~Q-R6 결정 → Regime Detection 설계 → 구현 → regime.parquet

끝.