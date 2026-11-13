# Migration v5.6 — proposed generation windows

Companion to `migration_v56_split_wide_generations.sql`. **Not applied to production yet — awaiting approval.**

Five `generations` rows spanned more than 12 years. Ad analysis uses the generation window as the year guard of the live market comparison, so these rows compared a car with listings a decade or more apart.

## Proposed windows

Rows marked **existing** keep their current id (and everything linked to it). The others are inserted.

| Model | Today | Proposed | Row |
|---|---|---|---|
| BMW 530 | Geração principal 1988–now | E34 1988–1995 | new |
| | | E39 1996–2003 | **existing** (355) |
| | | E60 2004–2009 | new |
| | | F10 2010–2016 | new |
| | | G30 2017–2023 | new |
| | | G60 2024–now | new |
| Volkswagen Caddy | Caddy III 2003–2020 | Caddy III 2003–2010 | new |
| | | Caddy III facelift 2011–2015 | new |
| | | Caddy IV 2016–2020 | **existing** (283) |
| | Caddy V 2020–now | Caddy V 2021–now | existing (282), start year moved |
| Fiat 500 | 500 (312) 2007–2023 | 500 (312) 2007–2015 | **existing** (36) |
| | | 500 (312) facelift 2016–2024 | new |
| Fiat Panda | Panda III 2012–now | Panda III 2012–2019 | new |
| | | Panda III (2020 update) 2020–now | **existing** (37) |
| Lexus IS | IS III 2013–now | IS III 2013–2016 | **existing** (340) |
| | | IS III facelift 2017–2020 | new |
| | | IS III 2nd facelift 2021–now | new |

Eleven rows inserted, six updated (the five wide rows plus Caddy V's start year), eleven `reliability_evidence` rows re-pointed.

## Rules used

- **Windows of one model do not overlap.** `_get_generation_window` returns the newest row containing the year, so an overlapping changeover year always went to the newer generation.
- **A changeover year goes to the generation on sale for most of it.** Launch in the second half of the year: the outgoing generation keeps that year. This is why G60 starts in 2024 (deliveries began October 2023) and Caddy V in 2021.
- **Where a generation really is that long-lived** (Fiat 500, Panda, Lexus IS, Caddy 2K), the split is at the major facelift. `migration_v51` already does this for the Tesla Model 3 and Model S.

## Sources

Dates marked ✓ were checked on the web on 2026-11-13. The rest are from general knowledge of these model lines and are worth a second look before approval.

**BMW 5 Series**
- E34 1988–1996, E39 1995–2003 (saloon; launched December 1995), E60 2003–2010 (launched July 2003), F10 2010–2016 (launched March 2010), G30 2017–2023 (launched February 2017).
- ✓ G60: production from July 2023, sales from October 2023 — [BMW 5 Series (G60), Wikipedia](https://en.wikipedia.org/wiki/BMW_5_Series_(G60)).

**Volkswagen Caddy**
- ✓ Typ 2K from 2003/2004; phase-two facelift 2010; deeper 2015 update (Typ 2K "SA") that Volkswagen counts as the fourth generation, on sale five years until 2020 — [Parkers: Caddy history](https://parkers.co.uk/vans-pickups/advice/2020/volkswagen-caddy-history), [Volkswagen Caddy, Wikipedia](https://en.wikipedia.org/wiki/Volkswagen_Caddy).
- ✓ Caddy 5 unveiled February 2020, on sale at the very end of 2020 / January 2021 (same sources).
- 2015 is a split year (Caddy IV deliveries began mid-2015); it is assigned to the facelifted Caddy III.

**Fiat 500 (312)**
- ✓ Launched 2007; facelift in 2015 (about 1,900 changes); petrol/mild-hybrid production at Tychy ended in early July 2024 — [Autocar: Fiat 500 retired after 17 years](https://www.autocar.co.uk/node/151635), [autonotizen.de](https://autonotizen.de/neuigkeiten/fiat-500-verbrenner-produktion-ende-2024). The existing row said 2023.

**Fiat Panda III (319)**
- On sale since 2012 and still in production (renamed Pandina in 2024). There is no generation change to split on; 2020 is the 1.0 mild-hybrid launch (February 2020) followed by the late-2020 restyling.

**Lexus IS III (XE30)**
- ✓ Facelift shown April 2016, sold as model year 2017; second facelift revealed June 2020 — and Lexus confirmed it would not be sold in Western Europe — [Carscoops, October 2020](https://www.carscoops.com/2020/10/official-the-2021-lexus-is-facelift-wont-be-coming-to-western-europe/). The 2021–now row therefore only catches imports.

## What references `generations.id`

Four tables have a foreign key to `generations(id)` (checked in production, read-only, 2026-11-13). `engines` and `engine_issues` link to the model, not the generation.

| Table | Rows on the five wide generations | Handling |
|---|---|---|
| `price_observations` | 0 | nothing to do |
| `market_price_stats_history` | 0 | nothing to do |
| `reliability_scores_history` | 6 | stay on the existing id; recomputed by the monthly reliability run |
| `reliability_evidence` | 99 (BMW 9, Fiat 500 85, Panda 4, Caddy 1) | see below |

Evidence rows that move (they carry a single model year, so they follow it):

- BMW 530 → E34: ids 930 (1994), 931 (1995).
- Fiat 500 → facelift: ids 2071, 2073–2080 (model years 2016–2018; one recall, eight complaint rows).

Evidence rows that stay: the other 7 BMW rows (1997–2001, now E39), the other 76 Fiat 500 rows (2011–2015), Panda's four Safety Gate recalls (2024–2026, now the 2020-update row) and Caddy's one Safety Gate recall (2013–2024, now Caddy IV — the largest part of its range; recall display uses the recall's own years, not the generation's).

New rows start with no reliability score. Ad analysis and recommendations average the non-null scores of a model, so nothing changes for users until the next monthly reliability run scores the new rows.

## Tested

Run twice against a throwaway local Postgres 18 loaded with a copy of the seven affected generation rows, their 100 evidence rows and 9 score rows: first run splits, second run is a no-op; no evidence or score row lost; every single-year evidence row sits inside its generation's window.

## Known limits — not changed here

- **This migration alone does not fix the 2018 BMW 530e example.** The 530e only exists from 2017, so "1988–now" and "G30 2017–2023" return almost the same comparables (dry run 2026-11-13: median €29,485 vs €29,440, 18 listings each). G30 is a six-year window, below the eight-year threshold of the code safety net. Narrowing to ±2 years gives about €27,900 from 5 listings. The comparison also ignores mileage.
- BMW "530" is a separate model row from "Série 5" (which has F10 2009–2016 and G30 2016–now, itself stale since the G60).
- Fiat 500e (2020–now) still overlaps the petrol 500; the lookup is fuel-blind, so every 2020+ Fiat 500 resolves to the 500e row.
- Three of Panda's four recalls are for the Grande Panda, a different car.
