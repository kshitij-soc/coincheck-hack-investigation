# Reproducibility notes

**Project:** Coincheck NEM theft investigation (First Quadrant Labs / BIA)

## What you need
Python 3.10 or newer with `requests`, `pandas` and `matplotlib`.

## Steps
1. **Raw data.** `raw/addressA_raw.json` and `raw/addressB_raw.json` were collected on 28 September 2026 with `scripts/coincheck_collector.py` from the public NIS1 node `7338.work:7890`. You can use the saved files or collect them again.
2. **Processing.** Run `python scripts/process_raw.py` from this folder. It writes `data/transactions_corrected.csv` (4,350 rows).
3. **Findings.** Run `python scripts/find_theft_and_sweeps.py`. Expected output:
   - A to B: 11 transfers, 526,300,010 XEM (first 8: 523,000,010; last 3: 3,300,000)
   - B later outflows (not traced): 37 transfers, 3,300,334 XEM
   - B onward, first sweep: 8 transfers, 523,000,000 XEM
4. **Integrity.** Compare each file's SHA-256 hash with `EVIDENCE_REGISTER.csv` (`sha256sum <file>` on Linux or macOS, `Get-FileHash <file>` in Windows PowerShell).

## Method notes
- NEM timestamps count seconds from 2015-03-29 00:06:25 UTC. The first collector script used 00:00:00, so its times were 6 min 25 s early. `process_raw.py` uses the corrected epoch. Times in the report are in JST (UTC+9); the transaction tables also show UTC.
- `process_raw.py` works out direction from the signer's public key, unwraps multisig-wrapped transactions, and flags transactions that carry mosaics.

## Limitations
- **Single node.** All blockchain data came from one public third-party node in one session. A single node can be out of sync, incomplete or unavailable, so the key transactions (the 11 A to B transfers and the 8 onward transfers) should be checked against at least one more independent NIS1 node before being relied on. I have not done this.
- The eight onward transfers were selected as plain transfers of 500,000 XEM or more from Address B before 26 January 2018 00:00 UTC. That filter does not prove they are every movement from B.
- Only one hop beyond Address B was traced.
- The node may not stay online, so the saved raw files are the reference copy.
