# MSM 핸드오프 v4 — Step F 완료, Step B 대기

**작성일**: 2026-06-02 (밤, 세션 종료 시점)
**대상 repo**: `stanleyim/choonsimi-msm`
**최신 commit**: `c6eb6ba` ("Step F: macro_10y.json ...")
**상태**: Notebook 1 + Universe + Macro 완료. Active 데이터 4종(B~E) 미수집.
**다음 작업 시점**: 내일 아침 (새 노트북 + 새 Colab 세션)

---

## 0. 절대 원칙 (변경 없음)

1. **§1 추측 금지** — 모르는 건 검증. 가정 X.
2. **§6 모든 응답 전 3번 정밀 검토** — 형 명령. 한 번 검토는 위반.
3. **§7 옵션 → 형 결정 → 실행** — 임의 진행 X.
4. **§13 데이터 백업** — 매 단계 commit/push. Colab 컨테이너는 휘발성.
5. **MSM = choonsimi-premium과 완전 독립** — 데이터/코드 공유 X.
6. **외부 검토자 3 원칙** — v10c 6/26까지 freeze.
7. **태블릿 사용** — 셀 단위 가이드 금지. 통합 1셀로.

---

## 1. commit history (최신)

```
c6eb6ba ← HEAD (NEW): Step F macro_10y.json (7시리즈, 10y)
53886b3  README.md 보강
4b55ffc  Delete README.md
f450605  Add handoff v3
a52bfd5  Active Universe v1 (1318 codes)
9674ee8  Notebook 3 skeleton
9cac8dc  Notebook 2 skeleton + handoff v2
... (이하 v3 §1 참조)
```

---

## 2. 파일 인벤토리 (정확, 2026-06-02 22:50 KST)

**총 35 파일.**

```
choonsimi-msm/
├── MSM_HANDOFF_2026_06_02.md       (v1)
├── MSM_HANDOFF_2026_06_02_v2.md    (v2)
├── MSM_HANDOFF_2026_06_02_v3.md    (v3)
├── MSM_HANDOFF_2026_06_02_v4.md    (v4, 이 문서 — push 필요)
├── README.md
├── msm_data_ingestion.ipynb        (Notebook 2, 셀 2-3 + 5 + 24-29 검증완료)
├── msm_data_supplement.ipynb       (Notebook 1)
├── msm_state_vector.ipynb          (Notebook 3, 골격만)
└── data/
    ├── raw/
    │   ├── vkospi_10y.parquet           ✓ 2,307행 (2017-01-02 ~ 2026-06-02)
    │   ├── vkospi_10y_merged.csv         (백업)
    │   ├── delisted/
    │   │   ├── ohlcv/year={2017..2026}.parquet  ✓ 289종목
    │   │   └── flow/year={2017..2026}.parquet   ✓ 285종목
    │   ├── macro/
    │   │   └── macro_10y.json           ✓ 459.9 KB, 7 시리즈 (★ NEW c6eb6ba)
    │   └── active/                       ❌ 미생성 (Step B~E 산출)
    ├── universe/
    │   └── universe_msm.csv             ✓ 1,318종목 (596 KOSPI + 722 KOSDAQ)
    ├── state/                            ❌ 미생성 (Notebook 3 산출)
    └── checks/
        ├── batch_progress.json
        ├── delisted_codes.json
        ├── delisted_excluded.json
        └── delisted_validation.json
```

---

## 3. macro_10y.json 명세 (★ NEW)

`data/raw/macro/macro_10y.json` — 459.9 KB.

```json
{
  "KOSPI200":  { "YYYY-MM-DD": close_value, ... },  // 2,307일
  "코스피":     { ... },                              // 2,307일 (key 한글)
  "코스닥":     { ... },                              // 2,307일
  "코스닥150":  { ... },                              // 2,307일
  "VKOSPI":    { ... },                              // 2,307일
  "USDKRW":    { ... },                              // 2,458일 (외환영업일)
  "BASE_RATE": { ... }                               // 3,439일 (매일, ITEM 0101000)
}
```

