# Client Q\&A log

**Version**: 01&nbsp;

**Updated:** 16 Nov 2026 (SGT).&nbsp;

Instructions to Engineers: First check the downloaded archive and separate NTULearn attachments. Do not include client records or personal identifiers in the log. Use [delivery RID](../01-Plans_Status/delivery_RID.md) for delivery risks, do not raise in client log. John consolidates and sends to client.

&nbsp;

| ID | Drafted | Date sent | Question for client | Client response | Impact / Decision | Owner | Status |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| Q01 | 16 Nov 2026 | — | **Case Log:** Could you provide the CS case log or download location? How should repeat cases for the same order be counted? | — | **Impact**: Weekly complaint counts and duplicate handling remain provisional until the case log and counting rules are available. | B | Pending client |
| Q02 | 16 Nov 2026 | — | **Resolution Guide:** Could you provide the guide and effective date? Should resolutions follow the policy at order/complaint time or the current policy? | — | **Impact**: We can summarise the evidence, but policy-based recommendations need the Resolution Guide and confirmation of which policy date applies. | A/B | Pending client |
| Q03 | 16 Nov 2026 | — | **Weekly Reporting:** How should orders be assigned to reporting zones, and are these the same as pricing zones? | — | **Impact**: Reliable weekly zone reporting needs an agreed assignment rule and confirmation of whether reporting and pricing zones align. | B | Pending client |
| Q04 | 16 Nov 2026 | — | **Delivery Evidence:** Are there additional v2 PODs? Does the delivery export contain every attempt, or only the latest/selected event? | — | **Impact**: We will show missing PODs or delivery history as unavailable evidence, rather than infer delivery failure or reuse a scan from another system. | A/B | Pending client |
| Q05 | 16 Nov 2026 | — | **Timestamps:** Are GPS values standard Unix seconds? What timezone do delivery timestamps use, and are there known clock offsets? | — | **Impact**: Delivery and GPS evidence need confirmed time conventions so we can compare the correct time window and avoid misleading conclusions. | B | Pending client |
| Q06 | 16 Nov 2026 | — | **Rate Card:** Could you provide applicable cards before 1 April 2026? If unavailable, should pricing checks be limited to orders from that date? | — | **Impact**: We cannot verify pricing for the 17,195 orders before 1 April 2026 without an earlier applicable rate card or client confirmation. | A/B | Pending client |
| Q07 | 16 Nov 2026 | — | **Rate Card:** Which weight band applies at exactly 3 kg and 10 kg, given the ranges ≤3 kg / 3–10 kg / 10–25 kg? | — | **Impact**: Boundary pricing remains ambiguous for 20 orders at exactly 3 kg or 10 kg, including 7 within the supplied card’s effective period. | A | Pending client |
| Q08 | 16 Nov 2026 | — | **Rate Card:** How do postal codes map to pricing zones? Where are service type (standard/same-day) and other surcharge inputs, such as CBD timing, holiday service and attempt count, recorded? | — | **Impact**: Accurate rates, surcharges and service availability checks need the pricing-zone mapping, service type and applicable surcharge inputs. | A | Pending client |

&nbsp;


## Impact review — 16 Nov 2026

Impacts describe current evidence limits, not client-approved decisions. The status Pending client indicates that clarification is needed; the questions have not yet been sent. Q04 covers weekly reporting-zone definitions; Q08 covers pricing-zone mapping, service type and surcharge inputs. John records the actual send date after sending and updates the status when a reply is received.

Evidence: [data audit](../05-Reviews/data_audit_2026-11-16.md), [package reconciliation](../05-Reviews/package_reconciliation_2026-11-16.md). Q07 boundary counts were rechecked read-only against the full SQL dump; they are not counts from a running MySQL instance.
