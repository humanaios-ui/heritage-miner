# Historical claim verification protocol

1. Select one contested claim from the **private** GEDCOM and personal notes.
2. Independently retrieve an actual external historical document. Record author, publication date, page/section, live source locator, access date and whether text is an original scan or a transcription.
3. Keep the GEDCOM value and historical publication value **as separate observations**.
4. Deduplicate mirrors of one book by underlying source identity, not URL.
5. Mark conflicting claims **CONTRADICTED**. This establishes a verified discrepancy, not the correct date.
6. Seek a closer primary record (census, church register, probate, vital record).
7. Keep the person-level proof receipt in private storage while this repository is public.
8. Generate a reviewed research proposal to Resource Miner only; no execution authority.

## Falsifiable software experiment
Given two independent source labels with different asserted years, `reconcile` must show both, mark CON-TRADICTED, select neither, and leave the input unchanged. A duplicate web transcription of one book must not inflate the count of underlying works. A user name must be rejected by the Resource Miner opaque-only proposal schema.

## Evidence labels
- OBSERVED: an externally retrieved work makes an explicit statement.
- SUPPORTED: a claim has documentary support, with limitations noted.
- CONTRADICTED: two source assertions disagree; no winner inferred.
- UNVERIFIED: an assertion lacks independent evidence.

Code can compare supplied values. Code **cannot authenticate a historical work** by itself.
