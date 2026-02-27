import csv
from pathlib import Path
import matplotlib.pyplot as plt

csv_path = Path('build/reports/deserialize_benchmark.csv')
out = Path('build/reports/deserialize_benchmark.png')

rows = list(csv.DictReader(csv_path.open()))
modes = [r['mode'] for r in rows]
rps = [float(r['rows_per_sec']) for r in rows]
mem = [float(r['mem_delta_mb']) for r in rows]

fig, ax = plt.subplots(1, 2, figsize=(10, 4))
ax[0].bar(modes, rps, color=['#4c78a8', '#f58518'])
ax[0].set_title('Rows/sec')
ax[0].set_ylabel('rows/sec')

ax[1].bar(modes, mem, color=['#4c78a8', '#f58518'])
ax[1].set_title('Memory delta (MB)')
ax[1].set_ylabel('MB')

fig.suptitle('JsonNode vs POJO deserialization')
fig.tight_layout()
out.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(out, dpi=150)
print(f'saved: {out}')
