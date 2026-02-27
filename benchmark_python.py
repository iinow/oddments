import argparse
import csv
import json
import random
import time
from dataclasses import dataclass
from pathlib import Path


def make_row(i: int) -> dict:
    r = random.Random(i)
    return {
        "id": f"item-{i}",
        "ts": 1700000000000 + i,
        "type": "event",
        "value": r.randint(0, 10000),
        "nested": {
            "name": "l1", "score": r.randint(0, 100), "child": {
                "name": "l2", "score": r.randint(0, 100), "child": {
                    "name": "l3", "score": r.randint(0, 100), "child": {
                        "name": "l4", "score": r.randint(0, 100), "child": {
                            "name": "l5", "score": r.randint(0, 100), "child": {
                                "name": "l6", "score": r.randint(0, 100), "leaf": f"hello-{i}"
                            }
                        }
                    }
                }
            }
        }
    }


def generate(path: Path, rows: int):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for i in range(rows):
            f.write(json.dumps(make_row(i), ensure_ascii=False))
            f.write("\n")


@dataclass
class L6:
    name: str
    score: int
    leaf: str


@dataclass
class L5:
    name: str
    score: int
    child: L6


@dataclass
class L4:
    name: str
    score: int
    child: L5


@dataclass
class L3:
    name: str
    score: int
    child: L4


@dataclass
class L2:
    name: str
    score: int
    child: L3


@dataclass
class L1:
    name: str
    score: int
    child: L2


@dataclass
class Payload:
    id: str
    ts: int
    type: str
    value: int
    nested: L1


def to_payload(d: dict) -> Payload:
    n1 = d["nested"]
    n2 = n1["child"]
    n3 = n2["child"]
    n4 = n3["child"]
    n5 = n4["child"]
    n6 = n5["child"]
    return Payload(
        id=d["id"], ts=d["ts"], type=d["type"], value=d["value"],
        nested=L1(
            name=n1["name"], score=n1["score"],
            child=L2(
                name=n2["name"], score=n2["score"],
                child=L3(
                    name=n3["name"], score=n3["score"],
                    child=L4(
                        name=n4["name"], score=n4["score"],
                        child=L5(
                            name=n5["name"], score=n5["score"],
                            child=L6(name=n6["name"], score=n6["score"], leaf=n6["leaf"]),
                        ),
                    ),
                ),
            ),
        ),
    )


def bench_dict(path: Path):
    start = time.perf_counter()
    cnt = 0
    checksum = 0
    with path.open(encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            checksum += d["value"] + d["nested"]["child"]["child"]["child"]["child"]["child"]["score"]
            cnt += 1
    sec = time.perf_counter() - start
    return "JsonNode(dict)", cnt, sec, checksum


def bench_pojo(path: Path):
    start = time.perf_counter()
    cnt = 0
    checksum = 0
    with path.open(encoding="utf-8") as f:
        for line in f:
            p = to_payload(json.loads(line))
            checksum += p.value + p.nested.child.child.child.child.child.score
            cnt += 1
    sec = time.perf_counter() - start
    return "POJO(dataclass)", cnt, sec, checksum


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", type=int, default=1_000_000)
    ap.add_argument("--data", default="build/data/payload.ndjson")
    ap.add_argument("--out", default="build/reports/deserialize_benchmark_py.csv")
    args = ap.parse_args()

    data = Path(args.data)
    out = Path(args.out)

    if not data.exists():
        print(f"Generating {args.rows:,} rows -> {data}")
        generate(data, args.rows)

    r1 = bench_dict(data)
    r2 = bench_pojo(data)

    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["mode", "rows", "seconds", "rows_per_sec", "checksum"])
        for mode, rows, sec, checksum in (r1, r2):
            w.writerow([mode, rows, f"{sec:.6f}", f"{rows/sec:.2f}", checksum])

    print("\n=== RESULT ===")
    for mode, rows, sec, checksum in (r1, r2):
        print(f"{mode:16s} {sec:.3f}s  {rows/sec:,.0f} rows/s  checksum={checksum}")
    print(f"CSV: {out}")


if __name__ == "__main__":
    main()
