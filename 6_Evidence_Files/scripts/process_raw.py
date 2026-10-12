"""Re-process the raw NIS1 JSON exports offline.

Fixes over the first collector script:
  * uses the NEM epoch 2015-03-29 00:06:25 UTC (the first script used 00:00:00)
  * unwraps multisig-wrapped transactions (type 4100) instead of reading them as 0 XEM
  * records direction (out / in) using the signer public key, not the queried address
  * flags transactions that carry mosaics, because their 'amount' is not plain XEM
Usage: python process_raw.py   (run from the folder that holds raw/ and data/)
"""
import json, csv
from datetime import datetime, timedelta

EPOCH = datetime(2015, 3, 29, 0, 6, 25)          # NEM nemesis time, UTC
ADDR = {
    "A": ("NC3BI3DNMR2PGEOOMP2NKXQGSAKMS7GYRKVA5CSZ",
          "e40d7a1c74f173cde9a1d19369da59d53017e799143f969a4e788a6f972016af"),
    "B": ("NC4C6PSUW5CLTDT5SXAGJDQJGZNESKFK5MCN77OG",
          "fdeeab78d2082ca13f45af2fd7794d2daaf584cb1c290b4bd50306f1809a0f31"),
}

def rows_for(label):
    address, pubkey = ADDR[label]
    for e in json.load(open(f"raw/address{label}_raw.json")):
        meta, tx = e["meta"], e["transaction"]
        inner = tx.get("otherTrans", tx)            # unwrap multisig
        ts = EPOCH + timedelta(seconds=tx.get("timeStamp", 0))
        signer = inner.get("signer", tx.get("signer", ""))
        yield {
            "tx_hash": meta["hash"]["data"],
            "utc": ts.isoformat(),
            "jst": (ts + timedelta(hours=9)).isoformat(),
            "block_height": meta.get("height", ""),
            "queried_address": address,
            "direction": "out" if signer == pubkey else "in",
            "recipient": inner.get("recipient", ""),
            "amount_xem": inner.get("amount", 0) / 1e6,
            "fee_xem": tx.get("fee", 0) / 1e6,
            "outer_type": tx.get("type"),
            "multisig_wrapped": "otherTrans" in tx,
            "has_mosaics": "mosaics" in inner,
        }

if __name__ == "__main__":
    out = [r for lab in ("A", "B") for r in rows_for(lab)]
    with open("data/transactions_corrected.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader(); w.writerows(out)
    print(len(out), "rows written to data/transactions_corrected.csv")
