# MSM 작업 계획서 v1

**작성일**: 2026-06-07 (KST, MSM 세션 #10 종결 시점)
**대상 repo**: stanleyim/choonsimi-msm
**기준 핸드오프**: MSM_HANDOFF_2026_06_07_v15.md
**기준 commit**: 92b047f (v13 핸드오프 commit)

---

## 0. 작업 계획 원칙

1. 각 작업 = 단일 셀 단위로 실행 가능해야 함 (태블릿 환경)
2. 각 작업 = 명확한 산출물 + 검증 기준 + 의존성 + 예상 시간 명시
3. 작업 순서 = 의존성 따라 sequential (병렬 시 명시)
4. 모든 데이터 작업 = batch push 의무 (v13 #51)
5. 모든 alpha 작업 = 단일 축 순차 검증 (ΔSharpe ≥ +0.05 채택)
6. §1 추측 X / §6 3축 검토 / §7 옵션 → 형 결정 → 실행
7. blocked 시 unblock 후보 능동 제시 (v15 #14)

---

## 1. 전체 진행 일정 (요약)

| Phase | 내용 | 예상 세션 | 예상 시간 |
|---|---|---|---|
| Phase 2.A | KRX OpenAPI 4축 확장 (basis/PCR/ETF/yield) | 1~2 | 4~6시간 |
| Phase 2.B | US 10Y + state v3+ 통합 + ΔSharpe 검증 | 1 | 2~3시간 |
| Phase 2.5 | Forward Test 누적 (daily routine) | 지속 | 1~2주 |
| Phase 3 | 12008 web scraping (시장 분리 flow) | 1 | 2~3시간 |
| Phase 4 | choonsimi-premium 6/26 비교 + dual-engine 검토 | 1~2 | 6월 26일 이후 |
| Phase 5 | v3+ LOCK 또는 STEP 9 (state v4) 결정 | 1 | 3개월 후 |

---

## 2. Phase 2.A — KRX OpenAPI 4축 확장 (basis + PCR + ETF + yield)

### 2.A.1 — 형 portal 4 endpoint 신청 (오프라인)

**작업**:
- portal (openapi.krx.co.kr) → 각 endpoint 페이지 → "API 이용신청" 클릭
- 4개 신청:
  1. 선물 일별매매정보 (drv/fut_bydd_trd) — basis + OI
  2. 옵션 일별매매정보 (drv/opt_bydd_trd) — PCR + IV
  3. ETF 일별매매정보 (etp/etf_bydd_trd) — ETF + sector
  4. 국채전문유통시장 (bon/kts_bydd_trd) — yield curve (선택)

**의존성**: 없음
**예상 시간**: 5분 (즉시 승인 패턴 확인됨)
**검증**: portal "마이페이지 → API 이용현황" 에 4 endpoint "승인" 상태
**담당**: 형 (오프라인)
**Blocker**: 없음

---

### 2.A.2 — Smoke v4 (header + 신청 완료 검증)

**작업**: 단일 셀 실행
- 이미 승인된 sto/stk_bydd_trd 로 header (Apikey 추정) 확정
- 신규 4 endpoint 200 응답 확인

**셀 구조**:
```python
import requests
BASE = 'https://data-dbg.krx.co.kr/svc/apis'
TEST_DATE = '20260605'  # 또는 dates_94y[-1]

# Step 1: header 확정 (sto/stk_bydd_trd 사용)
for hname in ['Apikey', 'AUTH_KEY', 'apikey']:
    r = requests.get(f'{BASE}/sto/stk_bydd_trd',
                     params={'basDd': TEST_DATE},
                     headers={hname: KRX_API_KEY})
    if r.status_code == 200:
        WORKING_HEADER = {hname: KRX_API_KEY}
        break

# Step 2: 신규 4 endpoint 검증
for ep in ['drv/fut_bydd_trd', 'drv/opt_bydd_trd', 'etp/etf_bydd_trd', 'bon/kts_bydd_trd']:
    r = requests.get(f'{BASE}/{ep}', params={'basDd': TEST_DATE}, headers=WORKING_HEADER)
    # status == 200 + len(OutBlock_1) > 0 → 신청 완료
```

**의존성**: 2.A.1 (4 endpoint 신청 완료)
**예상 시간**: 1분
**산출물**: WORKING_HEADER 변수 (다음 작업 사용)
**검증**:
- status 200
- OutBlock_1 에 rows 존재
- 5개 endpoint (sto + 4 신규) 모두 PASS
**Blocker**: header 3 후보 모두 fail → KRX 가이드 PDF 또는 portal "API 이용신청" 페이지의 example 확인

---

### 2.A.3 — basis (fut_bydd_trd) 9.4y bulk fetch

**작업**: 단일 셀 (batch push 의무)
- 2017-01-02 ~ 2026-06-02 (2307 영업일)
- df_sv_v2['date'].unique() 활용 (v12 calendar)
- API rate limit 보수적 (time.sleep(0.15))
- 100 batches 마다 git push

**셀 구조**:
```python
DATES = sorted(df_sv_v2['date'].dt.strftime('%Y%m%d').unique())
OUT = Path('data/raw/openapi/basis_10y.parquet')
BATCH = 100

accumulated = []
t_start = time.time()
for i, date in enumerate(DATES):
    r = requests.get(f'{BASE}/drv/fut_bydd_trd',
                     params={'basDd': date},
                     headers=WORKING_HEADER, timeout=15)
    if r.status_code == 200:
        rows = r.json().get('OutBlock_1', [])
        accumulated.extend(rows)
    if (i+1) % BATCH == 0:
        pd.DataFrame(accumulated).to_parquet(OUT)
        # git add + commit + push
        subprocess.run(['git','add', str(OUT)], cwd=REPO)
        subprocess.run(['git','commit','-m',f'basis batch {(i+1)//BATCH}'], cwd=REPO)
        subprocess.run(['git','push'], cwd=REPO)
        elapsed = time.time() - t_start
        eta = elapsed * (len(DATES)-i-1) / (i+1)
        print(f'{i+1}/{len(DATES)} elapsed={elapsed:.0f}s ETA={eta:.0f}s')
    time.sleep(0.15)
# 최종 저장
pd.DataFrame(accumulated).to_parquet(OUT)
```

**의존성**: 2.A.2 (WORKING_HEADER)
**예상 시간**: ~6분 (2307 × 0.15s + 처리)
**산출물**: `data/raw/openapi/basis_10y.parquet` (~12k rows)
**검증**:
- shape > (10000, 15) 정도
- date 분포 = 2307 일 모두
- columns = BAS_DD/PROD_NM/MKT_NM/ISU_CD/ISU_NM/TDD_CLSPRC/CMPPREVDD_PRC/TDD_OPNPRC/TDD_HGPRC/TDD_LWPRC/SPOT_PRC/SETL_PRC/ACC_TRDVOL/ACC_TRDVAL/ACC_OPNINT_QTY
- KOSPI 200 선물 product 존재 (PROD_NM 또는 ISU_NM 으로 식별)
**Blocker**:
- rate limit (429) → time.sleep 증가
- network 끊김 → resume from last batch (already-saved 활용)

---

### 2.A.4 — PCR + IV (opt_bydd_trd) 9.4y bulk fetch

**작업**: 단일 셀 (batch push)
- 같은 패턴, endpoint = opt_bydd_trd

**의존성**: 2.A.2
**예상 시간**: ~6분 (단 row 수 더 많음 ~115k)
**산출물**: `data/raw/openapi/pcr_10y.parquet` (~115k rows)
**검증**:
- columns = ... RGHT_TP_NM (CALL/PUT) ... IMP_VOLT ...
- RGHT_TP_NM 분포 = CALL ~50% / PUT ~50%
- IMP_VOLT 값 정상 (0.1 ~ 1.0 range)
**Blocker**: 동일

---

### 2.A.5 — ETF (etf_bydd_trd) 9.4y bulk fetch

**작업**: 단일 셀 (batch push)
- 데이터 크기 가장 큰 endpoint

**의존성**: 2.A.2
**예상 시간**: ~10분 (~1.4M rows, 종목 ~600 ETFs × 2307 days)
**산출물**: `data/raw/openapi/etf_10y.parquet` (~1.4M rows, 추정 ~150MB)
**검증**:
- columns = ... IDX_IND_NM (기초지수명) ...
- IDX_IND_NM nunique > 50 (sector 분류 가능)
- NAV / TDD_CLSPRC 값 정상
**Blocker**:
- 메모리 부담 → 만약 시 batch 별 parquet split 후 통합

---

### 2.A.6 — KTS (kts_bydd_trd) 9.4y bulk fetch (선택)

**작업**: 단일 셀 (batch push)

**의존성**: 2.A.2
**예상 시간**: ~6분 (~350k rows, 종목 ~150 bonds)
**산출물**: `data/raw/openapi/kts_10y.parquet`
**검증**:
- columns = ... BND_EXP_TP_NM (만기년수) ... CLSPRC_YD (수익률) ...
- BND_EXP_TP_NM 분포 = 3Y, 5Y, 10Y, 30Y 등
**Blocker**: 동일

**선택 사유**: yield curve = 외부 anchor proxy, marginal alpha 가능성 있지만 우선순위 4순위

---

## 3. Phase 2.B — US 10Y + state v3+ 통합 + ΔSharpe 검증

### 3.B.1 — US 10Y Treasury yield fetch

**작업**: 단일 셀
- Option A (★ 권장): FDR (FinanceDataReader)
  ```python
  import FinanceDataReader as fdr
  us10y = fdr.DataReader('US10YT=X', '2017-01-01', '2026-06-07')
  ```
- Option B: ECOS API (해외통계 → 미국 시장금리 → 10년물)
  ```python
  # 정확한 stat code 검증 필요 (KRX_ID/PW 또는 ECOS_API_KEY)
  ```

**의존성**: 없음 (2.A 와 병렬 가능)
**예상 시간**: 1분
**산출물**: `data/raw/macro/us10y_10y.parquet` (date, yield)
**검증**:
- 2307 days coverage
- yield 값 정상 (1~5% range)
- 미국 영업일 ≠ 한국 영업일 → KOSPI date 에 맞춰 join 시 일부 NaN forward-fill 필요
**Blocker**:
- FDR yahoo 의존성 → ECOS fallback
- ticker 명 불일치 → 'US10YT=X' / 'TNX' / '^TNX' 후보 시도

---

### 3.B.2 — basis state axis 계산

**작업**: 단일 셀
- KOSPI 200 선물 active contract 식별
- basis = TDD_CLSPRC - SPOT_PRC
- z_basis = zscore(basis, rolling=252)

**셀 구조**:
```python
fut = pd.read_parquet('data/raw/openapi/basis_10y.parquet')
# KOSPI 200 active contract = ISU_NM 에 "KOSPI 200" 포함 + 가장 빠른 만기 + ACC_TRDVOL 가장 큰
fut['date'] = pd.to_datetime(fut['BAS_DD'])
kospi200 = fut[fut['ISU_NM'].str.contains('KOSPI 200', na=False)]
# active contract 선정 logic (만기/거래량 기준)
active = kospi200.groupby('date').apply(select_active_per_day).reset_index(drop=True)
active['basis'] = active['TDD_CLSPRC'].astype(float) - active['SPOT_PRC'].astype(float)
active['z_basis'] = (active['basis'] - active['basis'].rolling(252).mean()) / active['basis'].rolling(252).std()

# OI change
active['oi_change'] = active['ACC_OPNINT_QTY'].astype(float).diff()
active['z_oi_change'] = zscore_rolling(active['oi_change'], 252)
```

**의존성**: 2.A.3
**예상 시간**: 5분 (계산) + 5분 (검증)
**산출물**: `data/state/v3_plus/basis.parquet` (date, basis, z_basis, oi_change, z_oi_change)
**검증**:
- 2307 days
- z_basis 분포 (mean ≈ 0, std ≈ 1)
- basis 값 = ±수십 ~ 수백 (지수 포인트)

---

### 3.B.3 — PCR + IV skew state axis 계산

**작업**: 단일 셀
- KOSPI 200 옵션 row only
- PCR = sum(TRDVOL @ PUT) / sum(TRDVOL @ CALL)
- IV skew: ATM strike 식별 + put_iv - call_iv

**셀 구조**:
```python
opt = pd.read_parquet('data/raw/openapi/pcr_10y.parquet')
opt['date'] = pd.to_datetime(opt['BAS_DD'])

# PCR (전체 거래량 기준)
pcr_daily = opt.groupby(['date', 'RGHT_TP_NM'])['ACC_TRDVOL'].sum().unstack()
pcr_daily['pcr'] = pcr_daily['PUT'] / pcr_daily['CALL']
pcr_daily['z_pcr'] = zscore_rolling(pcr_daily['pcr'], 252)

# IV skew (ATM 식별)
# ATM = strike 가 spot 에 가장 가까운 strike
# spot = fut_bydd_trd.SPOT_PRC 활용 (또는 KOSPI200 index 직접)
# put_iv_atm - call_iv_atm = skew
# 구현: ISU_NM 또는 별도 column 에서 strike 추출 필요

# IV term structure (선택)
# 단기 만기 vs 장기 만기 IV 차이
```

**의존성**: 2.A.4, 2.A.3 (spot 가격 위해)
**예상 시간**: 15분 (ATM 식별 로직 까다로움)
**산출물**: `data/state/v3_plus/pcr_iv.parquet` (date, pcr, z_pcr, iv_skew, z_iv_skew)
**검증**:
- z_pcr / z_iv_skew 분포
- PUT/CALL row 수 균형
**Blocker**:
- ATM strike 식별 로직 불명확 → ISU_NM 파싱 필요 (예: "KOSPI200 P 200708 380" 형식)

---

### 3.B.4 — ETF sector flow state axis 계산

**작업**: 단일 셀
- IDX_IND_NM 패턴 매칭으로 sector 분류
- sector_flow = sum(ACC_TRDVAL) per sector per day

**셀 구조**:
```python
etf = pd.read_parquet('data/raw/openapi/etf_10y.parquet')
etf['date'] = pd.to_datetime(etf['BAS_DD'])

SECTOR_PATTERNS = {
    'semi':       r'반도체|Semi',
    'finance':    r'금융|은행|증권',
    'dividend':   r'배당|Dividend',
    'growth':     r'성장|Growth',
    'value':      r'가치|Value',
    'consumer':   r'소비|Consumer',
    'bio':        r'바이오|헬스|Bio|Health',
    'auto':       r'자동차|Auto',
    'reit':       r'리츠|REITs',
    'large':      r'대형|Large',
    # 기타: 추가 필요
}

def classify(idx_name):
    if pd.isna(idx_name): return 'other'
    for sector, pat in SECTOR_PATTERNS.items():
        if re.search(pat, idx_name, re.IGNORECASE):
            return sector
    return 'other'

etf['sector'] = etf['IDX_IND_NM'].apply(classify)
sector_flow = etf.groupby(['date','sector'])['ACC_TRDVAL'].sum().unstack()
# zscore per sector
sector_z = sector_flow.apply(lambda s: zscore_rolling(s, 252))
```

**의존성**: 2.A.5
**예상 시간**: 20분 (sector pattern 설정 + 검증)
**산출물**: `data/state/v3_plus/etf_sector.parquet` (date × sector matrix)
**검증**:
- sector 별 row 수 (other 가 너무 많으면 pattern 재정의)
- sector_flow 시계열 연속성
**Blocker**:
- IDX_IND_NM 패턴 다양 → 초기 'other' 비중 50%+ 가능, pattern iterative 추가

---

### 3.B.5 — yield curve state axis 계산 (선택, kts 신청 시)

**작업**: 단일 셀
- 만기별 (3Y/5Y/10Y/30Y) average yield
- yield_3y_10y_spread = yield_10y - yield_3y

**의존성**: 2.A.6
**예상 시간**: 10분
**산출물**: `data/state/v3_plus/yield_curve.parquet`
**검증**:
- 만기별 column 정상 (3Y/5Y/10Y/30Y)
- spread 값 정상

---

### 3.B.6 — state_vector_v3+ 통합

**작업**: 단일 셀
- df_sv_v2 (기존 v12) + v3 (VIX/SOX/flow) + v3+ (basis/PCR/ETF/yield/US10Y) 통합
- date 기준 left join (df_sv_v2 universe × 2307 days × 26 columns 유지 + 새 columns 추가)

**셀 구조**:
```python
df_sv_v2  # (2793837, 26) — v12 LOCK
# load v3 (already in some form, may need recomputation)
# load v3+ new axes
basis_df = pd.read_parquet('data/state/v3_plus/basis.parquet')
pcr_df = pd.read_parquet('data/state/v3_plus/pcr_iv.parquet')
sector_df = pd.read_parquet('data/state/v3_plus/etf_sector.parquet')
us10y_df = pd.read_parquet('data/raw/macro/us10y_10y.parquet')
# (kts_df = ...)

# merge on date
df_sv_v3plus = df_sv_v2.copy()
df_sv_v3plus = df_sv_v3plus.merge(basis_df[['date','z_basis','z_oi_change']], on='date', how='left')
df_sv_v3plus = df_sv_v3plus.merge(pcr_df[['date','z_pcr','z_iv_skew']], on='date', how='left')
# sector columns: z_etf_sector_semi, z_etf_sector_finance, ...
# us10y: z_us10y
```

**의존성**: 3.B.1~3.B.5 모두
**예상 시간**: 15분
**산출물**: `data/state/state_vector_v3plus/year=*.parquet`
**검증**:
- shape = (2793837, 26 + N) where N = 신규 columns
- 결측값 비율 < 5% (초기 252일 rolling window 제외)
- date 분포 동일 (2307 days)

---

### 3.B.7 — 단일 축 순차 ΔSharpe 검증

**작업**: 단일 셀 (반복, 축 별)
- v12 LOCKED config 그대로
- state_vector 만 v3+ 사용
- 각 신규 축을 selection rule 에 1개씩 추가 시도
- ΔSharpe ≥ +0.05 시 채택

**순서** (v15 §5-6 기준):
1. z_basis
2. z_iv_skew (학술 가장 강력)
3. z_pcr
4. z_oi_change
5. z_etf_sector_* (각 sector)
6. z_us10y
7. z_yield_3y_10y_spread (선택)

**각 축 별 셀**:
```python
# Test axis = z_basis
# v12 LONG selection: NEUTRAL × bot z_ell top 10
# Test: NEUTRAL × bot (z_ell + 0.5 * z_basis) top 10 (또는 다른 결합 방식)
# or: NEUTRAL & z_basis < -1.5 (regime 필터로 추가) × bot z_ell top 10

# backtest 9.4y full
# CAGR, Sharpe, MDD 측정
# ΔSharpe = Sharpe_v3plus - Sharpe_v12LOCK (0.686)
```

**의존성**: 3.B.6
**예상 시간**: 30분 (축 별 5분 × 7축)
**산출물**: `data/sim/v3_plus/{axis_name}.parquet` 각 시뮬, `data/sim/v3_plus_summary.parquet`
**검증**:
- 단일 축 추가 시 v12 LOCK 결과 재현 (sanity check)
- ΔSharpe 분포
- 채택 축 list
**채택 기준**:
- ΔSharpe ≥ +0.05
- MDD 악화 ≤ +5%p
- in-sample + OOS 일관성 확인

---

### 3.B.8 — v3+ COMBO 채택 + LOCK 결정

**작업**: 단일 셀
- 채택된 축들 combination
- 다중 축 동시 사용 시 overfitting risk 평가
- v12 LOCK vs v3 (VIX+SOX+flow) vs v3+ (모든 채택 축) 3-way 비교

**의존성**: 3.B.7
**예상 시간**: 1시간
**산출물**: `data/sim/v3_plus_final.parquet`, comparison_report
**채택 기준**:
- v3+ COMBO Sharpe > v3 COMBO Sharpe (1.052)
- 단일 축 ΔSharpe 합산 effect 의 70% 이상 유지 (다중 추가 시 dampening)
- OOS robust

---

## 4. Phase 2.5 — Forward Test 누적 (병렬 진행)

### 4.1 — Daily Routine cell 확립

**작업**: 단일 셀 (cron-style 매일 실행)
- 어제 close 후 또는 오늘 장 마감 후
- v12 LOCKED config 그대로 적용
- 오늘 signal 생성 + 어제 entry 의 close PnL 누적

**셀 구조**:
```python
TODAY = '20260608'
T_MINUS_1 = '20260605'

# 1. fetch today's data (active OHLCV, flow, short)
# 2. state vector update for TODAY
# 3. v12 selection rule applied
# 4. log signals to forward_test/log/{TODAY}.parquet
# 5. compute T-1 entry's close PnL
# 6. accumulate to forward_test/metrics/rolling_pnl.parquet
# 7. git push
```

**의존성**: v12 LOCK 인프라 (이미 보유)
**예상 시간**: 5분/day
**산출물**: `forward_test/log/{date}.parquet`, `forward_test/metrics/rolling_*.parquet`
**검증**:
- 일별 PnL 정상 (음수 / 양수 합리 범위)
- rolling Sharpe trajectory
- regime drift 모니터링

---

### 4.2 — Weekly Rolling Sharpe

**작업**: 단일 셀 (주 1회)
- 누적 OOS 결과 → rolling Sharpe / MDD / CAGR
- v12 LOCK baseline 과 비교

**의존성**: 4.1 누적 (최소 1주)
**예상 시간**: 5분
**산출물**: `forward_test/metrics/weekly_rolling.parquet`

---

### 4.3 — Regime Drift 검증

**작업**: 단일 셀
- NEUTRAL/SHOCK regime 분포 OOS vs in-sample
- 비율 변화 > 20% → regime mismatch warning

**의존성**: 4.1 누적 (최소 1개월)
**예상 시간**: 10분
**산출물**: `forward_test/regime/drift_check.parquet`

---

## 5. Phase 3 — 12008 Web Scraping (시장 분리 외인/기관 flow)

### 5.1 — KRX 데이터광장 12008 DevTools cURL 캡처

**작업**: 형 오프라인
- PC Chrome → openapi 가 아닌 data.krx.co.kr 의 12008 화면 접근
- F12 → Network 탭 → Clear → CSV 다운로드 클릭
- 우클릭 → Copy as cURL (bash) → 채팅 paste

**의존성**: 없음 (Phase 2 와 병렬 가능)
**예상 시간**: 5분
**산출물**: cURL 문자열 1개 (Claude paste 받음)
**검증**: cURL 안에 bld code + payload + cookies 모두 포함
**Blocker**: PC 접근 불가 → 우회 path 별도 (B 옵션, 다른 source)

---

### 5.2 — KRX 데이터광장 OTP 패턴 cell

**작업**: 단일 셀
- cURL parse → bld + payload + headers 추출
- Python requests 변환
- 단일일 fetch 검증

**의존성**: 5.1
**예상 시간**: 20분 (cURL parsing + 검증)
**산출물**: web scraping cell (재사용 가능)
**검증**: 200 응답 + CSV data 정상 파싱

---

### 5.3 — 12008 9.4y bulk fetch (KOSPI/KOSDAQ 분리)

**작업**: 단일 셀
- KOSPI 단독 / KOSDAQ 단독 각 9.4y fetch
- KRX 데이터광장 rate limit 보수적

**의존성**: 5.2
**예상 시간**: ~30분 (rate limit 더 보수적, 2시간 limit 가능)
**산출물**:
- `data/raw/web/12008_kospi_10y.parquet`
- `data/raw/web/12008_kosdaq_10y.parquet`
**검증**:
- 2307 days coverage
- 투자자별 11개 column 정상
**Blocker**:
- session timeout → 재로그인 자동화
- rate limit IP ban → 분산 또는 대기

---

### 5.4 — 시장 분리 외인/기관 z-score 추가

**작업**: 단일 셀
- KOSPI 외인 net / KOSDAQ 외인 net
- KOSPI 기관 net / KOSDAQ 기관 net
- 시장 간 divergence (KOSPI 외인 매수 + KOSDAQ 외인 매도) → 별도 signal

**의존성**: 5.3
**예상 시간**: 10분
**산출물**: `data/state/v3_plus_phase3/market_split_flow.parquet`

---

### 5.5 — ΔSharpe 검증 (시장 분리 flow)

**작업**: 단일 셀
- v3+ COMBO 결과에 시장 분리 axis 추가
- ΔSharpe ≥ +0.05 시 채택

**의존성**: 5.4, 3.B.8 (v3+ baseline)
**예상 시간**: 30분
**산출물**: `data/sim/v3_plus_with_phase3.parquet`
**채택 기준**: 동일

---

## 6. Phase 4 — choonsimi-premium 6/26 비교

### 6.1 — v10c forward test 결과 수집

**작업**: 단일 셀
- 6/26 이후 choonsimi-premium repo 의 forward test 결과
- v10c (5-axis cross-sectional rank weighted) 1개월 결과

**의존성**: 6/26 도래
**예상 시간**: 10분
**산출물**: `comparison/v10c_forward_2606_2706.parquet`

---

### 6.2 — MSM v3+ 동기간 비교

**작업**: 단일 셀
- v3+ 의 6/3~6/26 forward test PnL
- v10c 의 5/26~6/26 forward test PnL (동기간 또는 인접)

**의존성**: 4.1 누적 (forward test 1개월)
**예상 시간**: 30분
**산출물**: `comparison/v3plus_vs_v10c.parquet`, `comparison/report.md`

---

### 6.3 — Dual-engine 검토

**작업**: 단일 셀
- v10c Core (mean-reversion) + v3+ Hyper (momentum + regime aware)
- 두 시스템 상관 측정 → 0 근처면 dual-engine 가능
- portfolio 결합 시 risk parity 또는 sharpe-max weight

**의존성**: 6.2
**예상 시간**: 1시간
**산출물**: `comparison/dual_engine_design.md`

---

## 7. Phase 5 — v3+ LOCK 또는 STEP 9 결정

### 7.1 — 3개월 OOS 검증

**작업**: 단일 셀
- 60거래일 OOS 누적
- Sharpe CI (confidence interval) 계산
- v12 LOCK / v3 / v3+ / v3+ + Phase 3 4-way 비교

**의존성**: 4.1 누적 (3개월)
**예상 시간**: 1시간
**산출물**: `comparison/3month_oos_report.md`

---

### 7.2 — 결정: LOCK or STEP 9

**작업**: 핵심 결정
- v3+ Sharpe > v12 + 일정 margin → v3+ LOCK
- 그렇지 않으면 v12 LOCK 유지 + STEP 9 (state v4 = sector regime / uptick / 추가 axes)

**의존성**: 7.1
**예상 시간**: -
**산출물**: `MSM_HANDOFF_v_LOCK_or_STEP9.md`

---

## 8. 산출물 인벤토리 (예상)

### 8.1 data/raw/
- `openapi/basis_10y.parquet` (~12k rows)
- `openapi/pcr_10y.parquet` (~115k rows)
- `openapi/etf_10y.parquet` (~1.4M rows)
- `openapi/kts_10y.parquet` (~350k rows, 선택)
- `macro/us10y_10y.parquet` (2307 rows)
- `web/12008_kospi_10y.parquet` (Phase 3)
- `web/12008_kosdaq_10y.parquet` (Phase 3)

### 8.2 data/state/
- `state_vector_v3plus/year=*.parquet` (2793837 rows × 30+ columns)
- `v3_plus/basis.parquet`
- `v3_plus/pcr_iv.parquet`
- `v3_plus/etf_sector.parquet`
- `v3_plus/yield_curve.parquet` (선택)
- `v3_plus_phase3/market_split_flow.parquet`

### 8.3 data/sim/
- `v3_plus/{axis_name}.parquet` (단일 축 별)
- `v3_plus_summary.parquet`
- `v3_plus_final.parquet`
- `v3_plus_with_phase3.parquet`

### 8.4 forward_test/
- `log/{date}.parquet` 누적
- `metrics/rolling_pnl.parquet`
- `metrics/weekly_rolling.parquet`
- `regime/drift_check.parquet`

### 8.5 comparison/ (Phase 4)
- `v10c_forward_2606_2706.parquet`
- `v3plus_vs_v10c.parquet`
- `report.md`
- `dual_engine_design.md`
- `3month_oos_report.md`

### 8.6 문서
- `MSM_HANDOFF_2026_06_07_v15.md` (현재)
- `MSM_WORKPLAN_v1.md` (★ 본 문서)
- `MSM_HANDOFF_v16.md` (Phase 2.A/B 종결 후)
- `MSM_HANDOFF_v17.md` (Phase 3 종결 후)
- 이후 Phase 별 핸드오프

---

## 9. 위험 / 막힘 가능 지점 (사전 식별)

### 9.1 KRX OpenAPI 관련
- **R1**: header name 3 후보 모두 fail → portal 가이드 PDF / KRX 고객센터
- **R2**: rate limit (429) → time.sleep 증가, 또는 분할 fetch
- **R3**: 일일 호출 quota → endpoint 별 분산 (4 endpoint 동시 X)
- **R4**: 만기물 식별 로직 불명확 → ISU_NM 파싱 패턴 별도 검증

### 9.2 데이터 처리 관련
- **R5**: ETF 1.4M rows 메모리 부담 → batch 처리 / chunk save
- **R6**: ATM strike 식별 (옵션 IV) → ISU_NM 패턴 + spot 가격 비교 로직 까다로움
- **R7**: ETF sector 분류 'other' 비중 50%+ → pattern iterative 추가
- **R8**: NaN forward-fill / interpolation 정책 (US10Y 영업일 mismatch 등)

### 9.3 alpha 검증 관련
- **R9**: 단일 축 ΔSharpe 합산 ≠ 다중 축 동시 Sharpe (interaction)
- **R10**: in-sample fitting 위험 (2307 days 짧음, regime 4~5개 안에서)
- **R11**: forward test 1개월 = 통계 의미 약함, 3개월 이후 결정 권장

### 9.4 Phase 3 관련
- **R12**: KRX 데이터광장 web scraping = session timeout / IP ban 위험
- **R13**: cURL 캡처 시점 OTP token = 시간 제한 (수 시간만 유효)
- **R14**: 12008 시계열 download 메뉴 = 9.4y 한 번에 가능 여부 미확정 (월 별 분할 필요 가능)

---

## 10. 의존성 그래프

```
[Phase 2.A]
2.A.1 (신청, 형) ──> 2.A.2 (smoke v4) ──> 2.A.3 (basis fetch)
                                      ──> 2.A.4 (pcr fetch)
                                      ──> 2.A.5 (etf fetch)
                                      ──> 2.A.6 (kts fetch, 선택)

[Phase 2.B]
2.A.3 ──> 3.B.2 (basis axis)
2.A.4 + 2.A.3 ──> 3.B.3 (pcr/iv axis)
2.A.5 ──> 3.B.4 (etf sector axis)
2.A.6 ──> 3.B.5 (yield curve axis, 선택)
(독립) ──> 3.B.1 (us10y fetch)

3.B.1~3.B.5 ──> 3.B.6 (state_v3+ 통합) ──> 3.B.7 (ΔSharpe) ──> 3.B.8 (LOCK 결정)

[Phase 2.5] (병렬)
4.1 (daily) ──> 4.2 (weekly) ──> 4.3 (regime drift)

[Phase 3] (병렬 또는 Phase 2 후)
5.1 (cURL, 형) ──> 5.2 (otp cell) ──> 5.3 (12008 fetch) ──> 5.4 (axis) ──> 5.5 (ΔSharpe)

[Phase 4] (6/26 이후)
6.1 (v10c 수집) ──> 6.2 (비교) ──> 6.3 (dual-engine)
4.1 누적 1개월 ──> 6.2

[Phase 5] (3개월 후)
4.1 누적 60d ──> 7.1 (3m OOS) ──> 7.2 (결정)
```

---

## 11. 다음 세션 즉시 첫 단계 (요약)

1. portal 4 endpoint 신청 (5분, 형) — 작업 2.A.1
2. setup cell (v15 §6-1) 실행 (~40초)
3. smoke v4 cell (작업 2.A.2) 실행
4. 4축 9.4y bulk fetch 진행 (2.A.3 ~ 2.A.5, 작업 2.A.6 선택)
5. US 10Y fetch (3.B.1)
6. state v3+ axis 계산 (3.B.2 ~ 3.B.5)
7. state v3+ 통합 (3.B.6)
8. 단일 축 ΔSharpe (3.B.7)

★ Phase 2 종결 시 → MSM_HANDOFF_v16.md 작성

---

## 12. 핵심 원칙 재확인

- 단일 축씩 검증 (병렬 X, v13 §4-1)
- ΔSharpe ≥ +0.05 채택 기준 (v13 §4-1)
- batch push 의무 (v13 #51, 30분+ 작업)
- §1 추측 X / §6 3축 / §7 옵션 → 형 → 실행
- Spec.docx response schema 우선 정독 (v15 #65)
- 형 사실 (Spec / 스크린샷) = ground truth (v15 #15)
- blocked 시 unblock 후보 능동 제시 (v15 #14)
- KRX 시스템 분리 (data-dbg.krx.co.kr OpenAPI vs data.krx.co.kr web) (v15 #13)

---

작성자: Claude (MSM 세션 #10 종결 시점)
기준 핸드오프: v15
다음 갱신: Phase 2.A 종결 시 v2 (또는 v16 핸드오프 통합)

끝.