**Notebook 3 입력 시 주의**:
- KOSPI/KOSDAQ/KOSDAQ150는 한글 key. `macro["코스피"]` 식 접근.
- BASE_RATE는 매일 발표(D 주기) — forward-fill 불필요.
- 영업일 일치: 7시리즈 모두 약간 다름. 통합 시 master calendar (KOSPI 1001) 기준 reindex 필요.

---

## 4. Q1~Q10 확정 셋 (락, v3와 동일)

v3 §3 그대로 유효. 변경 없음.

---

## 5. State Vector 정의 (Notebook 3, v3 §4와 동일)

```
S_t = [r, v, f, σ, ℓ]

r     = log(close_t / close_{t-1})              # adjusted close
v     = log(trade_value_t / 60d_mean)            # raw trade_value
f     = (foreign_5d + inst_5d) / trade_value_5d  # 원 단위
σ     = std(r) over 20d
ℓ     = log10(trade_value_60d / 100억)
```

**Dual normalization** (CS + TS, v3 §4 그대로).

---

## 6. 데이터 인벤토리 vs 부족분 (★ 업데이트)

| 항목 | 보유 | 비고 |
|---|---|---|
| Universe (active) | ✓ 1,318종목 | — |
| Delisted OHLCV | ✓ 289종목 (adj) | raw 거래대금 = `close × volume` 근사 사용 |
| Delisted Flow | ✓ 285종목 (원) | — |
| **VKOSPI** | ✓ 10년 | macro_10y.json에 통합됨 |
| **KOSPI200** | ✓ | macro_10y.json |
| **KOSPI 종합** | ✓ | macro_10y.json |
| **KOSDAQ 종합** | ✓ | macro_10y.json |
| **KOSDAQ150** | ✓ | macro_10y.json |
| **USD/KRW** | ✓ | macro_10y.json |
| **한국 기준금리** | ✓ | macro_10y.json (ITEM 0101000) |
| **Active OHLCV adj** | ❌ | Notebook 2 Step B (다음 작업 1순위) |
| Active OHLCV raw | ❌ | Step C |
| Active Flow | ❌ | Step D |
| Active Foreign | ❌ | Step E |

---

## 7. 다음 작업 즉시 실행 가이드 (★ 최우선)

### 7-1. 새 세션 시작 — 첫 셀

Colab 새 노트북에 아래 **단일 셀** 붙여넣고 실행:

```python
# === 새 세션 setup ===
!git clone https://github.com/stanleyim/choonsimi-msm.git
%cd choonsimi-msm
!pip install -q pykrx pyarrow finance-datareader requests

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
print(f"KRX_ID: {bool(os.environ.get('KRX_ID'))}, ECOS: {bool(ECOS_KEY)}, GH: {bool(GH_TOKEN)}")

from pykrx import stock as krx
import FinanceDataReader as fdr

START = "20170101"
END   = datetime.now().strftime("%Y%m%d")
print(f"수집 기간: {START} ~ {END}")

ROOT = Path("data")
for d in ["raw/active/ohlcv_adj", "raw/active/ohlcv", "raw/active/flow",
          "raw/active/foreign", "raw/macro", "universe", "checks"]:
    (ROOT / d).mkdir(parents=True, exist_ok=True)

# Universe 로드
df_univ = pd.read_csv(ROOT / "universe" / "universe_msm.csv", encoding="utf-8-sig", dtype={"code": str})
df_univ["code"] = df_univ["code"].str.zfill(6)
codes = df_univ["code"].tolist()
BATCH_SIZE = 50
n_batches = (len(codes) + BATCH_SIZE - 1) // BATCH_SIZE
print(f"\n대상: {len(codes)}종목 → {n_batches} batches")

# progress 파일
progress_path = ROOT / "checks" / "active_progress.json"
if not progress_path.exists():
    with open(progress_path, "w") as f:
        json.dump({"completed_batches": []}, f)

# git config (push용)
!git config user.email "msm@stanleyim.local"
!git config user.name "stanleyim"
print("\nSetup 완료. Step B 시작 가능.")
```

