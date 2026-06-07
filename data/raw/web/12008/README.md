# KRX 데이터광장 — 12008 투자자별 거래실적

**출처**: KRX 데이터광장 (data.krx.co.kr)
**화면번호**: 12008
**화면명**: 투자자별 거래실적
**수집일**: 2026-06-07
**수집 방법**: 형 수동 다운로드 (DevTools cURL X, 데이터광장 web CSV download)

---

## 1. 파일 구조

| 파일 | 시장 | ETF/ETN/ELW | rows | size |
|---|---|---|---|---|
| kospi_excl_etf_94y.parquet | KOSPI | 불포함 | 2309 | 188 KB |
| kospi_incl_etf_94y.parquet | KOSPI | 포함 | 2309 | 191 KB |
| kosdaq_94y.parquet | KOSDAQ | (불가) | 2309 | 179 KB |

★ KOSDAQ = ETF/ETN/ELW 미포함 default (형 명시)

## 2. 기간

- **2017-01-02 ~ 2026-06-05** (2309 거래일, 9.4년)
- 5 batch 분할 다운로드:
  - Batch 1: 2017-01-02 ~ 2018-12-28 (487 days)
  - Batch 2: 2019-01-02 ~ 2020-12-30 (494 days)
  - Batch 3: 2021-01-04 ~ 2022-12-29 (494 days)
  - Batch 4: 2023-01-02 ~ 2024-12-30 (489 days)
  - Batch 5: 2025-01-02 ~ 2026-06-05 (345 days)

## 3. Schema (13 columns)

| 컬럼 | 의미 |
|---|---|
| 일자 | 거래일 (datetime) |
| 금융투자 | 금융투자(증권사) 순매수 |
| 보험 | 보험사 순매수 |
| 투신 | 투자신탁 순매수 |
| 사모 | 사모펀드 순매수 |
| 은행 | 은행 순매수 |
| 기타금융 | 기타금융 순매수 |
| 연기금 등 | 연기금/공제회 순매수 |
| 기타법인 | 일반법인 순매수 |
| 개인 | 개인 순매수 |
| 외국인 | 외국인 순매수 |
| 기타외국인 | 기타외국인 순매수 |
| 전체 | zero-sum (always 0) |

★ 기관(7) = 금융투자 + 보험 + 투신 + 사모 + 은행 + 기타금융 + 연기금

## 4. 단위

**백만원** (KRW million) — 거래대금 순매수 기준

## 5. 정합성 검증 결과 (PASS)

```
CHECK 1: zero-sum
  전체 = 0  (모든 2309 days, 완벽)

CHECK 2: 11 투자자 sum vs 전체
  max diff = 3 백만원 (반올림 오차)

CHECK 3: ETF effect (KOSPI incl - excl)
  ETF 비중 = 외인 flow 의 10.6%
  ETF effect abs.mean = 37,080 백만원
  cash equity abs.mean = 348,266 백만원

CHECK 4: 시장 분리 corr (9.4y)
  KOSPI 외인 vs KOSDAQ 외인 = 0.032  ★ 거의 독립
  KOSPI 기관 vs KOSDAQ 기관 = 0.201
  KOSPI 개인 vs KOSDAQ 개인 = 0.194

CHECK 5: 연도별 KOSPI vs KOSDAQ 외인 corr
  2017: 0.073   2022: 0.195
  2018: 0.289   2023: 0.022
  2019: 0.007   2024: 0.176
  2020: 0.101   2025: 0.253
  2021: 0.258   2026: -0.086
  → 모든 연도 |corr| < 0.30 (안정)

CHECK 6: Stationarity (z-score validity)
  KOSPI(excl) 외인: mean=-71965, std=665009, ac(1)=0.494 (★ 강한 momentum)
  KOSPI(incl) 외인: mean=-70442, std=666633, ac(1)=0.489
  KOSDAQ 외인     : mean=  1573, std=132567, ac(1)=-0.006 (noisy)
```

## 6. MSM v3+ 사용 계획

```python
# axis 생성 (다음 세션)
kospi_excl = pd.read_parquet('data/raw/web/12008/kospi_excl_etf_94y.parquet')
kospi_incl = pd.read_parquet('data/raw/web/12008/kospi_incl_etf_94y.parquet')
kosdaq     = pd.read_parquet('data/raw/web/12008/kosdaq_94y.parquet')

# z-score (rolling 252)
z_foreign_kospi_cash = zscore_rolling(kospi_excl['외국인'], 252)
z_foreign_kospi_etf  = zscore_rolling((kospi_incl - kospi_excl)['외국인'], 252)
z_foreign_kosdaq     = zscore_rolling(kosdaq['외국인'], 252)

# 기관 합 (7 categories)
inst_cols = ['금융투자','보험','투신','사모','은행','기타금융','연기금 등']
z_inst_kospi_cash = zscore_rolling(kospi_excl[inst_cols].sum(axis=1), 252)
z_inst_kosdaq     = zscore_rolling(kosdaq[inst_cols].sum(axis=1), 252)

# 시장 divergence
z_divergence_foreign = z_foreign_kospi_cash - z_foreign_kosdaq
```

## 7. 단일 축 ΔSharpe 검증 순서

1. z_foreign_kospi_cash (★ 1순위, ac(1)=0.494 강한 momentum)
2. z_divergence_foreign (★ 2순위, 시장 분리 새 차원)
3. z_inst_kospi_cash
4. z_foreign_kosdaq
5. z_inst_kosdaq
6. z_foreign_kospi_etf (선택, ETF arbitrage)

채택 기준: ΔSharpe ≥ +0.05

---

작성: Claude (MSM 세션 #10, 2026-06-07)
