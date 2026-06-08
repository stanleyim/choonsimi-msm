"""
MSM Engine — Market Structure Model pipeline
============================================

5-stage pipeline:
  STATE → REGIME → TRANSITION → EDGE → TRADEABLE

v12 LOCK baseline (불변):
  LONG : NEUTRAL × bot z_ell top 10, hold 15d, weight 1/10
  SHORT: SHOCK × bot score top 10, hold 5d, weight 1/10
  Cost : 0.30% RT (entry 0.15% + exit 0.15%)

영구 제약 (v14 §0):
  - v12 simulator 재현 불가
  - regime detection logic 재현 불가
  → 신규 entry 생성은 외부 ground truth 의존

PATH-1 진행:
  v12 LOCK + axis filter (M8/M2/M6, Protocol C 결과)
  + forward test OOS 누적
"""

from __future__ import annotations
import json
import warnings
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')

# ============================================================
# Constants (LOCKED)
# ============================================================
REPO_ROOT = Path('/content/choonsimi-msm')

# v12 LOCK
ENTRY_COST = 0.0015
EXIT_COST  = 0.0015
WEIGHT     = 0.10
HOLD_LONG  = 15
HOLD_SHORT = 5

# Axis filter rules (Protocol C, Path D)
FILTER_RULES = {
    'M8': ('z_inst_kospi',         'gt',  0.0),   # M8 > 0.0
    'M2': ('z_vkospi_delta',       'gt', -1.0),   # M2 > -1.0
    'M6': ('z_foreign_kospi_etf',  'lt',  0.0),   # M6 < 0.0
}

AXIS_COLUMNS = {
    'M8': 'M8_z_inst_kospi',
    'M2': 'M2_z_vkospi_delta',
    'M6': 'M6_z_foreign_kospi_etf',
}

SIGNAL_VARIANTS = [
    'v12_RAW',
    'v12+M8',
    'v12+M2',
    'v12+M6',
    'v12+M8M2M6',
]

POLLUTION_RISK = {
    'v12_RAW':     False,
    'v12+M8':      True,
    'v12+M2':      True,
    'v12+M6':      True,
    'v12+M8M2M6': True,
}

OOS_BOUNDARY = pd.Timestamp('2026-06-04')


# ============================================================
# Data classes
# ============================================================
@dataclass
class FilterPass:
    M8: bool
    M2: bool
    M6: bool

    def for_variant(self, variant: str) -> bool:
        if variant == 'v12_RAW':       return True
        if variant == 'v12+M8':        return self.M8
        if variant == 'v12+M2':        return self.M2
        if variant == 'v12+M6':        return self.M6
        if variant == 'v12+M8M2M6':    return self.M8 and self.M2 and self.M6
        raise ValueError(f'unknown variant: {variant}')


@dataclass
class AxisSnapshot:
    ref_date: pd.Timestamp
    lag_bd: int
    M8: float
    M2: float
    M6: float

    def filter_pass(self) -> FilterPass:
        return FilterPass(
            M8=bool(self.M8 > FILTER_RULES['M8'][2]) if not np.isnan(self.M8) else False,
            M2=bool(self.M2 > FILTER_RULES['M2'][2]) if not np.isnan(self.M2) else False,
            M6=bool(self.M6 < FILTER_RULES['M6'][2]) if not np.isnan(self.M6) else False,
        )


# ============================================================
# STAGE 1 — STATE
# ============================================================
def load_state_v2(repo: Path = REPO_ROOT) -> pd.DataFrame:
    """state_vector_v2 전체 load. shape (2,793,837 × 26) 가정 (v12 LOCK 시점)."""
    from glob import glob
    files = sorted(glob(str(repo / 'data/state/state_vector_v2/year=*.parquet')))
    assert files, 'state_vector_v2 not found'
    df = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    df['date'] = pd.to_datetime(df['date'])
    if 'score' not in df.columns:
        df['score'] = df['z_r'] + df['z_f']
    return df


def load_axis_v3(repo: Path = REPO_ROOT) -> pd.DataFrame:
    """19-axis catalog. DatetimeIndex, columns = M{N}_z_*"""
    df = pd.read_parquet(repo / 'data/state/axis_v3/axis_candidates_19.parquet')
    return df


