#!/usr/bin/env python3
"""AI 작화 비용 합계 — _작화비용.log 를 편별·품질별로 더한다.   python3 samples/엔진/scripts/cost.py [편 이름 일부]"""
import sys, collections
from pathlib import Path
LOG = Path(__file__).resolve().parents[3] / "_작화비용.log"
if not LOG.exists(): sys.exit("아직 기록이 없습니다(AI 작화를 한 번도 안 돌림).")
key = sys.argv[1] if len(sys.argv) > 1 else ""
by = collections.defaultdict(lambda: [0, 0.0])
for ln in LOG.read_text(encoding="utf-8").splitlines():
    p = ln.split("\t")
    if len(p) < 5 or key not in p[1]: continue
    by[(p[1], p[3])][0] += 1; by[(p[1], p[3])][1] += float(p[4])
tot = 0.0
for (ep, q), (n, c) in sorted(by.items()):
    print(f"{ep:30s} {q:6s} {n:3d}장  ${c:.2f}"); tot += c
print(f"{'합계':30s}        ${tot:.2f}  (대략값 — 실제는 OpenAI 대시보드)")
