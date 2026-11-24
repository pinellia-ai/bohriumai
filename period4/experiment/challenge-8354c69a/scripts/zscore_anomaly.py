#!/usr/bin/env python3
"""异常检测: zscore_anomaly.py baseline.csv readings.csv -> anomalies.csv
baseline.csv: metric,mean,sd   readings.csv: sample,batch,metric,value"""
import csv, sys
base = {r['metric']: (float(r['mean']), float(r['sd'])) for r in csv.DictReader(open(sys.argv[1]))}
rows = []
for r in csv.DictReader(open(sys.argv[2])):
    m = r['metric']; v = float(r['value'])
    if m not in base: continue
    mu, sd = base[m]
    z = (v - mu) / sd if sd else 0
    verdict = 'anomaly' if abs(z) >= 3 else ('borderline' if abs(z) >= 2 else 'normal')
    rows.append([r['sample'], r.get('batch', ''), m, v, round(z, 2), verdict])
with open('anomalies.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['sample', 'batch', 'metric', 'value', 'z', 'verdict']); w.writerows(rows)
print(f"anomalies.csv: {len(rows)} readings, {sum(1 for r in rows if r[5]=='anomaly')} anomalies, {sum(1 for r in rows if r[5]=='borderline')} borderline")
