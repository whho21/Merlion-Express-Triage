# Client Brief — Merlion Express Logistics Pte Ltd

*From: Priya Nair, Head of Customer Experience (your client contact)*

We deliver ~100 parcels a day island-wide. My CS team is buried in complaint emails and our ops
data is split across an old and a new system after a February migration that, frankly, went badly.

**What we want:** a complaint-triage assistant. Paste or ingest a customer email and it should:
identify the order (customers never tell us which system their order number is from), pull the
delivery history, the POD scan if any, the GPS trail near the delivery time, check the rate card,
and recommend a resolution per our policies (re-deliver, refund, compensate, reject — my CS
team's Resolution Guide). Also:
a weekly "which drivers / zones cause the most complaints" view for me.

**Known landmines:**
- Order numbers repeat across the v1/v2 systems. Yes, really.
- Our GPS pings and our delivery times don't seem to line up by a few hours(?).
- Some postal codes look wrong. Singapore postal codes are 6 digits.

**Data manifest:** `sql/merlion_ops.sql`, `tabular/` (my CS team's case log with their Resolution Guide),
`logs/gps_pings_sample.jsonl` (60k pings), `images/proof_of_delivery/` (80 scans), `images/rate_cards/`,
`docs/complaint_emails/` (90 emails).

---

## Engagement rules (same for all teams)

You are a squad of **forward deployed engineers**. The client is non-technical.
A panel of judges will role-play your client contact at the demo.

**You must deliver, on presentation day (Fri 27 Nov 2026, 09:00–13:00, NTU@one-north SR902; per team: 5-minute pitch, 5-minute live demo, then Q&A from the panel; slot order announced at the Tue 24 Nov consult):**

1. A working AI application using the LLM API endpoint provided in class (open API, key issued per team). No other paid AI services.
2. Ingestion of ALL data source types in this package (SQL, tabular, images, documents). The app must answer from *this* data, not model memory.
3. An architecture diagram and at least two Mermaid diagrams (e.g. data flow, sequence diagram of one query, ER diagram of your cleaned schema).
4. A one-page data quality report: what was wrong with the client's data and what you did about it.
5. A live demo in which the client (the judging panel) will ask unscripted questions.

**Constraints:**
- The raw data is too large to paste into a prompt. You are expected to build retrieval / pipelines, not a mega-prompt.
- Answers must cite their source (table, file, or image) so the client can verify.
- If the data cannot answer a question, the app must say so instead of guessing.
- Handle the data-protection issues you find. You may be asked about PDPA on demo day.

**Talking to the client:** the client is reachable by email only. Send questions to the course director with the
subject `Client question — Team N`; the client replies within two working days, answers only what is asked, and does
not take calls. Real clients forget things: if something this brief mentions is not in the package, do not guess and
do not work around it in silence — ask. Record every client answer in `docs/client_qa.md` in your repo.

**Marking signal (what the client cares about):** correct answers on messy cross-source questions,
graceful handling of contradictions and missing data (including noticing what is missing and asking),
clear architecture, and a demo that survives questions you did not rehearse.
