"""Cross-check the key transactions against a second, independent NIS1 source.

The main analysis used one public node (7338.work:7890). This script asks a
different node (or reads raw JSON saved from a different source) for the same
accounts and checks that every transaction used in the findings is present
with the same amount, recipient and block height.

Checked transactions
  - the 11 transfers from Address A to Address B  (data/theft_transactions_corrected.csv, EVD-018)
  - the 8 onward transfers from Address B          (data/hop2_sweeps.csv, EVD-019)

Usage (run from the 6_Evidence_Files folder)
  python scripts/crosscheck_second_node.py --node http://nis1.p-runner.net:7890
  python scripts/crosscheck_second_node.py --raw-a other_A.json --raw-b other_B.json

Output
  A summary on screen and data/crosscheck_<source>.csv with one row per transaction.
  Exit code 0 if all 19 transactions match, 1 otherwise.

Status: the offline mode was tested against the saved raw files (EVD-011, 012).
The live-node mode reuses the endpoint and paging of coincheck_collector.py but has
not yet been run against a second node. Record the result in CHAIN_OF_CUSTODY.csv
and the evidence register when you do.
"""
import argparse
import csv
import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

NEM_EPOCH = datetime(2015, 3, 29, 0, 6, 25)  # corrected epoch, same as process_raw.py
STOP_BEFORE = datetime(2018, 1, 25)           # the theft starts on 25 Jan 2018 UTC
ROOT = Path(__file__).resolve().parent.parent

ADDRESS_A = "NC3BI3DNMR2PGEOOMP2NKXQGSAKMS7GYRKVA5CSZ"  # Coincheck hot wallet
ADDRESS_B = "NC4C6PSUW5CLTDT5SXAGJDQJGZNESKFK5MCN77OG"  # first destination


def load_expected():
    """Return the 19 transactions the report relies on."""
    rows = []
    for role, name in (("A->B", "theft_transactions_corrected.csv"), ("B->onward", "hop2_sweeps.csv")):
        with open(ROOT / "data" / name, newline="", encoding="utf8") as f:
            for r in csv.DictReader(f):
                rows.append({
                    "role": role,
                    "tx_hash": r["tx_hash"],
                    "amount_xem": round(float(r["amount_xem"]), 6),
                    "recipient": r["recipient"],
                    "block_height": int(r["block_height"]),
                })
    return rows


def fetch_node(node, address, pause=0.3, max_pages=500):
    """Page through /account/transfers/all, newest first, as the collector does."""
    import requests  # imported here so offline mode needs no extra packages

    out, last_id = [], None
    for page in range(1, max_pages + 1):
        url = f"{node}/account/transfers/all?address={address}&pageSize=100"
        if last_id:
            url += f"&id={last_id}"
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        txs = r.json().get("data", [])
        if not txs:
            break
        out.extend(txs)
        last_id = txs[-1]["meta"]["id"]
        oldest = NEM_EPOCH + timedelta(seconds=txs[-1]["transaction"].get("timeStamp", 0))
        print(f"  {address[:8]}... page {page}: {len(out)} records, oldest {oldest}")
        if oldest < STOP_BEFORE or len(txs) < 100:
            break
        time.sleep(pause)
    return out


def index_by_hash(records):
    idx = {}
    for tx in records:
        h = tx["meta"]["hash"]["data"]
        t = tx["transaction"]
        idx[h] = {
            "amount_xem": round(t.get("amount", 0) / 1_000_000, 6),
            "recipient": t.get("recipient"),
            "block_height": tx["meta"].get("height"),
        }
    return idx


def compare(expected, idx_a, idx_b):
    results = []
    for e in expected:
        idx = idx_a if e["role"] == "A->B" else idx_b
        got = idx.get(e["tx_hash"])
        if got is None:
            status, detail = "MISSING", "hash not returned by this source"
        else:
            diffs = [f"{k}: expected {e[k]}, got {got[k]}"
                     for k in ("amount_xem", "recipient", "block_height") if e[k] != got[k]]
            status, detail = ("MATCH", "") if not diffs else ("DIFFERENT", "; ".join(diffs))
        results.append({**e, "status": status, "detail": detail})
    return results


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--node", help="base URL of a second NIS1 node, e.g. http://host:7890")
    ap.add_argument("--raw-a", help="raw JSON for Address A from another source")
    ap.add_argument("--raw-b", help="raw JSON for Address B from another source")
    args = ap.parse_args()

    if args.node:
        label = urlparse(args.node).hostname or "node"
        records_a = fetch_node(args.node, ADDRESS_A)
        records_b = fetch_node(args.node, ADDRESS_B)
    elif args.raw_a and args.raw_b:
        label = "rawfiles"
        records_a = json.load(open(args.raw_a, encoding="utf8"))
        records_b = json.load(open(args.raw_b, encoding="utf8"))
    else:
        ap.error("give --node, or both --raw-a and --raw-b")

    results = compare(load_expected(), index_by_hash(records_a), index_by_hash(records_b))
    out_path = ROOT / "data" / f"crosscheck_{label}.csv"
    with open(out_path, "w", newline="", encoding="utf8") as f:
        w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        w.writeheader()
        w.writerows(results)

    ok = sum(r["status"] == "MATCH" for r in results)
    for role in ("A->B", "B->onward"):
        sub = [r for r in results if r["role"] == role]
        print(f"{role}: {sum(r['status'] == 'MATCH' for r in sub)} of {len(sub)} match")
    for r in results:
        if r["status"] != "MATCH":
            print(f"  {r['status']}: {r['tx_hash'][:16]}... {r['detail']}")
    print(f"Result: {ok} of {len(results)} transactions match. Written to {out_path.name}")
    sys.exit(0 if ok == len(results) else 1)


if __name__ == "__main__":
    main()