**기대 출력:**
```
KRX_ID: True, ECOS: True, GH: True
수집 기간: 20170101 ~ 20260603
대상: 1318종목 → 27 batches
Setup 완료. Step B 시작 가능.
```

### 7-2. Step B 실행 — 단일 셀 (~54분)

```python
# === Step B: Active OHLCV adjusted 전체 수집 (1318종목, 27 batches) ===

def run_active_ohlcv_adj_batch(batch_num):
    start = batch_num * BATCH_SIZE
    end_idx = min(start + BATCH_SIZE, len(codes))
    batch_codes = codes[start:end_idx]
    rows, fail = [], []
    for code in batch_codes:
        try:
            df = krx.get_market_ohlcv(START, END, code, adjusted=True)
            if len(df) > 0:
                df = df.reset_index().rename(columns={
                    "날짜": "date", "시가": "open", "고가": "high", "저가": "low",
                    "종가": "close", "거래량": "volume", "등락률": "change_rate"
                })
                df["code"] = code.zfill(6)
                rows.append(df)
            else:
                fail.append((code, "0행"))
        except Exception as e:
            fail.append((code, str(e)[:60]))
        time.sleep(0.15)
    # 연도별 incremental 저장
    if rows:
        df_all = pd.concat(rows, ignore_index=True)
        df_all["date"] = pd.to_datetime(df_all["date"])
        df_all["year"] = df_all["date"].dt.year
        for year, df_y in df_all.groupby("year"):
            out = ROOT / "raw" / "active" / "ohlcv_adj" / f"year={year}.parquet"
            df_y_new = df_y.drop(columns=["year"])
            if out.exists():
                df_old = pd.read_parquet(out)
                df_y_new = pd.concat([df_old, df_y_new], ignore_index=True).drop_duplicates(
                    subset=["code", "date"], keep="last"
                )
            df_y_new.to_parquet(out, index=False)
        return {"batch": batch_num, "rows": len(df_all), "codes": df_all["code"].nunique(), "fail": fail}
    return {"batch": batch_num, "rows": 0, "codes": 0, "fail": fail}

# 자동 루프 (27 batches)
t_start = time.time()
results = []
all_fails = []
for b in range(n_batches):
    t_b = time.time()
    print(f"\n--- Batch {b+1}/{n_batches} ({datetime.now().strftime('%H:%M:%S')}) ---")
    try:
        r = run_active_ohlcv_adj_batch(b)
        results.append(r)
        # progress 업데이트
        with open(progress_path) as f:
            prog = json.load(f)
        prog["completed_batches"].append(b)
        prog["last_updated"] = datetime.now().isoformat()
        with open(progress_path, "w") as f:
            json.dump(prog, f, indent=2)
        all_fails.extend([(b, c, e) for c, e in r["fail"]])
        elapsed = time.time() - t_b
        total = (time.time() - t_start) / 60
        remain = elapsed * (n_batches - b - 1) / 60
        print(f"  ✓ {r['rows']}행 {r['codes']}종목 실패{len(r['fail'])} | "
              f"⏱{elapsed:.1f}s 경과{total:.1f}m 잔여{remain:.1f}m")
    except Exception as e:
        print(f"  ❌ Batch {b} 예외: {e}")

# 최종 검증
print(f"\n=== Step B 완료: {(time.time()-t_start)/60:.1f}분 ===")
import glob
files = sorted(glob.glob("data/raw/active/ohlcv_adj/year=*.parquet"))
total_rows = 0
all_codes = set()
for fp in files:
    df = pd.read_parquet(fp)
    total_rows += len(df)
    all_codes |= set(df["code"].unique())
    print(f"  {fp}: {len(df):>7}행, {df['code'].nunique()}종목")
print(f"\n총: {total_rows}행, {len(all_codes)}종목 / Universe 1318 = {100*len(all_codes)/len(codes):.1f}%")
print(f"실패 종목 수: {len(all_fails)}")
if all_fails[:5]:
    print("실패 샘플:")
    for b, c, e in all_fails[:5]:
        print(f"  batch{b} {c}: {e}")

# checks 저장
with open(ROOT / "checks" / "step_b_failures.json", "w") as f:
    json.dump([{"batch": b, "code": c, "error": e} for b, c, e in all_fails], f, ensure_ascii=False, indent=2)
```

