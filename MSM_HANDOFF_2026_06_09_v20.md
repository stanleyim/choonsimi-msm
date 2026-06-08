# MSM 핸드오프 v20 — STATE freeze COMPLETE (9.4y axis_raw + 3 flags)

작성일: 2026-06-09 (KST, MSM 세션 #15 종결)
대상 repo: stanleyim/choonsimi-msm
최신 commit: cfa4aa6 — MSM v20 fix: M16_expiry_flag day range 6→5 (60/60 outlier cover)
상태: ★ STATE VECTOR v20 LOCKED. REGIME 분류 진입 가능.
다음 작업: REGIME 분류 (v4 STEP 2)

---

## 0. 절대 원칙 (v19 §0 동일)

1. §1 추측 금지
2. §6 3번 검토 (정확성 + 사고 가능성 + 안전장치)
3. §7 옵션 → 형 결정 → 실행
4. §13 매 단계 commit/push
5. MSM = choonsimi-premium 독립
6. 단일 셀 통합 코드
7. Long-running 작업 batch + auto-push 의무
8. forward test 발견 진실 즉시 진단

---

## 1. LOCKED VALUES

### 1-1. v12 LOCK (불변)
- commit 559a65e, NET Sharpe 0.686

### 1-2. v18~v19 LOCK (불변)
- build_axis.py SSOT (195750f, 9.4y 검증)
- M17 = front-month (deterministic), M15/M16 = max_vol
- 5월 cross-val 19/19 PASS

### 1-3. v20 NEW LOCK ★

axis_raw_17axis.parquet (raw, 무변경):
- shape: (2309, 18)
- range: 2017-01-02 ~ 2026-06-05
- fail count: 0

axis_raw_v20.parquet (raw + 3 flags) ★:
- shape: (2309, 21)
- 추가 flag:
  - M17_missing: 470 (VKOSPI 선물 거래 단절)
  - M19_missing: 331 (KOSDAQ150 옵션 미상장)
  - M16_expiry_flag: 256 (3/6/9/12월 5~14일)
- M16 outlier cover: 60/60 (100%)

---

## 2. 본 세션 (#15) 진행 내역

### 2-1. Setup
- CWD 잔존 문제 → os.chdir('/content') 추가
- handoff v19 commit (660ccfd) 발견 → HEAD 갱신

### 2-2. K3 영업일 source
- 옵션 C 채택 (ohlcv parquet unique dates)
- 1,846 dates 확보 (2017-01-02 ~ 2024-07-05)

### 2-3. K3 9.4y backfill ★
- 138.2분 (예상 3~5h 대비 단축)
- fail 0 — v19 §11 risk 완전 해소
- 최종 axis_raw: 2,309 rows

### 2-4. Sanity 결과
- 16/19 axes NaN = 0
- M17 NaN 470 (20.4%) / M19 NaN 331 (14.3%) / M16 outlier 60 → 진단 진입

### 2-5. Anomaly 진단 (raw level)

M19 = KOSDAQ150 옵션 PCR (build_axis L160 직접 read):
- 2017년 100% NaN = 옵션 미상장 (2018-03-26 이후 정상)

M17 = front-month VKOSPI 거래 단절 (20 dates raw dump):
- 20/20 sample = CLS_MISSING (vol=0, cls=빈문자열, spot 정상)
- candidates=6 (contract listing OK)
- 시장 정보 (저변동성 + 거래 동결)

M16 outlier = 분기 만기 cluster:
- 60 dates 전부 3/6/9/12월 5~14일
- 2025년 이후 std 4 (vs 2017~2024 std 165~324) — 미시구조 변화

### 2-6. STATE freeze 정책 LOCK

| Axis | 정책 | flag |
|---|---|---|
| M17 | KEEP + flag | M17_missing |
| M19 | KEEP + flag | M19_missing |
| M16 | RAW 유지 + flag | M16_expiry_flag |

### 2-7. M16_expiry_flag 정의 보정
- 1차: day 6~14 → 58/60 cover
- 2차: day 5~14 → 60/60 (100%) ★

---

## 3. STATE VECTOR v20 정의

S_t = {
  raw axes (16): M1-M11, M15-M19
  flags (3): M17_missing, M19_missing, M16_expiry_flag
  meta: _n_valid
}

### 3-1. flag 코드

df['M17_missing'] = df['M17'].isna().astype(int)
df['M19_missing'] = df['M19'].isna().astype(int)

def is_quarterly_expiry_week(date):
    return (date.month in [3,6,9,12]) and (5 <= date.day <= 14)
df['M16_expiry_flag'] = df['date'].apply(is_quarterly_expiry_week).astype(int)

### 3-2. axis 정의

| Axis | 정의 | NaN 의미 |
|---|---|---|
| M1 | VKOSPI | - |
| M2 | VKOSPI 변화 | - |
| M3-M4 | (build_axis.py SSOT) | - |
| M5-M11 | 투자자별 net flow | - |
| M15 | KOSPI200 선물 basis (max_vol) | - |
| M16 | KOSDAQ150 선물 basis (max_vol) | - |
| M17 | VKOSPI 선물 basis (front-month) | vol=0 거래단절 |
| M18 | (확인 필요 — 후순위) | - |
| M19 | KOSDAQ150 옵션 PCR | 옵션 미상장 |

---

## 4. 다음 세션 (#16) — REGIME 진입

### 4-1. 입력
- data/state/axis_raw/axis_raw_v20.parquet

### 4-2. REGIME 정의 (v4 STEP 2 1차)
- shock: M1 > 40 또는 quantile 90%+
- trend: |M5/M7 flow| 임계 + |M2| 작음
- range: |M2| 작음 + |basis| 작음
- transition: else

### 4-3. 결정 필요 사항 (§7 옵션 송부 예정)

| 결정 | 옵션 |
|---|---|
| REGIME 방식 | A: rule-based / B: KMeans / C: HMM |
| NaN 처리 | A: fillna(0) / B: KNNImputer / C: row drop |
| feature | A: 16 axes / B: PCA / C: 선별 |

### 4-4. 예상 시간
- REGIME ~30분 / TRANSITION ~30분 / EDGE+TRADEABLE ~20분 / 비교 ~10분
- 합 ~90분

---

## 5. 다음 세션 진입 패키지

### 5-1. Setup cell

import os, subprocess, shutil, time, sys
from pathlib import Path

os.chdir('/content')
t0 = time.time()
REPO = '/content/choonsimi-msm'

from google.colab import userdata
GH = userdata.get('GH_TOKEN')
assert GH

if Path(REPO).exists():
    shutil.rmtree(REPO)
url = f'https://x-access-token:{GH}@github.com/stanleyim/choonsimi-msm.git'
r = subprocess.run(['git','clone',url,REPO], capture_output=True, text=True)
assert r.returncode==0, f'clone 실패: {r.stderr}'
os.chdir(REPO)

head = subprocess.run(['git','rev-parse','--short','HEAD'],
                      capture_output=True, text=True).stdout.strip()
print(f'HEAD={head}')

subprocess.run([sys.executable,'-m','pip','install','-q',
                'pyarrow','pandas','numpy','psutil','scikit-learn'], check=True)
import pandas as pd, numpy as np, psutil
from sklearn.preprocessing import RobustScaler
from sklearn.cluster import KMeans
from sklearn.impute import KNNImputer

for k in ['KRX_ID','KRX_PW','ECOS_API_KEY','KRX_API_KEY']:
    try:
        v = userdata.get(k)
        if v: os.environ[k] = v
    except: pass

subprocess.run(['git','config','user.email','msm@stanleyim.local'], check=True)
subprocess.run(['git','config','user.name','stanleyim'], check=True)

df = pd.read_parquet('data/state/axis_raw/axis_raw_v20.parquet')
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date').reset_index(drop=True)
print(f'axis_raw_v20: {df.shape}')
print(f'range: {df["date"].min().date()} ~ {df["date"].max().date()}')

mem = psutil.virtual_memory()
print(f'RAM free: {mem.available/1e9:.1f} GB')
print(f'준비 완료 {time.time()-t0:.1f}s')

### 5-2. 첫 메시지 (Claude에게)

MSM Phase 4 세션 #16.
HEAD = (v20 이후 갱신된 HEAD).

상태:
- axis_raw_v20.parquet (2309 rows, 21 cols)
- M17/M19/M16 anomaly 정책 LOCK
- raw + 3 flags 분리

다음 작업:
1. REGIME 분류 (rule-based 1차, ~30분)
2. TRANSITION (kNN, ~30분)
3. EDGE FIELD + TRADEABLE (~20분)
4. v4 vs v12 비교

§1 추측 X, §6 3축, §7 옵션→형 결정→실행, 단일 셀.
큰 결정만 옵션 송부, 기술 세부는 자체 판단 실행 후 보고.

먼저 Setup cell 검증 결과 송부.

---

## 6. 실수 누적 (v19 #69~#72 + v20 신규)

#73: 세션 #14 종료 시 CWD 정리 안 함 → 세션 #15 setup shutil.rmtree 시 deleted CWD 에러. 재발 방지: setup 최상단 os.chdir('/content') 의무.

#74: handoff v19 doc commit (660ccfd)이 v19 작성 시점보다 늦게 push됨 → EXPECTED_HEAD 불일치. 재발 방지: handoff 작성 직후 commit hash 기록.

#75: K3 sanity 시 M19 정의 미확인 상태로 freeze 진입 시도 → §1 위반. 재발 방지: 새 axis NaN/outlier 발견 시 build_axis.py source 직접 read 후 정의 확인.

#76: M16_expiry_flag 1차 (day 6~14) → 58/60 cover. 자의적 calendar 정의가 실제 데이터 분포 fit 부족. 재발 방지: flag 정의 = 데이터 분포로 검증.

#77: v20 handoff 작성 시 Python triple-quote 안에 긴 markdown content → SyntaxError. 재발 방지: 긴 doc 작성은 heredoc 또는 Path.write_text() 사용.

#78: %%writefile magic 사용 시 markdown 내부 백틱 코드블록이 truncate 유발 (98 lines만 저장됨). 재발 방지: heredoc bash 또는 raw string + Path.write_text() 사용.

---

## 7. 핵심 한 줄

v19 → v20: K3 9.4y backfill (fail 0) + anomaly 3건 raw 진단 완료 (M19 PCR / M17 거래단절 / M16 만기cluster) + STATE freeze (raw 무수정 + 3 flags). 다음 = REGIME 분류 진입.

---

## 8. 정직 메시지

진짜 가치:
1. K3 9.4y full fail 0 — v19 §11 risk 완전 해소
2. anomaly 전부 raw level 원인 규명 — §1 준수
3. STATE freeze 가역적 (raw 무수정, flag만 추가)
4. flag 정의 자체를 데이터 분포로 검증

남은 risk:
- REGIME NaN 처리 전략 미정
- KMeans/HMM 선택에 따른 결과 분산
- 2025 이후 M16 std 급감 → REGIME 학습 partition 영향 가능성

다음: REGIME 분류 → v21.

---

작성자: Claude (MSM 세션 #15, STATE freeze COMPLETE)
상태: v20 LOCK
다음 작업: v4 STEP 2 REGIME → STEP 3 TRANSITION → STEP 4 EDGE FIELD

끝.
