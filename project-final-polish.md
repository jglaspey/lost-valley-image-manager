## Project: Final Polish

Comprehensive plan to: rerun image processing from Google Drive, expand non-LLM metadata capture (creator, dates, description, dimensions), review/improve prompts and optional multi-pass analysis, expose full metadata in the UI, enable user edits with version history, refine filters, and default to most recent sorting.

### Goals
- Rerun all images cleanly with safe data handling and history.
- Enrich records with Google Drive-native metadata (non-LLM).
- Evaluate prompts; optionally add multi-sample consensus for higher accuracy.
- Display all metadata on the detail page; make it user editable with version history.
- Tighten filters and keep most useful defaults; default sort to most recent.

### Scope & Deliverables
1) Rerun Strategy and Controls
- Add CLI support to reprocess the entire library with guardrails:
  - Add a new CLI command in `image_processor/cli/main.py`: `reprocess_all`.
    - Options:
      - `--upsert` (default): update existing metadata records in-place.
      - `--archive-existing` (optional): snapshot current metadata into `metadata_versions` before update.
      - `--clear-first` (optional): delete `metadata` + `activity_tags` then recreate fresh.
      - `--limit N` (optional): limit number processed for smoke runs.
    - Behavior: set `files.processing_status` to `pending` for image rows, then process using existing batching.
  - Acceptance:
    - Running `reprocess_all --upsert` completes without UNIQUE constraint errors.
    - `processing_history` shows a new attempt per file.

2) Non-LLM Metadata Enrichment (Google Drive)
- Extend Google Drive fetch fields in `image_processor/google_drive/service.py`:
  - List/get requests to include: `description`, `owners(displayName,emailAddress)`, `lastModifyingUser(displayName,emailAddress)`, and `imageMediaMetadata(width,height,cameraMake,cameraModel,time)`, `videoMediaMetadata(width,height,time)`.
  - Fallback for shared drives where `owners` may not be present: use `lastModifyingUser`.
- Persist to DB in `files` table:
  - New columns: `creator TEXT`, `description TEXT`.
  - For dimensions: continue to store `width`/`height` (already present). If present in Drive `imageMediaMetadata`, set during discovery; otherwise maintain current thumbnail-time extraction fallback.
  - Acceptance:
    - After discovery, new rows have `creator` when resolvable, and `description` when present on Drive.
    - `width`/`height` filled for most images from Drive or thumbnail pipeline.

3) Database Migrations (Python-owned schema)
- Bump `SCHEMA_VERSION` in `image_processor/database/schema.py` to 4.
- Migrate:
  - `ALTER TABLE files ADD COLUMN creator TEXT` (nullable)
  - `ALTER TABLE files ADD COLUMN description TEXT` (nullable)
  - Create audit table for user edits:
    - `metadata_versions`:
      - `id INTEGER PRIMARY KEY AUTOINCREMENT`
      - `file_id INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE`
      - `version INTEGER NOT NULL` (monotonic per file)
      - `data_json TEXT NOT NULL` (full snapshot of merged metadata+tags)
      - `edited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP`
      - `edited_by TEXT` (store editor identifier; in current password-only world set to `'admin'`)
      - Unique `(file_id, version)`
- Add repository helpers:
  - `MetadataRepository.upsert(metadata)` or use `INSERT ... ON CONFLICT(file_id) DO UPDATE` equivalent.
  - `ProcessingHistoryRepository` remains; add a helper to mark reprocess cycles if desired.
  - New `MetadataVersionRepository` with `add_version(file_id, data_json, edited_by)` and `list_versions(file_id)`.
- Acceptance:
  - `migrate_schema()` upgrades existing DBs to version 4 without data loss.
  - New tables/columns visible via quick SELECTs.

4) Prompt Review and Analysis Strategy
- Unify field sets across local `VisionClient` and `ClaudeVisionClient`:
  - Ensure both produce identical keys to match DB schema and UI: `primary_subject`, `has_people`, `people_count`, `is_indoor`, `activity_tags`, `visual_quality`, `social_media_score`, `social_media_reason`, `marketing_score`, `marketing_use`, optional `season`, `time_of_day`, `mood_energy`, `color_palette`, `notes`.
- Tighten prompts:
  - Demand strict JSON, include an explicit JSON schema excerpt, and instruct “respond with only JSON”.
  - For pass-2 scoring, collapse extraneous narrative; keep guidelines but shorter; set expectations for realistic score distribution.
- Optional multi-sample consensus (feature flag):
  - Add `vision_model.consensus_samples` in config. If >1, run `analyze_image` multiple times and merge via majority vote/median (scores: median; booleans: majority; tags: union capped to known set; text fields: longest or first).
  - Acceptance: On a 20-image eval set, consensus reduces contradictory outcomes (e.g., `has_people` flip-flops) by >=30%.

5) API Enhancements (Node server)
- Versions API:
  - `GET /api/images/:id/versions` → list `metadata_versions` entries with `version`, `edited_at`, `edited_by`.
  - `POST /api/images/:id/versions/:version/revert` → restore snapshot to current `metadata` and `activity_tags`, and create a new version capturing the revert.
