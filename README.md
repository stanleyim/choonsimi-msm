# MSM Engine — File Set

## 파일 구조

```
choonsimi-msm/
├── engine.py                              ← 메인 모듈 (5-stage pipeline)
├── forward_test/
│   ├── daily_run.py                       ← cron/CLI 실행용
│   ├── inbox/                             ← 신규 signal 투입 (json)
│   │   └── long_signals_YYYYMMDD.json
│   ├── log/realized/realized_log.parquet  ← 누적 OOS log (schema v1.2)
│   ├── schema/realized_log_v1.json
│   └── templates/
│       └── daily_run_cell.py              ← Colab 단일 셀 paste & run
```

## 설치 (1회)

위 3 파일 GitHub repo 루트에 upload:
- `engine.py` → repo 루트
- `daily_run.py` → `forward_test/daily_run.py`
- `daily_run_cell.py` → `forward_test/templates/daily_run_cell.py`

inbox 디렉토리 생성:
```bash
mkdir -p forward_test/inbox
```

## 매일 실행

### Colab tablet (단일 셀)

`forward_test/templates/daily_run_cell.py` 내용을 셀에 paste & run.

### CLI

```bash
python forward_test/daily_run.py            # 실제 실행
python forward_test/daily_run.py --dry-run  # parquet write + git 없이 검증
```

## 신규 entry 투입

`forward_test/inbox/long_signals_YYYYMMDD.json` 생성 (YYYYMMDD = latest biz day):

```json
{
  "entry_date": "2026-06-08",
  "side": "LONG",
  "hold_target": 15,
  "codes": ["000157","003650","006405","058650","065710",
            "052330","000270","005380","105560","000660"]
}
```

(우선주 제외 권장. 우선주 진단은 PREF_DIAGNOSIS_2026_06_05.md 참고.)

신규 entry signal 생성 자체는 v12 simulator 영구 불가로 별도 작업.
v12 LOCK 또는 외부 source에서 받아 inbox에 투입.

## 동작

매 실행 시:
1. `realized_log.parquet` load
2. OPEN position의 mtm_px 최신 KRX 거래일로 갱신
3. 만기(hold_days_target 도달) 시 자동 CLOSED + exit_cost 차감
4. inbox 신규 signal 있으면 5 variants × N codes row append:
   - `v12_RAW` (pollution=False, 진짜 OOS)
   - `v12+M8`, `v12+M2`, `v12+M6`, `v12+M8M2M6` (pollution=True, 진단용)
5. parquet 저장 + git commit/push

Idempotent: 같은 날 재실행 안전.

## 핵심 상수 (engine.py에 LOCKED)

| 상수 | 값 |
|---|---|
| ENTRY_COST | 0.0015 |
| EXIT_COST | 0.0015 |
| WEIGHT | 0.10 |
| HOLD_LONG | 15 |
| HOLD_SHORT | 5 |
| OOS_BOUNDARY | 2026-06-04 |

| Filter | Rule |
|---|---|
| M8 z_inst_kospi | > 0.0 |
| M2 z_vkospi_delta | > -1.0 |
| M6 z_foreign_kospi_etf | < 0.0 |

## 영구 제약

- v12 simulator 재현 영구 불가 (§0 #13)
- regime detection logic 재현 영구 불가
- → 신규 entry signal 생성은 inbox 외부 의존

## 메트릭

```python
from engine import portfolio_metrics
import pandas as pd
df_log = pd.read_parquet('forward_test/log/realized/realized_log.parquet')
print(portfolio_metrics(df_log))
```

진짜 OOS Sharpe는 `is_pollution_risk=False` row만 (`signal_source=='v12_RAW'`).
n ≥ 20 누적 후 통계 의미.
