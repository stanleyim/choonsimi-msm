# axis_oos — Path D OOS evaluation
생성: 2026-06-07T12:47:02.458779

## Axis 정의 (재현 corr=1.000000 / MAE=0.000000)
- M2 = z60(vkospi_ohlc["등락률"])
- M8 = z60(kospi_excl_etf[7 inst cols].sum(axis=1))
- M6 = z60((kospi_incl - kospi_excl)["외인합"])
  외인합 = "외국인" + "기타외국인"  ★ README L98 단일 표기 정정

window = 60, reindex to biz_full

## T-1 alignment
- axis_t1 = axis.shift(1) on biz_full index
- 6/4 entry uses 6/2 axis (biz_full T-1: 6/3 raw에 없음)

## Path D strict
M2 > -1.0 AND M8 > 0.0 AND M6 < 0.0 → LONG entry
