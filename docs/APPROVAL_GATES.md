# Approval gates

Only humans open these gates. Software, including this prototype, never opens one. Until each applicable gate is recorded as approved, nothing real is published and no deployment is authorized.

| # | Gate | Decides | Required before | Recorded as |
|---|---|---|---|---|
| 1 | Author/estate and image permissions | Who holds rights in the text, photos and captions; permission to reproduce and distribute | Any real scan, transcript, print PDF or EPUB leaves private custody | Written permission, kept privately (not in this repo) |
| 2 | Audience | Family only, private review, or public; per item | Any distribution; choosing `audience` on a contribution | Decision note naming scope |
| 3 | Living-person material | What may appear about living people, minors included | Publishing any item that names or depicts them | Per-item consent or exclusion |
| 4 | Editorial rules and moderator | Family editorial rules; who the moderator is; approve/reject authority | Enabling CONTRIBUTE for real submissions | Named moderator; entries in `data/review_log.jsonl` |
| 5 | Behavioral research | Whether any separate study is invited at all | Any recruitment or data collection | Separate consent, independent ethical review; never inferred from reading or participation |

Rules that apply to every gate:

- No automatic public launch. Acceptance step 8 is a human decision.
- Permissions and private records stay outside this public repo.
- A gate decision is new information; it does not retroactively edit the 1992 edition.
- Approvals of contributions are logged append-only with hash chaining (see `DATA_CONTRACT.md`).
