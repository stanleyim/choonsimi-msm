# MSM 핸드오프 v23 — v4 종결 + v5 설계 패키지

**작성일**: 2026-06-09 (KST, MSM 세션 #16 종결)
**대상 repo**: stanleyim/choonsimi-msm
**상태**: ★ v4 PIPELINE FULL END (실패 진단 완료). v5 설계 진입 준비.
**다음 작업**: v5 STEP 1 — Rolling distribution estimation POC

---

## 0. 절대 원칙 (v19~v20 §0 동일 + v23 신규)

1. §1 추측 금지
2. §6 3번 검토 (정확성 + 사고 가능성 + 안전장치)
3. §7 옵션 → 형 결정 → 실행
4. §13 매 단계 commit/push
5. 단일 셀 통합 코드
6. **v23 신규**: 통계적 검증 결과 (silhouette / tstat 등) 단독으로 신뢰 금지. 시계열 분포 + 모델 가정과 함께 다층 검증.

---

## 1. v4 결과 — 종결 보존 (재사용 금지)

### 1-1. STATE (LOCK 유지)
- `data/state/axis_raw/axis_raw_v20.parquet` — 2309 rows, 21 cols
- M17_missing=470, M19_missing=331, M16_expiry_flag=256
- **v5에서도 동일 입력으로 사용**

### 1-2. REGIME — ★ 실패
- v20: 97% R=0 dominance (outlier cluster)
- v21: log-sign + M16 winsorize + Robust, 51/3/35/11 → label instability + temporal bias
- v22: feature 축소 (10), 4/0.2/93/3 → outlier dominance 재발
- **공통 원인**: KMeans static / Euclidean / hard cluster + market non-stationarity

### 1-3. TRANSITION — 부속 폐기
- v21 위에 구축 → π 안정, mixing 5.95d
- 단 base regime invalid → 의미 무효

### 1-4. EDGE — ★ 실패 (temporal artifact)
- R1 hold 6d tstat 4.55 (Bonferroni 통과)
- **단 R1=77 dates 전부 2026 cluster (coverage 10%)**
- in-sample fit, OOS 신뢰 불가

### 1-5. TRADEABLE — ★ 실패 (B&H 미달)
- KOSPI R2 hold3d: Sharpe 0.510 / CAGR 5.93%
- KQ150 R3 hold1d: Sharpe 0.737 / CAGR 10.10%
- Combined: Sharpe 0.798 / CAGR 8.38%
- **B&H KOSPI**: Sharpe 0.829 / CAGR 16.43% (전 전략 미달)
- v12 LOCK: Sharpe 0.686 / CAGR 16.48% (참고)

### 1-6. TEMPORAL VALIDATION (STEP 6)
- Train 2017-2024 / Test 2025-2026 split
- v21 vs OOS train agreement: 2.44% (random 25% 미만)
- → clustering solution 자체가 non-identifiable
- → label permutation 문제가 아니라 cluster structure 본질 불안정

---

## 2. v4 실패 원인 — 구조적 결론

**문제의 본질**: S_t → R_t mapping이 time-invariant function이 아니다

**근거:**
1. R1 (SHOCK) 77 dates 전부 2026년 → stationarity 가정 붕괴
2. v21 R3 (TRANSITION) OOS에서 소멸 → cluster geometry 불안정
3. train fit reproducibility 2.44% → solution 자체가 unstable

**가정 실패:**
- v4 = "시장 regime은 stationary, 시간 무관 partition으로 정의 가능"
- 실제: 시장 regime은 시간 의존 + 분포 변동

---

## 3. v5 설계 (LOCK)

### 3-1. 4 핵심 수정

| 수정 | v4 (실패) | v5 |
|---|---|---|
| 1 | Global KMeans | Rolling window |
| 2 | Euclidean distance | Distributional likelihood |
| 3 | Hard cluster R∈{0,1,2,3} | Soft P(R\|S) |
| 4 | Time-invariant μ_k | Adaptive μ_k(t) |

### 3-2. 새 Pipeline

```
S_t (v20 LOCK 유지)
→ Rolling embedding (window W)
→ Adaptive regime (density / likelihood)
→ Transition operator in probability space
→ Continuous expected return surface
→ Soft tradeable region
```

### 3-3. STEP 별 정의

**STEP 1: STATE (LOCK 유지)**
- 입력: axis_raw_v20.parquet
- 변환: 없음 (v20 그대로)
- 출력: S_t (LOCK)

**STEP 2: REGIME (재정의 핵심)**
- 입력: S_{t-W:t}
- 변환:
  - (a) Rolling Window Density Estimation
    - window W: 60d / 120d 후보 (POC에서 결정)
    - 각 cluster k: μ_k(t), Σ_k(t) 추정
  - (b) Likelihood 기반 soft assignment
    - P(R=k | S_t) ∝ N(S_t | μ_k(t), Σ_k(t))
- 출력: R_t = [p1, p2, p3, p4] (soft vector)

**STEP 3: TRANSITION**
- 입력: R_t (soft), R_{t+1}
- 변환:
  - 기존 hard transition matrix 폐기
  - v5: E[R_{t+1} | R_t]
  - 또는 continuous-state transition: P(R_{t+1} | R_t) ≈ linear/kernel regression
- 출력: Transition operator in probability space

**STEP 4: EDGE FIELD**
- 입력: (R_t, Δprice_{t+1:t+H})
- 변환:
  - Expected return: E[r | R_t] = Σ_k p_k * μ_return_k
  - horizon별 surface: H ∈ {1d, 3d, 5d, 10d}
- 출력: continuous expected return surface

**STEP 5: TRADEABLE REGION**
- 입력: Edge surface
- 변환:
  - E[r] > 0
  - t-stat > threshold
  - stability over rolling OOS
- 출력: Soft region filter

### 3-4. POC (다음 세션 첫 실행)

**POC 1: Rolling μ, Σ 추정 안정성 검증**

1. window 후보 비교: W1=60 / W2=120
2. 각 t에서: μ(t), Σ(t) 추정
3. 검증: μ drift magnitude / Σ condition number / regime separability (Mahalanobis)

**출력:** rolling parameter stability report + W 선택 결정

---

## 4. 보존 파일

```
data/state/axis_raw/axis_raw_v20.parquet          ★ v5 입력 (LOCK)
data/raw/index/kospi_kq150_94y.parquet            ★ return source (재사용)
data/state/regime/regime_v4_step2*.parquet        × v4 폐기 (참조용)
data/state/transition/*.parquet                    × v4 폐기 (참조용)
data/state/edge_v4/*.parquet                       × v4 폐기 (참조용)
data/state/tradeable_v4/*.parquet                  × v4 폐기 (참조용)
data/state/temporal_validation/*.parquet           × v4 진단 결과 (참조용)
```

---

## 5. 다음 세션 (#17) 진입 패키지

### 5-1. Setup cell

다음 세션에서 그대로 실행. EXPECTED_HEAD_PREFIX는 본 핸드오프 commit hash로 교체 필요.

```
import os, subprocess, shutil, time, sys
from pathlib import Path

os.chdir('/content')
t0 = time.time()
REPO = '/content/choonsimi-msm'
EXPECTED_HEAD_PREFIX = '__v23_commit_hash__'

from google.colab import userdata
GH = userdata.get('GH_TOKEN')
assert GH

if Path(REPO).exists():
    shutil.rmtree(REPO)
url = 'https://x-access-token:' + GH + '@github.com/stanleyim/choonsimi-msm.git'
r = subprocess.run(['git','clone',url,REPO], capture_output=True, text=True)
assert r.returncode == 0
os.chdir(REPO)

head = subprocess.run(['git','rev-parse','--short','HEAD'], capture_output=True, text=True).stdout.strip()
assert head.startswith(EXPECTED_HEAD_PREFIX)
print('HEAD=' + head)

subprocess.run([sys.executable,'-m','pip','install','-q',
                'pyarrow','pandas','numpy','psutil','scikit-learn','scipy'], check=True)
import pandas as pd, numpy as np, psutil
print('packages ready')

for k in ['KRX_ID','KRX_PW','ECOS_API_KEY','KRX_API_KEY']:
    try:
        v = userdata.get(k)
        if v: os.environ[k] = v
    except Exception: pass

subprocess.run(['git','config','user.email','msm@stanleyim.local'], check=True)
subprocess.run(['git','config','user.name','stanleyim'], check=True)

df = pd.read_parquet('data/state/axis_raw/axis_raw_v20.parquet')
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date').reset_index(drop=True)
assert df.shape == (2309, 21)
print('axis_raw_v20: ' + str(df.shape))

mem = psutil.virtual_memory()
print('RAM free: ' + str(round(mem.available/1e9, 1)) + ' GB')
print('준비 완료 ' + str(round(time.time()-t0, 1)) + 's')
```

### 5-2. 첫 메시지 (Claude에게)

```
MSM Phase 4 세션 #17 (v5 진입).
HEAD = (v23 commit hash).

상태:
- v4 종결 (STATE/REGIME/TRANSITION/EDGE/TRADEABLE 전 단계 실패 진단 완료)
- STATE (v20) LOCK 유지
- v5 4 수정안 LOCK: rolling / distributional / soft / adaptive

다음 작업: v5 STEP 1 — Rolling μ, Σ 추정 POC
- W1=60 / W2=120 비교
- μ drift / Σ condition number / Mahalanobis separability

§1 추측 X, §6 3축, §7 옵션→형 결정→실행, 단일 셀.

먼저 Setup cell 검증 결과 송부.
```

---

## 6. 본 세션 (#16) commit 이력

- 4a14ac0 (v20 base, 세션 시작 HEAD)
- v4 STEP 2 v20: outlier dominance (97% R=0)
- v4 STEP 2 v21: log-sign + M16 winsorize + Robust
- v4 STEP 2 v22: feature 축소 → outlier 재발
- v4 STEP 3: transition matrix + π + mixing 5.95d
- v4 STEP 4.1: pykrx KOSPI+KOSDAQ150 9.4y
- v4 STEP 4: EDGE atomic + hold + pair
- v4 STEP 5: TRADEABLE backtest (B&H 미달)
- v4 STEP 6: TEMPORAL VALIDATION (label instability 발견)
- v23 핸드오프 (본 commit)

---

## 7. ★ 실수 누적 (v19~v22 #69~#78 + v23 신규 #79~#83)

**#79: STEP 6 Hungarian label matching 비대칭 confusion에서 cluster 1개 누락**
- v21 R=1 (test 전속) → train confusion에 row 부재 → 3×4 matrix → linear_sum_assignment가 3 cluster만 매핑
- OOS R=0 217 rows 통계 손실
- 재발 방지: cluster 매핑 시 정사각 confusion 보장. label_map size assert == n_clusters.

**#80: 자동 판정 변수 의미 오역**
- "CASE 2 VALID" 출력의 R1이 v21 R1(SHOCK 2026 100%)이 아니라 remapped slot
- 1차 단정 송부 시도 → 형 "추측하지 말고 냉정 검토" 지적으로 회피
- 재발 방지: 자동 판정 변수의 의미 정의를 print에서 함께 출력.

**#81: 통계적 유의성 (tstat 4.55, Bonferroni 통과) 단독 신뢰 실패**
- R1 hold 6d edge가 strict threshold 통과했으나 시계열 분포 확인 시 100% 2026 cluster
- 재발 방지: tstat 보고 시 시계열 분포 (연도별 count, cluster 길이) 자동 산출 의무.

**#82: Stationarity 가정 미검증 진입**
- KMeans 적용 전 "regime은 stationary" 가정 명시적 검증 없이 진행
- 재발 방지: clustering 모델 진입 시 가정 명시 + sanity test (rolling fit reproducibility) 의무.

**#83: Python triple-quoted string 안에 f-string 포함 → SyntaxError (2회 연속)**
- v23 핸드오프 작성 1차: Path.write_text() 채택했으나 본문 내부 f'...' 가 외부 트리플 quote 종료 인식 방해
- v23 핸드오프 작성 2차: bash heredoc을 Python string 안에 래핑 → 동일 문제
- v22 #77/#78 패턴 반복
- 재발 방지: 긴 markdown 문서는 **create_file 도구로 직접 작성** 후 형 업로드 또는 별도 commit. Python 내 string으로 절대 처리 안 함.

---

## 8. 핵심 한 줄

v4 = correct structure × false assumption (stationarity).
v5 = rolling + distributional + soft + adaptive 로 가정 자체 교체.
v4 가 잘못된 게 아니라 잘못된 가정을 정확히 제거한 상태.

---

## 9. 정직 메시지

**본 세션 진짜 가치:**
1. v4 full pipeline 완주 + 각 단계 §6 검토 충실
2. "tstat 4.55 + Bonferroni 통과"의 temporal artifact 진단 — 시스템 신뢰성 핵심 위협 회피
3. label instability 발견 (agreement 2.4% << random 25%) — clustering 모델 한계 정량 확인
4. v4 가정 (stationarity) 자체 실패 인식 — v5 방향 명확화

**남은 risk:**
- v5 rolling window 자체도 W 선택, regularization 등 hyperparameter 존재
- soft assignment + transition operator 가 hard regime + matrix 보다 backtest 평가 복잡
- POC 단계에서 W 선정 잘못 시 v5도 동일 함정

**v5 진입 조건:**
- POC stability report 통과 시만 STEP 2 진입
- 통과 못 하면 W 재선정 또는 모델 family 재검토 (GMM / HDP / Dirichlet process)

---

**작성자**: Claude (MSM 세션 #16, v4 종결 + v5 설계)
**상태**: v4 LOCK 종료. v5 LOCK 시작.
**다음 작업**: v5 POC 1 (Rolling μ/Σ stability).

끝.