- Edits capture:
  - On `PUT /api/images/:id/metadata`, before update:
    - Read current joined metadata+tags
    - Store into `metadata_versions` as next `version` with `edited_by = 'admin'`.
  - Keep existing update logic (validated ranges), return updated record.
- Acceptance:
  - Version list populates after an edit, and revert restores exact previous values.

6) Frontend Enhancements
- Image Detail Modal (`web-app/client/src/components/ImageDetailModal.tsx`):
  - Display everything:
    - File: filename, file_path, file_size, width×height, created_date, modified_date, creator, drive links.
    - AI: primary_subject, visual_quality, social_media_score + reason, marketing_score + use, has_people + people_count, is_indoor, season, time_of_day, mood_energy, color_palette, notes, activity_tags.
  - Editing:
    - Add an Edit toggle to inline-edit AI fields and tags (use `shadcn` inputs/slider/checkboxes).
    - Save triggers `PUT /api/images/:id/metadata` and shows toast on success.
    - A Versions section lists prior edits; “Revert” calls versions API.
- Filters and defaults:
  - Keep the quick filters row (High Quality, Marketing Ready, With People, Outdoor).
  - In the left filter panel, default open sections: Quality, Scores, Activity, People; collapse less-used by default.
  - Confirm default sort is most recent (created_date DESC) and expose a simple sort dropdown if needed.
- Acceptance:
  - All fields above are visible; edits persist; version history lists entries and revert works.

### Implementation Notes
- Discovery fields (Drive v3):
  - List: `files(id,name,mimeType,size,createdTime,modifiedTime,parents,description,owners(displayName,emailAddress),lastModifyingUser(displayName,emailAddress),imageMediaMetadata(width,height,cameraMake,cameraModel,time),videoMediaMetadata(width,height,time))`
  - Get: the same field superset for `_get_file_info` when needed.
- Creator resolution precedence: `owners[0].displayName` → `lastModifyingUser.displayName` → `owners[0].emailAddress`.
- Dimensions precedence: `imageMediaMetadata.width/height` → thumbnail pipeline extraction (Sharp) → unknown.
- Upsert strategy for reprocessing: prefer SQL upsert to avoid delete/recreate; keep `activity_tags` replace semantics (clear then insert new set) to reflect current analysis.
- Audit payload shape (`data_json`): include a single merged object: `{ file: { id, filename, ... }, metadata: { ... }, activity_tags: [...] }` to make diffs readable.

### Data Migration & Rollout
1. Update Python schema and run migration locally against a copy of prod DB.
2. Deploy server with new endpoints (reading same DB file).
3. Ship client updates (detail page + editing + versions UI + filters).
4. Dry-run reprocess on a subset: `reprocess_all --upsert --limit 25`.
5. Full reprocess window:
   - Take a backup of DB.
   - `reprocess_all --archive-existing --upsert` or `--clear-first` per decision.
   - Monitor logs and `processing_history`.

### Acceptance Criteria (Summary)
- CLI can reprocess entire library without uniqueness errors; stats reflect fresh processing.
- `files` has `creator` and `description` populated where present; `width`/`height` populated for the majority.
- UI shows all fields and allows edits; version history visible; revert restores fields.
- Filters are concise, default open key sections; default sorting is most recent.
- Optional consensus mode togglable in config, with measured reduction of contradictory outputs on a sample.

### Risks / Considerations
- Google Drive `owners` info can be restricted on shared drives; fallbacks required.
- Reprocessing at scale may hit Drive rate limits; respect backoff already in `GoogleDriveService`.
- Versioning can bloat DB; consider pruning policy later (e.g., keep last N versions).
- Password-only auth means `edited_by` is coarse; fine-grained user tracking would require real accounts.

### Task Checklist
- [ ] Schema v4: add `creator`, `description`; create `metadata_versions` table.
- [ ] Drive service: request extra fields; map to `MediaFile`; set dims from Drive metadata when present.
- [ ] Repos: `MetadataRepository.upsert`; new `MetadataVersionRepository`.
- [ ] CLI: `reprocess_all` with `--upsert`, `--archive-existing`, `--clear-first`, `--limit`.
- [ ] Claude/local prompts: tighten JSON-only, unify keys; add optional consensus.
- [ ] API: versions endpoints; capture version on update; revert endpoint.
- [ ] Frontend: detail page full display; editing UI; versions UI; filters default/open tweaks; ensure default sort.
- [ ] Docs: update `README.md`, `PROGRESS.md` with new workflow and commands.

### Useful Commands
```bash
# Migrate DB locally
python -m image_processor.cli.main init_db

# Count files to estimate scale
python -m image_processor.cli.main count_files --folder-id <DRIVE_FOLDER_ID>

# Discover any new files (optional step if structure changed)
python -m image_processor.cli.main discover --folder-id <DRIVE_FOLDER_ID>

# Dry-run reprocess a subset
python -m image_processor.cli.main reprocess_all --upsert --limit 25

# Full reprocess with version archiving
python -m image_processor.cli.main reprocess_all --archive-existing --upsert
```


