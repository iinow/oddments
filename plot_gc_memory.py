import re
import argparse
from pathlib import Path
import matplotlib.pyplot as plt

# Example line:
# [..][1.121s][info][gc] GC(5) Pause Young ... 122M->2M(200M) 0.746ms
GC_RE = re.compile(
    r"\[(?P<uptime>[0-9.]+)s\].*?GC\((?P<id>\d+)\).*?Pause .*? (?P<before>\d+)M->(?P<after>\d+)M\((?P<heap>\d+)M\) (?P<pause>[0-9.]+)ms"
)


def parse_gc(path: Path):
    points = []
    for line in path.read_text(errors="ignore").splitlines():
        m = GC_RE.search(line)
        if not m:
            continue
        points.append({
            "t": float(m.group("uptime")),
            "id": int(m.group("id")),
            "before": float(m.group("before")),
            "after": float(m.group("after")),
            "pause": float(m.group("pause")),
        })
    return points


def summarize(points):
    if not points:
        return {"events": 0, "peak_before": 0, "peak_after": 0, "pause_sum": 0, "pause_max": 0}
    return {
        "events": len(points),
        "peak_before": max(p["before"] for p in points),
        "peak_after": max(p["after"] for p in points),
        "pause_sum": sum(p["pause"] for p in points),
        "pause_max": max(p["pause"] for p in points),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jsonnode", required=True)
    ap.add_argument("--pojo", required=True)
    ap.add_argument("--out", default="build/reports/gc_memory_chart.png")
    args = ap.parse_args()

    j = parse_gc(Path(args.jsonnode))
    p = parse_gc(Path(args.pojo))

    js = summarize(j)
    ps = summarize(p)

    fig, ax = plt.subplots(1, 3, figsize=(16, 4.5))

    # 1) before-GC memory (pressure)
    ax[0].plot([x["t"] for x in j], [x["before"] for x in j], label=f"JsonNode before (peak={js['peak_before']:.0f}MB)", color="#4e79a7")
    ax[0].plot([x["t"] for x in p], [x["before"] for x in p], label=f"POJO before (peak={ps['peak_before']:.0f}MB)", color="#f28e2b")
    ax[0].set_title("Before-GC used heap (allocation pressure)")
    ax[0].set_xlabel("uptime(s)")
    ax[0].set_ylabel("MB")
    ax[0].legend()

    # 2) after-GC live set
    ax[1].plot([x["t"] for x in j], [x["after"] for x in j], label=f"JsonNode after (peak={js['peak_after']:.0f}MB)", color="#4e79a7")
    ax[1].plot([x["t"] for x in p], [x["after"] for x in p], label=f"POJO after (peak={ps['peak_after']:.0f}MB)", color="#f28e2b")
    ax[1].set_title("After-GC used heap (live set)")
    ax[1].set_xlabel("uptime(s)")
    ax[1].set_ylabel("MB")
    ax[1].legend()

    # 3) pause timeline
    ax[2].plot([x["t"] for x in j], [x["pause"] for x in j], label=f"JsonNode pause(sum={js['pause_sum']:.1f}ms,max={js['pause_max']:.1f}ms)", color="#4e79a7")
    ax[2].plot([x["t"] for x in p], [x["pause"] for x in p], label=f"POJO pause(sum={ps['pause_sum']:.1f}ms,max={ps['pause_max']:.1f}ms)", color="#f28e2b")
    ax[2].set_title("GC pause timeline (STW)")
    ax[2].set_xlabel("uptime(s)")
    ax[2].set_ylabel("ms")
    ax[2].legend()

    fig.suptitle("GC/Memory comparison from GC pause lines")
    fig.tight_layout()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=160)
    print(out)
    print("JsonNode:", js)
    print("POJO:", ps)


if __name__ == "__main__":
    main()
