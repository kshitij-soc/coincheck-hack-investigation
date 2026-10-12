# Coincheck NEM Theft (January 2018): Blockchain Investigation

An independent, reproducible reconstruction of the 26 January 2018 theft of NEM (XEM) from the Japanese exchange Coincheck. It uses public statements and blockchain records that I collected myself from a public NEM (NIS1) node on 28 September 2026.

Everything here is built from public information. It is a reconstruction, not a full digital forensic examination: no internal Coincheck logs, disk images, memory dumps or malware samples are public.

## Key findings

| Finding | Confidence |
|---|---|
| 526,300,010 XEM moved from Coincheck's wallet (Address A) to a new address (Address B) in 11 transfers, the first at 00:02:13 JST | Confirmed (blockchain) |
| Address B sent exactly 523,000,000 XEM on to eight new addresses between 02:57:24 and 03:29:54 JST | Confirmed (blockchain) |
| All 11 transfers were plain single-signer transfers with no co-signatures | Confirmed (blockchain) |
| The XEM was in a hot wallet; the president cited technical difficulties and a staff shortage | Strongly supported (company statements) |
| Coincheck's reported ~523M XEM matches the first eight transfers; the last three (3,300,000 XEM) are not reflected | Arithmetic confirmed; explanation is an interpretation |
| Coincheck's reported ~02:57 start matches the first onward transfer from B, not the first transfer out of A (00:02:13), which would make the detection gap about 11 h 23 min rather than about 8 h 28 min | Interpretation |
| How the attacker got in, who they were, whether customer data was exposed, where the funds went after the eight addresses | Unknown |

Findings are labelled **Confirmed**, **Strongly supported**, **Interpretation** or **Unknown**. Each is mapped to its evidence in [`6_Evidence_Files/FINDINGS_MATRIX.csv`](6_Evidence_Files/FINDINGS_MATRIX.csv).

## What is in this repository

| Path | What it is |
|---|---|
| `1_Executive_Summary.docx` | Two-page summary for a general reader |
| `2_Detailed_Incident_Report.docx` | Scope, timeline, attack vector, impact, forensic method, discrepancies, limitations, sources |
| `3_Mitigation_Plan.docx` | Immediate, short-term and long-term actions, each tied to the case, with a scored risk view and scoring criteria |
| `4_Forensic_Evidence_Portfolio.docx` | Evidence register, SHA-256 hashes, screenshots, transaction tables, chain of custody, finding-to-evidence matrix |
| `5_Presentation_Deck.pptx` | Eight-slide summary, including a slide on what the analysis cannot tell you |
| `pdf/` | PDF copies of the five documents above, for reading in the browser |
| `6_Evidence_Files/` | Raw node data, processed tables, scripts, figures, screenshots, register and reproducibility notes |

Inside `6_Evidence_Files/`:

```
raw/            node responses for Address A and Address B (as saved on 28 Sep 2026)
data/           processed tables (corrected epoch, direction, multisig unwrapped)
scripts/        collector, processing, findings, and second-node cross-check
figures/        cumulative movement chart and fund-flow diagram
screenshots/    news, regulator and account-record captures
EVIDENCE_REGISTER.csv   every item with its SHA-256 hash and confidence level
CHAIN_OF_CUSTODY.csv    source, method, collector, date, storage and transformations
FINDINGS_MATRIX.csv     finding -> evidence IDs -> processing step -> how to verify
REPRODUCIBILITY.md      steps, expected output, method notes
```

## Reproduce the analysis

Requires Python 3.10+ with `requests`, `pandas` and `matplotlib`.

```bash
cd 6_Evidence_Files
python scripts/process_raw.py              # builds data/transactions_corrected.csv (4,350 rows)
python scripts/find_theft_and_sweeps.py    # prints the findings
```

Expected output:

```
A -> B: 11 transfers, total 526,300,010 XEM
first 8 A->B: 523,000,010 | last 3: 3,300,000
B later outflows (not traced): 37 transfers, 3,300,334 XEM
B -> onward (first sweep): 8 transfers, total 523,000,000 XEM
```

Check file integrity against the register:

```bash
python -c "import csv,hashlib;[print(r['Evidence_ID'],'OK' if hashlib.sha256(open(r['File'],'rb').read()).hexdigest()==r['SHA256'] else 'MISMATCH') for r in csv.DictReader(open('EVIDENCE_REGISTER.csv'))]"
```

A `.gitattributes` file stops Git from changing line endings in `6_Evidence_Files/`, so the hashes still match after checkout on any operating system.

## Limitations

- **Single node.** All blockchain data came from one public NIS1 node in one session. `scripts/crosscheck_second_node.py` compares the 19 key transactions with another node; it has not yet been run against a second node.
- **One hop traced.** Funds are followed from A to B to eight addresses. Their onward movement is not traced.
- **Two interpretations.** The explanations for the 3.3M XEM gap and the reported start time are my readings of the data, not confirmed facts.
- **No internal artifacts.** The attack vector is marked Unknown. One published case study reports malware on a company terminal; I could not trace it to a primary source.
- **Chain of custody.** The time of day of each collection and the exact command line were not recorded at the time and are marked as such.

## Possible next steps

1. Run the second-node cross-check and record the result in the chain-of-custody log.
2. Extend the trace past the eight addresses where reliable historical data permits, with its scope and limits stated.

## AI assistance

I used an AI assistant (Claude) to review my processing scripts and to help draft and edit the written documents. No finding depends on AI output alone: every number can be recomputed from the raw node data with the scripts above, and the outputs and hashes match the evidence register. Section 1.1 of the Incident Report lists the check for each part of the work.

## License

Released under the MIT License. See [`LICENSE`](LICENSE).

## Disclaimer

This is independent research for education. It uses public sources only, makes no claim about the conduct of any named person or organisation beyond what those sources state, and is not legal, financial or security advice.

## Author

Kshitij Randhire