# ============================================================
# STAGE 2 — REGIME
# ============================================================
def axis_snapshot(df_ax: pd.DataFrame, entry_date: pd.Timestamp) -> AxisSnapshot:
    """T-1 axis 값 추출 (cutoff 미달 시 fallback)."""
    target = entry_date - pd.tseries.offsets.BDay(1)
    if target in df_ax.index:
        ref = target
    else:
        valid = df_ax.index[df_ax.index < entry_date]
        if len(valid) == 0:
            return AxisSnapshot(ref_date=pd.NaT, lag_bd=-1,
                                M8=np.nan, M2=np.nan, M6=np.nan)
        ref = valid.max()

    bdays = pd.bdate_range(start=ref, end=entry_date)
    lag = max(0, len(bdays) - 1)
    row = df_ax.loc[ref]

    def _get(col):
        v = row[col]
        return float(v) if pd.notna(v) else np.nan

    return AxisSnapshot(
        ref_date=ref,
        lag_bd=lag,
        M8=_get(AXIS_COLUMNS['M8']),
        M2=_get(AXIS_COLUMNS['M2']),
        M6=_get(AXIS_COLUMNS['M6']),
    )


# ============================================================
# STAGE 3 — TRANSITION (forward-only, no in-sample reconstruction)
# ============================================================
def is_oos(entry_date: pd.Timestamp) -> bool:
    return pd.Timestamp(entry_date) >= OOS_BOUNDARY


# ============================================================
# STAGE 4 — EDGE (cost-aware mark-to-market)
# ============================================================
def compute_mtm(entry_px: float, mtm_px: float, closed: bool) -> dict:
    gross = (mtm_px / entry_px) - 1.0
    exit_c = EXIT_COST if closed else 0.0
    net = gross - ENTRY_COST - exit_c
    return {
        'gross_ret_mtm': gross,
        'entry_cost': ENTRY_COST,
        'exit_cost': exit_c,
        'net_ret_mtm': net,
    }


# ============================================================
# STAGE 5 — TRADEABLE (realized log row generation)
# ============================================================
def build_log_row(
    *,
    entry_date: pd.Timestamp,
    code: str,
    side: str,
    signal_source: str,
    signal_status: str,
    entry_px: Optional[float],
    mtm_px: Optional[float],
    mtm_date: Optional[pd.Timestamp],
    axis: AxisSnapshot,
    fp: FilterPass,
    hold_days_target: int = HOLD_LONG,
    closed: bool = False,
    regime: str = 'NEUTRAL_assumed',
    notes: str = '',
) -> dict:
    """Schema v1.2 row 생성."""
    log_id = f"{pd.Timestamp(entry_date).strftime('%Y%m%d')}_{code}_{signal_source.replace('+','_')}"

    if signal_status == 'TAKEN':
        assert entry_px is not None and mtm_px is not None
        mtm = compute_mtm(entry_px, mtm_px, closed)
        bdays = pd.bdate_range(start=entry_date, end=mtm_date)
        hold_elapsed = max(0, len(bdays) - 1)
        status = 'CLOSED' if closed else 'OPEN'
        exit_date = pd.Timestamp(mtm_date).date() if closed else pd.NaT
        weight = WEIGHT
    else:  # REJECTED_BY_FILTER
        mtm = {'gross_ret_mtm': 0.0, 'entry_cost': 0.0,
               'exit_cost': 0.0, 'net_ret_mtm': 0.0}
        hold_elapsed = 0
        status = 'SKIPPED'
        exit_date = pd.NaT
        entry_px = np.nan
        mtm_px = np.nan
        mtm_date = pd.NaT
        weight = 0.0

    return {
        'log_id': log_id,
        'entry_date': pd.Timestamp(entry_date).date(),
        'exit_date': exit_date,
        'code': code,
        'side': side,
        'signal_source': signal_source,
        'signal_status': signal_status,
        'is_pollution_risk': POLLUTION_RISK[signal_source],
        'is_oos': is_oos(entry_date),
        'entry_px': entry_px,
        'mtm_px': mtm_px,
        'mtm_date': pd.Timestamp(mtm_date).date() if pd.notna(mtm_date) else pd.NaT,
        'gross_ret_mtm': mtm['gross_ret_mtm'],
        'entry_cost': mtm['entry_cost'],
        'exit_cost': mtm['exit_cost'],
        'net_ret_mtm': mtm['net_ret_mtm'],
        'weight': weight,
        'hold_days_elapsed': hold_elapsed,
        'hold_days_target': hold_days_target,
        'status': status,
        'regime_at_entry': regime,
        'axis_M8': axis.M8,
        'axis_M2': axis.M2,
        'axis_M6': axis.M6,
        'axis_ref_date': pd.Timestamp(axis.ref_date).date() if pd.notna(axis.ref_date) else pd.NaT,
        'axis_lag_bd': axis.lag_bd,
        'filter_M8_pass': fp.M8,
        'filter_M2_pass': fp.M2,
        'filter_M6_pass': fp.M6,
        'notes': notes,
    }


