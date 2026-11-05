# The Anderson Story — Living Family Edition (v0.1)

Family-first, dependency-free, static website. Designed for the `humanaios-ui/heritage-miner` project (Issue #2).

## Test right now

1. Unzip this package.
2. Open `site/index.html` in a modern browser. No server is needed.
3. Select your own copy of the original manuscript PDF under **The book**. It stays on your device.
4. Add a photo under **Add your piece of the story**. It appears in **Family album** as a **local draft**.
5. Use **Export contribution** to save a JSON package with the photo. Use **Import** to test restore.

The static preview has **no submission server**. Choosing "Family edition — propose for review" does not transmit anything or publish a photo. Local draft storage uses IndexedDB when available; if blocked, drafts remain for the session only. The exported contribution contains private contents; keep it off public GitHub.

## Preservation and provenance

- The user's original 1992 manuscript PDF is **not included** in this public-safe preview, and is not changed by this software.
- Its canonical PDF has 217 scan pages and no extractable text; the public demo uses a thematic reading guide, not the original named table of contents. The original TOC remains inside the user-supplied PDF; printed page numbers are not mapped to scan positions.
- One early scan may be inverted; the reader offers Rotate.
- Completeness and publishing rights need review before public publication of manuscript scans or contributed memories.

## Test notes

This is a first family experience, **not** a hosted or collaborative service. No accounts, model calls, background tracking, analytics, external fetches, AI commentary, or server uploads. A shared family editorial workflow is a later phase.

## Authority boundary

Saving or exporting a draft grants no publication authority. Contributions require independent family-editor review and consent before sharing. Future research functions remain separate and opt-in.


## Heritage background (v0.2)
The hero now uses `assets/heritage-parchment.webp`: an artistic, AI-assisted background derived from visual references in the family's scanned 1992 manuscript. It is **not** an exact historical photograph or transcription. The original PDF is unchanged and not bundled. The background is ornamental and is stored with the publicly visible website source; review family-image sharing preferences before broad publication.

The mobile and desktop layouts keep the heading readable above a translucent cream panel. To replace it later, change the asset and the `.hero` background in `style.css`.