### 7-3. Step B push 셀

```python
# === Step B push ===
import subprocess
token = userdata.get("GH_TOKEN")
origin_url = subprocess.run(["git", "remote", "get-url", "origin"], capture_output=True, text=True).stdout.strip()
auth_url = origin_url.replace("https://", f"https://{token}@")
!git remote set-url origin {auth_url}
!git add data/raw/active/ohlcv_adj/ data/checks/active_progress.json data/checks/step_b_failures.json
!git status --short
!git commit -m "Step B: Active OHLCV adjusted (1318 codes, 27 batches)"
!git push origin main
!git remote set-url origin {origin_url}
!git log -1 --oneline
```

### 7-4. 이후 (Step C/D/E/G + Notebook 3)

Step B 검증 통과 후 형 결정 받고 진행. 동일 패턴.

---

## 8. KRX 세션 만료 대응 (§9.10, 검증됨)

- KRX 인증 1시간 만료. pykrx 호출 도중 자동 감지 → 환경변수로 재로그인.
- 메시지: `"KRX 세션 만료, 재로그인 시도... KRX 세션 갱신 완료"`
- 환경변수만 살아있으면 형 개입 불필요.
- Step B ~54분 → 1시간 직전. 만료 발생 가능성 → 자동 재로그인 작동 확인.

---

## 9. 오늘 새 발견 (★ NEW, v3에 없음)

### 9-1. ECOS API ITEM_CODE 필수
**문제**: 통계표 722Y001 (한국은행 기준금리)에 **48개 ITEM** 존재. ITEM_CODE 미지정 → 응답 10,000 row 한도에서 절단되어 BASE_RATE가 2020-01-17에서 끊김.

**해결**:
```python
url = f"https://ecos.bok.or.kr/api/StatisticSearch/{ECOS_KEY}/json/kr/1/10000/722Y001/D/{START}/{END}/0101000"
                                                                                              # ↑ ITEM_CODE 끝에 추가
```

- `0101000` = 한국은행 기준금리 (Bank of Korea Base Rate)
- D 주기로 3,439일 수신 (10년 매일).
- 데이터 검증: 2017-01-01 = 1.25%, 2020-01-17 = 1.25, 2026-06-01 = 2.5%. ✓

### 9-2. FDR DataReader 날짜 인자 ISO 포맷 필수
**문제**: `fdr.DataReader("USD/KRW", "2017", "2026")` 호출 시 연도만 해석되어 2026-01-01에서 끊김.

**해결**: ISO 포맷 사용.
```python
start_dt = f"{START[:4]}-{START[4:6]}-{START[6:8]}"  # "2017-01-01"
end_dt   = f"{END[:4]}-{END[4:6]}-{END[6:8]}"        # "2026-06-02"
fx = fdr.DataReader("USD/KRW", start_dt, end_dt)
```

### 9-3. Colab Secrets 노트북 액세스 토글
**문제**: 새 노트북마다 Secrets 4개(KRX_ID/KRX_PW/ECOS_API_KEY/GH_TOKEN)의 **노트북 액세스 토글이 OFF**로 시작. 첫 호출에서 `TimeoutException: Requesting secret KRX_ID timed out` 발생.

**해결**: 좌측 🔑 아이콘 → 각 secret의 "노트북 액세스" 토글 ON. 1회 작업.

---

## 10. §10 매뉴얼 수정사항 누적 (v3 §10 + 신규)

### 10-1 ~ 10-4: v3 §10 그대로 유효
- §5.1 단위 정정 (Flow = 원)
- §6.1 지수 코드 (1001/1028/2001/2203/1330)
- §9.10 pykrx 자동 재인증
- Universe 6축 필터 약점

### 10-5. ECOS 통계표 호출 규칙 (★ NEW)
- 통계표 ID(722Y001 등) 외 **ITEM_CODE 명시 필수**.
- ITEM_CODE 목록 확인: `https://ecos.bok.or.kr/api/StatisticItemList/{KEY}/json/kr/1/100/{STAT_CODE}` 호출.
- 한국은행 기준금리 = `722Y001 + 0101000`.

