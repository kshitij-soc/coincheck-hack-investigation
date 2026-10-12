import requests
import json
import csv
import time
from datetime import datetime, timedelta

NEM_EPOCH = datetime(2015, 3, 29, 0, 0, 0)

NODES_TO_TRY = [
    "http://7338.work:7890",
    "http://nis1.p-runner.net:7890",
]

ADDRESS_A = "NC3BI3DNMR2PGEOOMP2NKXQGSAKMS7GYRKVA5CSZ"  # Coincheck hot wallet
ADDRESS_B = "NC4C6PSUW5CLTDT5SXAGJDQJGZNESKFK5MCN77OG"  # Initial destination


def find_working_node():
    for node in NODES_TO_TRY:
        try:
            r = requests.get(f"{node}/heartbeat", timeout=5)
            if r.status_code == 200:
                print(f"[OK] Node alive: {node}")
                return node
        except Exception as e:
            print(f"[FAIL] {node}: {e}")
    raise Exception("No working NIS1 node found.")


def fetch_all_transfers(node, address, label, stop_before_iso="2018-01-01T00:00:00"):
    all_txs = []
    last_id = None
    page = 1
    stop_before = datetime.fromisoformat(stop_before_iso)
    max_pages = 500  # hard safety cap so this can never truly run forever

    while page <= max_pages:
        url = f"{node}/account/transfers/all?address={address}&pageSize=100"
        if last_id:
            url += f"&id={last_id}"
        try:
            r = requests.get(url, timeout=15)
            r.raise_for_status()
        except Exception as e:
            print(f"  [WARN] Page {page} failed: {e} -- stopping, keeping what we have.")
            break

        data = r.json()
        txs = data.get("data", [])
        if not txs:
            break

        all_txs.extend(txs)
        last_id = txs[-1]["meta"]["id"]

        last_ts = txs[-1]["transaction"].get("timeStamp", 0)
        last_time = NEM_EPOCH + timedelta(seconds=last_ts)
        print(f"  Page {page}: total = {len(all_txs)} | oldest tx time so far = {last_time}")

        if last_time < stop_before:
            print(f"  Reached transactions older than {stop_before_iso} -- stopping.")
            break

        page += 1
        time.sleep(0.3)

        if len(txs) < 100:
            break

    fname = f"{label}_raw.json"
    with open(fname, "w") as f:
        json.dump(all_txs, f, indent=2)
    print(f"  Saved {len(all_txs)} transactions to {fname}")
    return all_txs


def nem_timestamp_to_iso(nem_ts):
    return (NEM_EPOCH + timedelta(seconds=nem_ts)).isoformat()


def process_transactions(raw_txs, source_address):
    rows = []
    for entry in raw_txs:
        tx = entry.get("transaction", {})
        meta = entry.get("meta", {})
        tx_hash = meta.get("hash", {}).get("data", "")
        height = meta.get("height", "")
        timestamp = tx.get("timeStamp", 0)
        iso_time = nem_timestamp_to_iso(timestamp)
        amount = tx.get("amount", 0) / 1000000
        fee = tx.get("fee", 0) / 1000000
        recipient = tx.get("recipient", "")
        rows.append({
            "tx_hash": tx_hash,
            "timestamp": iso_time,
            "block_height": height,
            "recipient": recipient,
            "amount_xem": amount,
            "fee_xem": fee,
            "source_address": source_address
        })
    return rows


def main():
    node = find_working_node()

    print(f"\nFetching Address A...")
    raw_a = fetch_all_transfers(node, ADDRESS_A, "addressA", stop_before_iso="2018-01-20T00:00:00")

    print(f"\nFetching Address B...")
    raw_b = fetch_all_transfers(node, ADDRESS_B, "addressB", stop_before_iso="2018-01-20T00:00:00")

    rows_a = process_transactions(raw_a, ADDRESS_A)
    rows_b = process_transactions(raw_b, ADDRESS_B)
    all_rows = rows_a + rows_b

    with open("transactions.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["tx_hash", "timestamp", "block_height", "recipient", "amount_xem", "fee_xem", "source_address"])
        writer.writeheader()
        writer.writerows(all_rows)
    print(f"\ntransactions.csv written with {len(all_rows)} rows")

    total_out_a = sum(r["amount_xem"] for r in rows_a)
    print(f"Total XEM out of Address A: {total_out_a}")
    if rows_a:
        print(f"Earliest tx (last in list): {rows_a[-1]['timestamp']}")
        print(f"Latest tx (first in list): {rows_a[0]['timestamp']}")


if __name__ == "__main__":
    main()