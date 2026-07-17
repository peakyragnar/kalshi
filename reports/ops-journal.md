# Operations journal

Appended daily by the scheduled kalshi-daily-ops pass (14:11, after the 13:15
mechanical chain). Each entry: pipeline status, sweeps, signal changes, shadow
book stats, alerts. Open questions for the operator are flagged, never decided.

---

## 2026-07-17 — first scheduled pass (quiet)

- Pipeline: healthy. Incremental high-water 2026-07-17T12:15Z (~2.5h old);
  +1,072 markets, +119,984 trades; recorder 24,829 books, 0 errors; dashboard
  and all state files regenerated today.
- Rulebook sweep: 0 UNSWEPT — full backlog cleared by sweeps 2–3 earlier today
  (15 GREEN / 101 YELLOW / 1 RED across 117 candidates). The RED
  (KXCBPAIRPORT, causal attribution) was verdicted in sweep 3 and already
  blacklisted and committed before this pass; not new.
- Signals: no HOT. WARM on KXSENATECONFIRM-26APR29-JCLA (Clayton — held in
  shadow book); CLEAR on SBES, CMEA. Edge lights unchanged: politics_30d
  GREEN (+28.0% t90), financials_90d AMBER (bound below hurdle, halved-entry).
- Shadow book: 11 resting orders (6 Fin / 5 Pol), $1,995.73 resting, 0 fills,
  $10,000 cash, nothing deployed. Book created today 13:08Z.
- Open questions: (1) congressional watcher reports "? session days before
  deadline" (session_days_left null) — tail grading is running without session
  calendar data; (2) financials_90d newest resolution quarter 2026-Q3 shows
  +8%±9% (n=48), the soft cohort behind the AMBER light — watch as n grows.