### 10-6. FDR 날짜 포맷 (★ NEW)
- `fdr.DataReader(symbol, start, end)`: start/end **ISO 포맷** (`YYYY-MM-DD`).
- 연도만 전달 시 해당 연도 1월 1일로 해석되어 잘림.

---

## 11. 환경 설정 체크리스트 (★ 보강)

### Colab Secrets 필수
- ✓ `KRX_ID`
- ✓ `KRX_PW`
- ✓ `ECOS_API_KEY`
- ✓ `GH_TOKEN`

**★ 새 노트북마다 각 secret의 "노트북 액세스" 토글 ON 필요** (§9-3 참조).

### 패키지
```
pip install -q pykrx pyarrow finance-datareader requests
```

### git config (이전 세션 일관성)
```bash
git config user.email "msm@stanleyim.local"
git config user.name "stanleyim"
```

---

## 12. §8 실수 누적 (오늘 추가)

v3 §9 1~14번 그대로 유효. 오늘 추가:

15. **§6 3번 검토 또 미이행** — clone 명령을 두 가지로 해석 가능했는데 검증 없이 진행. 형이 "정신차려라" 지적.
16. **태블릿 환경 망각** — 셀별 가이드 반복. "셀 2 실행" 명령 후 "셀 3" 분리. 통합 1셀 원칙 위반.
17. **존재하지 않는 셀 가정** — 노트북 셀 자체가 비었을 가능성 검증 안 함. 형이 "셀을 줘" 지적.
18. **인증 토글 누락** — Colab Secrets 노트북 액세스 토글 안내 누락. 형의 첫 시도 실패 유발.
19. **추측으로 placeholder 채움** — git config user.email 검증 없이 "stanley@example.com" 둠. 다행히 push 전 git log로 실제 값 확인했지만 위험.

---

## 13. 다음 세션 시작 가이드

### 첫 메시지 권장 (형 → Claude)
```
MSM Notebook 2 Step B 실행 시작.
MSM_HANDOFF_2026_06_02_v4.md 참고.

현재:
- choonsimi-msm repo 최신 (HEAD = c6eb6ba, Step F 완료)
- macro_10y.json 7시리즈 ✓
- Universe 1318 + Delisted 285 ✓
- Notebook 2 셀 검증완료, Step B 자동 루프 셀 v4 §7-2 준비됨

다음:
- 7-1 Setup 셀 실행
- 7-2 Step B 자동 루프 실행 (~54분)
- 7-3 push

§1 추측 X, §6 3번 검토 매번, §7 옵션 → 형 결정 → 실행 준수.
태블릿 사용, 단일 셀 통합.
```

### Claude가 첫 응답에서 할 것
1. **v4 §0 절대 원칙 정독** (특히 §6 3번 검토 + 태블릿)
2. v4 §7 셀 코드 그대로 사용 — 단 §1 추측 X, 형 환경 확인 후 진행
3. Setup 셀 출력 받아 검증 (KRX/ECOS/GH 모두 True, 1318 / 27 batches)
4. 형 GO 받으면 Step B 자동 루프 시작
5. 결과 검증 + push

---

## 14. 핵심 한 줄

> "Step F까지 완료. 다음은 Step B (Active OHLCV adj, 1318종목, ~54분, 단일 자동 루프 셀 §7-2)."

---

## 15. 미반영 사항 (인계서 push 필요)

- 이 문서(`MSM_HANDOFF_2026_06_02_v4.md`)는 작성만 됨. **repo push 별도 필요**.
- 형 의향: 새 세션에서 첫 셀 setup 후 인계서 push 또는 형 수동 업로드.

---

**작성자**: Claude (MSM 세션 #2 어시스턴트)
**상태**: 데이터 수집 55% (Macro 추가 완료, Active 4종 미수집)
**다음 작업**: Notebook 2 Step B (Active OHLCV adjusted)
**우선순위**: §6 3번 검토 + 태블릿 단일셀 + §1 추측 X

끝.
