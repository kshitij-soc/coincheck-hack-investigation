"""Find (1) the A -> B transfers and (2) B's first onward sweep, from transactions_corrected.csv."""
import pandas as pd

A = "NC3BI3DNMR2PGEOOMP2NKXQGSAKMS7GYRKVA5CSZ"
B = "NC4C6PSUW5CLTDT5SXAGJDQJGZNESKFK5MCN77OG"

t = pd.read_csv("data/transactions_corrected.csv")
plain = t[(~t.multisig_wrapped) & (~t.has_mosaics)]           # plain XEM transfers only

a_to_b = (plain[(plain.queried_address == A) & (plain.direction == "out") & (plain.recipient == B)]
          .sort_values("utc"))
sweeps = (plain[(plain.queried_address == B) & (plain.direction == "out")
                & (plain.amount_xem >= 500_000) & (plain.utc < "2018-01-26")]
          .sort_values("utc"))

print("A -> B:", len(a_to_b), "transfers, total", f"{a_to_b.amount_xem.sum():,.0f}", "XEM")
print("first 8 A->B:", f"{a_to_b.amount_xem.iloc[:8].sum():,.0f}",
      "| last 3:", f"{a_to_b.amount_xem.iloc[8:].sum():,.0f}")
later = plain[(plain.queried_address == B) & (plain.direction == "out") & (plain.utc >= "2018-01-26")]
# NOTE: the sweep filter (plain transfers >= 500,000 XEM, before 2018-01-26 00:00 UTC) selects the large first-day
# transfers. It is not proof of every movement from B; later outflows are counted separately below.
print("B later outflows (not traced):", len(later), "transfers,", f"{later.amount_xem.sum():,.0f}", "XEM")
print("B -> onward (first sweep):", len(sweeps), "transfers, total", f"{sweeps.amount_xem.sum():,.0f}", "XEM")
a_to_b.to_csv("data/theft_transactions_corrected.csv", index=False)
sweeps.to_csv("data/hop2_sweeps.csv", index=False)