# ============================================================
# Orchestration — append OOS day (entry + variants)
# ============================================================
def append_oos_entries(
    *,
    entry_date: pd.Timestamp,
    mtm_date: pd.Timestamp,
    codes: list[str],
    px_map: dict[str, dict],
    df_ax: pd.DataFrame,
    side: str = 'LONG',
    hold_target: int = HOLD_LONG,
    notes: str = '',
) -> pd.DataFrame:
    """단일 entry_date의 5 variants × N codes log row 생성."""
    axis = axis_snapshot(df_ax, entry_date)
    fp = axis.filter_pass()

    rows = []
    for variant in SIGNAL_VARIANTS:
        passed = fp.for_variant(variant)
        status = 'TAKEN' if passed else 'REJECTED_BY_FILTER'

        for code in codes:
            if status == 'TAKEN':
                px = px_map.get(code)
                if px is None:
                    continue
                entry_px = px['entry_px']
                mtm_px   = px['mtm_px']
            else:
                entry_px = None
                mtm_px = None

            row = build_log_row(
                entry_date=entry_date,
                code=code,
                side=side,
                signal_source=variant,
                signal_status=status,
                entry_px=entry_px,
                mtm_px=mtm_px,
                mtm_date=mtm_date if status == 'TAKEN' else None,
                axis=axis,
                fp=fp,
                hold_days_target=hold_target,
                closed=False,
                notes=notes,
            )
            rows.append(row)

    return pd.DataFrame(rows)


# ============================================================
# Mark-to-market daily update
# ============================================================
def update_open_positions(
    df_log: pd.DataFrame,
    px_map: dict[str, float],
    mtm_date: pd.Timestamp,
) -> tuple[pd.DataFrame, int, int]:
    """OPEN row의 mtm 갱신. 만기 시 CLOSED."""
    mask_open = (df_log['signal_status'] == 'TAKEN') & (df_log['status'] == 'OPEN')
    df_open = df_log[mask_open].copy()
    df_rest = df_log[~mask_open].copy()

    updates, closes = 0, 0
    for idx, row in df_open.iterrows():
        if row['code'] not in px_map:
            continue
        new_mtm_px = px_map[row['code']]
        entry_px = row['entry_px']
        entry_date = pd.Timestamp(row['entry_date'])

        bdays = pd.bdate_range(start=entry_date, end=mtm_date)
        new_hold = max(0, len(bdays) - 1)
        is_maturity = new_hold >= int(row['hold_days_target'])

        mtm = compute_mtm(entry_px, new_mtm_px, is_maturity)

        df_open.at[idx, 'mtm_px']            = new_mtm_px
        df_open.at[idx, 'mtm_date']          = mtm_date.date()
        df_open.at[idx, 'gross_ret_mtm']     = mtm['gross_ret_mtm']
        df_open.at[idx, 'exit_cost']         = mtm['exit_cost']
        df_open.at[idx, 'net_ret_mtm']       = mtm['net_ret_mtm']
        df_open.at[idx, 'hold_days_elapsed'] = new_hold
        df_open.at[idx, 'status']            = 'CLOSED' if is_maturity else 'OPEN'
        df_open.at[idx, 'exit_date']         = mtm_date.date() if is_maturity else pd.NaT
        updates += 1
        if is_maturity:
            closes += 1

    df_new = pd.concat([df_rest, df_open], ignore_index=False).sort_index()
    return df_new, updates, closes


# ============================================================
# Metric utilities
# ============================================================
def annualized_sharpe(returns: np.ndarray, ann_factor: int = 252) -> float:
    if len(returns) == 0 or np.std(returns) == 0:
        return np.nan
    return (np.mean(returns) * ann_factor) / (np.std(returns) * np.sqrt(ann_factor))


def portfolio_metrics(df_log: pd.DataFrame) -> pd.DataFrame:
    """variant별 portfolio metric. is_pollution_risk=False만 진짜 OOS."""
    rows = []
    for variant, sub in df_log.groupby('signal_source'):
        n        = len(sub)
        n_taken  = (sub['signal_status'] == 'TAKEN').sum()
        n_reject = (sub['signal_status'] == 'REJECTED_BY_FILTER').sum()
        portfolio_net = sub['net_ret_mtm'].mean()
        rows.append({
            'variant': variant,
            'n_total': n,
            'n_TAKEN': n_taken,
            'n_REJECTED': n_reject,
            'portfolio_net_bp': portfolio_net * 10000,
            'is_pollution_risk': POLLUTION_RISK[variant],
        })
    return pd.DataFrame(rows)


# ============================================================
# Import test
# ============================================================
if __name__ == '__main__':
    print(f'MSM Engine v1 loaded')
    print(f'  ENTRY_COST = {ENTRY_COST}, EXIT_COST = {EXIT_COST}')
    print(f'  HOLD_LONG = {HOLD_LONG}, HOLD_SHORT = {HOLD_SHORT}')
    print(f'  FILTER_RULES = {FILTER_RULES}')
    print(f'  SIGNAL_VARIANTS = {SIGNAL_VARIANTS}')
    print(f'  OOS_BOUNDARY = {OOS_BOUNDARY.date()}')
