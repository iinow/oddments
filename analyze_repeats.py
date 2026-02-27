import argparse
import csv
from pathlib import Path
from statistics import mean, pstdev
import matplotlib.pyplot as plt


def load_rows(csv_path: Path):
    with csv_path.open() as f:
        return list(csv.DictReader(f))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="out/repeats", help="directory containing repeat_*.csv")
    ap.add_argument("--out", default="out/repeats/summary.png")
    ap.add_argument("--table", default="out/repeats/summary_table.csv")
    args = ap.parse_args()

    d = Path(args.dir)
    files = sorted(d.glob("repeat_*.csv"))
    if not files:
        raise SystemExit(f"No repeat_*.csv found in {d}")

    by_mode = {}
    for f in files:
        rows = load_rows(f)
        for r in rows:
            mode = r["mode"]
            by_mode.setdefault(mode, {"rows_per_sec": [], "mem_delta_mb": [], "millis": []})
            by_mode[mode]["rows_per_sec"].append(float(r["rows_per_sec"]))
            by_mode[mode]["mem_delta_mb"].append(float(r["mem_delta_mb"]))
            by_mode[mode]["millis"].append(float(r["millis"]))

    modes = list(by_mode.keys())
    rps_mean = [mean(by_mode[m]["rows_per_sec"]) for m in modes]
    rps_std = [pstdev(by_mode[m]["rows_per_sec"]) for m in modes]
    mem_mean = [mean(by_mode[m]["mem_delta_mb"]) for m in modes]
    mem_std = [pstdev(by_mode[m]["mem_delta_mb"]) for m in modes]

    out_table = Path(args.table)
    out_table.parent.mkdir(parents=True, exist_ok=True)
    with out_table.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["mode", "n", "rows_per_sec_mean", "rows_per_sec_std", "mem_delta_mb_mean", "mem_delta_mb_std"])
        for i, m in enumerate(modes):
            w.writerow([m, len(files), f"{rps_mean[i]:.2f}", f"{rps_std[i]:.2f}", f"{mem_mean[i]:.4f}", f"{mem_std[i]:.4f}"])

    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    colors = ["#4e79a7", "#f28e2b"]

    ax[0].bar(modes, rps_mean, yerr=rps_std, capsize=6, color=colors[: len(modes)])
    ax[0].set_title(f"Throughput mean±std (n={len(files)})")
    ax[0].set_ylabel("rows/sec")

    ax[1].bar(modes, mem_mean, yerr=mem_std, capsize=6, color=colors[: len(modes)])
    ax[1].set_title(f"Memory delta mean±std (n={len(files)})")
    ax[1].set_ylabel("MB")

    fig.suptitle("JsonNode vs POJO repeated benchmark")
    fig.tight_layout()

    out_img = Path(args.out)
    out_img.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_img, dpi=160)

    print(f"saved: {out_img}")
    print(f"saved: {out_table}")


if __name__ == "__main__":
    main()
