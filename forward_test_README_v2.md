# MSM Forward Test — 19:30 KST 매일 운용 명세

**작성일**: 2026-06-09
**상태**: v12 LOCK 운용 시스템

---

## 1. 시스템 개요

**목적:** v12 LOCK (NEUTRAL × bot z_ell, hold 15d, w=1/10) forward test 매일 OOS 누적.

**자동 실행:** 매일 19:30 KST (한국 장 마감 18:00 + 30분 buffer)
- GitHub Actions cron: `30 10 * * 1-5` (UTC 10:30 = KST 19:30)
- 한국 공휴일은 KRX biz day 체크에서 자동 skip

---

## 2. 데이터 흐름

```
[외부 signal source]
       ↓
forward_test/inbox/long_signals_YYYYMMDD.json
       ↓
daily_run.py (19:30 KST)
       ↓
1. realized_log mtm 갱신 (기존 OPEN positions 시가 업데이트)
2. inbox signal 있으면 → 신규 entry append
3. Path D axis eval 로그
4. git commit + push
```

---

## 3. Signal 공급 (외부 의존)

### 3-1. inbox 파일 형식

**경로:** `forward_test/inbox/long_signals_YYYYMMDD.json`

**스키마:**
```json
{
  "entry_date": "2026-06-09",
  "side": "LONG",
  "hold_target": 15,
  "codes": ["000157", "03473K", "003650", ...]
}
```

**필수 필드:**
- `entry_date`: 진입 의도일 (ISO format, T+0)
- `codes`: 10 KRX 종목 코드 (v12 LOCK = top 10)

**선택:**
- `side`: `LONG` / `SHORT` (default LONG)
- `hold_target`: 보유일 (default 15)

### 3-2. signal 부재 시

- inbox 파일 없으면 → daily_run은 **mtm만 수행** (정상 작동)
- 시스템 종료 X. 운용 공백만 발생.

### 3-3. signal source 정체

- v12 simulator는 영구 재현 불가 (engine.py §0 #13)
- signal 생성 주체 = **외부** (choonsimi-premium repo 또는 별도 시스템)
- 본 시스템은 receive + execute only

---

## 4. 일일 운영

### 4-1. 자동 (GitHub Actions)

`.github/workflows/daily-run.yml` 자동 실행. 추가 작업 없음.

### 4-2. 수동 trigger

GitHub repo → Actions → "MSM Forward Test Daily Run @ 19:30 KST" → Run workflow

### 4-3. Colab 수동 실행 (백업)

`forward_test/templates/daily_run_1930kst.py` paste & run (Colab에서).

---

## 5. 누락 복구

### 5-1. 단일 누락일 복구

1. 누락일에 inbox/long_signals_YYYYMMDD.json 입력
2. GitHub Actions 수동 trigger 또는 Colab paste

### 5-2. 다중 누락일 일괄 복구

mtm 갱신은 idempotent. 단순히 daily_run 1회 실행 = 최신 영업일까지 mtm 갱신.
신규 entry는 각 entry_date별 inbox 파일 필요.

### 5-3. 시스템 상태 확인

```python
import pandas as pd
df = pd.read_parquet('forward_test/log/realized/realized_log.parquet')
print(f'rows: {len(df)}, last entry_date: {df["entry_date"].max()}')
print(df.groupby(['signal_status', 'status']).size())
```

---

## 6. 검증

### 6-1. baseline (v12 LOCK 시뮬레이션)

- `forward_test/baseline.json`
  - sharpe_target: 0.686
  - cagr_target: 16.48%
  - mdd_target: -33.13%

### 6-2. OOS 누적 평가

`engine.portfolio_metrics(df_log)` 출력:
- TAKEN 행만 사용
- gross/net Sharpe, MDD, CAGR
- 누적 ~20~30 sample (~1.5~3개월) 필요 (의미 있는 평가)

### 6-3. baseline 대비 deviation

OOS Sharpe가 baseline ± 0.2 이내면 정상 운용 가정.
초과 deviation = signal source 변경, 시장 regime shift, 또는 system bug.

---

## 7. 알려진 제약

1. **v12 simulator 재현 불가** — entry signal은 외부 의존
2. **regime_at_entry = "NEUTRAL_assumed"** — regime detection 영구 재현 불가
3. **axis filter (M8/M2/M6) = Path D 결과** — Protocol C에서 선정, 변경 금지
4. **9.4y 데이터 1 cycle** — 통계적 일반화 한계
5. **MSM v4/v5 = 별도 R&D** — forward test와 분리 운용

---

## 8. 트러블슈팅

### "no signal in inbox"
정상. mtm만 갱신. signal 공급 안 됨.

### "fetch fail {code}"
pykrx 일시 fail. 다음날 자동 보정 (mtm은 idempotent).

### "KRX biz day fetch 실패"
pykrx 또는 KRX API 장애. 1시간 후 재시도 또는 다음날 자동 복구.

### "realized_log 부재"
긴급. git history에서 마지막 commit 복원.

```bash
git log --oneline -- forward_test/log/realized/realized_log.parquet
git checkout <commit> -- forward_test/log/realized/realized_log.parquet
```

### GitHub Actions 실행 안 됨
- repo Settings → Actions → "Allow all actions" 확인
- secrets.GITHUB_TOKEN 자동 제공 (workflow 권한 contents:write 필요 — 본 yml에 명시됨)

---

## 9. 파일 인벤토리

```
.github/workflows/daily-run.yml              ← 자동 cron
daily_run.py                                  ← 메인 실행 (Python script)
engine.py                                     ← 함수 정의
forward_test/
  inbox/                                      ← signal input (외부 공급)
    long_signals_YYYYMMDD.json
  log/realized/realized_log.parquet           ← OOS 누적 (PK=log_id)
  axis_oos/pathD_eval_oos.parquet             ← axis filter eval
  schema/realized_log_v1.json                 ← schema v1.2
  templates/daily_run_1930kst.py              ← Colab 수동 백업
  baseline.json                               ← v12 LOCK target
```

---

## 10. 변경 이력

- 2026-06-09: 19:30 KST 자동화 진입 (GitHub Actions cron). Path D eval 통합.
- 2026-06-07: realized_log v1.2 schema (TAKEN/REJECTED 분리)
- 2026-06-04: OOS#1 첫 entry (50 rows)
- 2026-06-05: v12 LOCK (commit 559a65e)

---

**연락:** repo owner stanleyim
