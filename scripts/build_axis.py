"""MSM build_axis.py — SSOT for 16 axes (M1~M11, M15~M19, excl M14)
v18 §3 매핑 + 2025-05-30 sample fetch 검증 후 LOCK.
"""
import time, requests
import numpy as np
import pandas as pd
from pathlib import Path

BASE_URL = "https://data-dbg.krx.co.kr/svc/apis"
ENDPOINTS = {
    "drvprod": "idx/drvprod_dd_trd",
    "bon":     "idx/bon_dd_trd",
    "fut":     "drv/fut_bydd_trd",
    "opt":     "drv/opt_bydd_trd",
}
INST7 = ["금융투자","보험","투신","사모","은행","기타금융","연기금 등"]
AXIS_KEYS = ["M1","M2","M3","M4","M5","M6","M7","M8","M9","M10","M11",
             "M15","M16","M17","M18","M19"]
COL_ORDER = ["date","M1","M2","M3","M4","M15","M16","M17","M18","M19",
             "M5","M6","M7","M8","M9","M10","M11","_n_valid"]


def _f(s):
    if s is None or s == "":
        return float("nan")
    try:
        return float(s)
    except (ValueError, TypeError):
        return float("nan")


def fetch_krx(endpoint, basDd, auth_key, retries=3, timeout=30):
    url = f"{BASE_URL}/{endpoint}"
    headers = {"AUTH_KEY": auth_key}
    params = {"basDd": basDd}
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=headers, params=params, timeout=timeout)
            if r.status_code == 200:
                return r.json().get("OutBlock_1", [])
            time.sleep(2 ** attempt)
        except Exception:
            time.sleep(2 ** attempt)
    return None


def extract_m1_m2(rows):
    for r in rows or []:
        if r.get("IDX_NM") == "코스피 200 변동성지수":
            return _f(r.get("CLSPRC_IDX")), _f(r.get("FLUC_RT"))
    return float("nan"), float("nan")


def extract_m3_m4(rows):
    for r in rows or []:
        if r.get("BND_IDX_GRP_NM") == "KRX 채권지수":
            return _f(r.get("BND_IDX_AVG_YD")), _f(r.get("AVG_DURATION"))
    return float("nan"), float("nan")


def extract_basis(rows, prod_nm):
    cands = [r for r in (rows or [])
             if r.get("PROD_NM") == prod_nm and r.get("MKT_NM") == "정규"]
    if not cands:
        return float("nan")
    def vol(r):
        v = _f(r.get("ACC_TRDVOL"))
        return -1.0 if np.isnan(v) else v
    nearest = max(cands, key=vol)
    if vol(nearest) <= 0:
        return float("nan")
    cls, spot = _f(nearest.get("TDD_CLSPRC")), _f(nearest.get("SPOT_PRC"))
    if np.isnan(cls) or np.isnan(spot):
        return float("nan")
    return cls - spot


def extract_pcr(rows, prod_nm):
    cands = [r for r in (rows or []) if r.get("PROD_NM") == prod_nm]
    if not cands:
        return float("nan")
    put_vol, call_vol = 0.0, 0.0
    for r in cands:
        v = _f(r.get("ACC_TRDVOL"))
        if np.isnan(v):
            continue
        tp = r.get("RGHT_TP_NM")
        if tp == "PUT":
            put_vol += v
        elif tp == "CALL":
            call_vol += v
    if call_vol == 0:
        return float("nan")
    return put_vol / call_vol


def extract_flow(date, df_excl, df_incl, df_kq):
    out = {f"M{i}": float("nan") for i in [5,6,7,8,9,10,11]}
    e = df_excl[df_excl["일자"] == date]
    i = df_incl[df_incl["일자"] == date]
    k = df_kq[df_kq["일자"] == date]
    if len(e) == 1 and len(i) == 1:
        er, ir = e.iloc[0], i.iloc[0]
        m5 = float(er["외국인"] + er["기타외국인"])
        m5_incl = float(ir["외국인"] + ir["기타외국인"])
        out["M5"] = m5
        out["M6"] = m5_incl - m5
        out["M8"] = float(sum(er[c] for c in INST7))
        out["M10"] = float(er["개인"])
    if len(k) == 1:
        kr = k.iloc[0]
        out["M7"] = float(kr["외국인"] + kr["기타외국인"])
        out["M9"] = float(sum(kr[c] for c in INST7))
        out["M11"] = float(kr["개인"])
    return out


def extract_basis_front(rows, prod_nm):
    """B': front-month basis (deterministic, vol-independent).
    Selection rule: min(yyyymm) over PROD_NM==prod_nm AND MKT_NM=='정규' AND not SP.
    Legacy alignment: web/vkospi_basis_94y.parquet (single row/date).
    NaN if cls or spot missing."""
    import re as _re
    cands = []
    for r in (rows or []):
        if r.get("PROD_NM") != prod_nm: continue
        if r.get("MKT_NM") != "정규": continue
        isu = r.get("ISU_NM") or ""
        if "SP" in isu: continue
        m = _re.search(r"F\s*(\d{6})", isu)
        if not m: continue
        cands.append((r, int(m.group(1))))
    if not cands:
        return float("nan")
    nearest, _ = min(cands, key=lambda x: x[1])
    cls, spot = _f(nearest.get("TDD_CLSPRC")), _f(nearest.get("SPOT_PRC"))
    if np.isnan(cls) or np.isnan(spot):
        return float("nan")
    return cls - spot


def build_axis_row(date, df_excl, df_incl, df_kq, auth_key, sleep=0.2):
    basDd = date.strftime("%Y%m%d")
    r_drvprod = fetch_krx(ENDPOINTS["drvprod"], basDd, auth_key)
    if r_drvprod is None: return None
    time.sleep(sleep)
    r_bon = fetch_krx(ENDPOINTS["bon"], basDd, auth_key)
    if r_bon is None: return None
    time.sleep(sleep)
    r_fut = fetch_krx(ENDPOINTS["fut"], basDd, auth_key)
    if r_fut is None: return None
    time.sleep(sleep)
    r_opt = fetch_krx(ENDPOINTS["opt"], basDd, auth_key)
    if r_opt is None: return None
    m1, m2 = extract_m1_m2(r_drvprod)
    m3, m4 = extract_m3_m4(r_bon)
    m15 = extract_basis(r_fut, "코스피200 선물")
    m16 = extract_basis(r_fut, "코스닥150 선물")
    m17 = extract_basis_front(r_fut, "변동성지수 선물")
    m18 = extract_pcr(r_opt, "코스피200 옵션")
    m19 = extract_pcr(r_opt, "코스닥150 옵션")
    flow = extract_flow(date, df_excl, df_incl, df_kq)
    row = {"date": date, "M1": m1, "M2": m2, "M3": m3, "M4": m4,
           "M15": m15, "M16": m16, "M17": m17, "M18": m18, "M19": m19,
           **flow}
    row["_n_valid"] = sum(1 for k in AXIS_KEYS
                          if not (isinstance(row[k], float) and np.isnan(row[k])))
    return row


def load_flow_parquets(repo=Path(".")):
    return (pd.read_parquet(repo / "data/raw/web/12008/kospi_excl_etf_94y.parquet"),
            pd.read_parquet(repo / "data/raw/web/12008/kospi_incl_etf_94y.parquet"),
            pd.read_parquet(repo / "data/raw/web/12008/kosdaq_94y.parquet"))
