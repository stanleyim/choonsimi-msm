# Forward Test — Daily Run Template
# 실행: 매일 장 마감 후 1회 (또는 누적 batch)
# 단일 셀로 paste & run
# v12 LOCK config 변경 금지

# (이 셀은 새 세션에서 사용; 매일 실행)
# 1. 환경 setup (clone, secrets)
# 2. 어제까지 누적 log 로드
# 3. 오늘 OOS fetch + state 생성
# 4. signal + simulation
# 5. push to forward_test/log/{date}.parquet
