## Phase 1: Backend runtime config endpoint

- Added backend runtime settings for `MAX_REPORT_PHOTOS` and tightened the default `GPS_MAX_ACCURACY_METERS` to `10.0` in `backend/app/core/config.py`.
- Added `GET /api/v1/config/mobile` (also available under the legacy `/api/config/mobile` prefix) returning:
  - `max_report_photos`
  - `gps_max_accuracy_meters`
- Added a dedicated response schema in `backend/app/api/schemas/config.py` and wired the new router into the main API router.
- Updated `backend/.env.example` with the new report capture environment variables.

### Files changed

- `backend/app/core/config.py`
- `backend/app/api/schemas/config.py`
- `backend/app/api/schemas/__init__.py`
- `backend/app/api/routes/config.py`
- `backend/app/api/routes/__init__.py`
- `backend/app/api/__init__.py`
- `backend/.env.example`

### Notes for review

- I did not change report creation behavior yet; this phase only exposes runtime config.
- I left `backend/.env` untouched to avoid changing your local environment unexpectedly; defaults now cover the intended values unless you override them.

## Phase 2: Backend schema for multi-photo reports

- Added a new `ReportPhoto` SQLAlchemy model backed by a `report_photos` table.
- Linked `Report` to many photos through `Report.photos` while keeping legacy `Report.image_url` unchanged for incremental migration.
- Added per-photo fields needed for later upload and validation phases:
  - `image_url`
  - `source_type`
  - `latitude`
  - `longitude`
  - `gps_accuracy`
  - `captured_at`
  - `exif_latitude`
  - `exif_longitude`
  - `exif_accuracy`
  - `exif_captured_at`
  - `created_at`
- Added Alembic migration `005_add_report_photos` with:
  - foreign key to `reports`
  - `CASCADE` delete behavior from report to child photos
  - indexes on `report_id` and `created_at`
  - a DB check constraint restricting `source_type` to `camera` or `gallery`

### Files changed

- `backend/app/models/models.py`
- `backend/app/models/__init__.py`
- `backend/alembic/env.py`
- `backend/alembic/versions/005_add_report_photos.py`

### Notes for review

- I used a string column plus DB check constraint for `source_type` instead of introducing a new PostgreSQL enum type yet. That keeps this phase smaller while still enforcing valid values.
- I did not backfill existing `reports.image_url` rows into `report_photos`; the legacy column remains the current source for existing reports until a later phase updates creation and read paths.
- Migration `005_add_report_photos` was then hardened to handle an already-existing `report_photos` table. It now:
  - creates the table on fresh databases
  - adds the `ck_report_photos_source_type` check constraint if the table already exists without it
  - only creates indexes when missing

## Phase 3: Backend report schemas and responses

- Added `ReportPhotoResponse` to represent per-photo metadata in API responses.
- Extended `ReportDetailResponse` with `photos: list[ReportPhotoResponse]`.
- Updated the report detail route to eager-load `Report.photos` so the new response field is populated reliably.
- Left list responses unchanged for now to avoid expanding payload size until the multi-photo creation flow is in place.

### Files changed

- `backend/app/api/schemas/report.py`
- `backend/app/api/schemas/__init__.py`
- `backend/app/api/routes/reports.py`

### Notes for review

- `image_url` remains on `ReportResponse` as the legacy top-level cover image field.
- `photos` is currently exposed on the detail response only, which matches the implementation plan while minimizing response-shape changes for existing list consumers.

## Phase 4: Backend batch report creation API

- Extended `POST /reports` to accept repeated `photos` file fields plus a JSON `photo_metadata` form field.
- Kept legacy `image` / `photo` single-file fields working, while rejecting requests that mix legacy and batch file fields.
- Added `ReportPhotoCreate` as the backend contract for per-photo metadata.
- Added validation for:
  - at least one uploaded photo
  - photo count `<= MAX_REPORT_PHOTOS`
  - exact file-to-metadata count matching
  - required metadata when using the new `photos` batch field
  - per-photo GPS accuracy within `GPS_MAX_ACCURACY_METERS`
  - required EXIF GPS and EXIF accuracy for gallery photos
- New submissions that include `photo_metadata` now create `report_photos` child rows.
- `Report.image_url` is still populated from the first uploaded photo for backward compatibility.
- If shared report coordinates/timestamp are omitted in the batch flow, the report falls back to the first photo metadata for `latitude`, `longitude`, `gps_accuracy`, and `reported_at`.

### Files changed

- `backend/app/api/schemas/report.py`
- `backend/app/api/schemas/__init__.py`
- `backend/app/api/routes/reports.py`

### Notes for review

- The backend now enforces the multi-photo request contract, but it still relies on the mobile client to extract EXIF values correctly and to label `source_type` honestly.
- Legacy single-photo requests without `photo_metadata` still work, but they do not create `report_photos` rows yet; that keeps old clients compatible during the transition.

## Phase 5: Legacy `Report.image_url` handling

- Chose the compatibility path from the plan: `report_photos` is the new primary multi-photo model, while `Report.image_url` remains temporarily as the legacy cover image field.
- Kept the create flow explicitly populating `Report.image_url` from the first uploaded photo so existing consumers continue to work during migration.
- Did not remove or repurpose `Report.image_url` yet; later phases can move consumers over incrementally without breaking current list/detail flows.

### Files changed

- `backend/app/api/routes/reports.py`

### Notes for review

- This phase intentionally avoids another response-shape change. The main implementation effect is locking in Option 1 from the plan: first photo becomes the legacy cover image, while `report_photos` carries the new multi-photo data.
- Legacy single-photo submissions still depend on `Report.image_url` unless they adopt the new metadata contract from phase 4.

## Phase 6: Mobile draft model redesign

- Added a dedicated mobile draft model in `mobile/lib/features/citizen/models/report_draft.dart` with:
  - `ReportDraft` for shared report fields
  - `ReportPhotoDraft` for per-photo fields
- `ReportPhotoDraft` now carries the per-photo state needed for later phases:
  - `filePath`
  - `sourceType`
  - `latitude`
  - `longitude`
  - `accuracy`
  - `capturedAt`
  - `exifValidationPassed`
- Refactored `CreateReportPage` to keep its in-memory report state in a `ReportDraft` instead of separate top-level garbage-type/severity/image variables.
- Kept the current UI behavior effectively single-photo for now, but the page state is now modeled as a list of photo drafts so later multi-photo capture/review work can build on it without another state-model rewrite.
- Current submission and offline fallback paths now derive shared report fields from the draft snapshot.

### Files changed

- `mobile/lib/features/citizen/models/report_draft.dart`
- `mobile/lib/features/citizen/pages/create_report_page.dart`

### Notes for review

- This phase does not yet redesign the offline queue model from `PendingReport`; that is still reserved for phase 11.
- Gallery photos are only marked in draft state with `sourceType = 'gallery'` and `exifValidationPassed = false` for now. Real EXIF parsing/validation belongs to the later EXIF phases.
- Verification found one Flutter deprecation info on `DropdownButtonFormField.value`, but no errors in the files changed for this phase.

## Phase 7: Mobile config fetch and cache

- Added `MobileRuntimeConfig` with the mobile runtime values needed by later capture phases:
  - `maxReportPhotos`
  - `gpsMaxAccuracyMeters`
- Added `MobileConfigService` to:
  - load cached config from Hive
  - fetch fresh config from `GET /config/mobile`
  - cache the latest successful response locally
  - fall back to safe defaults when there is no cache or fetch fails
- Added `ApiEndpoints.mobileConfig` for the new backend config endpoint.
- Updated dependency initialization to open a dedicated `app_config` Hive box and register `MobileConfigService`.
- Updated app startup to initialize the mobile config service before `runApp`, so the app warms cached/fresh config values as it launches.
- Also explicitly opened the `pending_reports` Hive box during dependency init, which matches the existing `SyncService` assumption and prepares later offline phases.

### Files changed

- `mobile/lib/core/config/mobile_runtime_config.dart`
- `mobile/lib/core/config/mobile_config_service.dart`
- `mobile/lib/core/network/api_endpoints.dart`
- `mobile/lib/core/di/injection.dart`
- `mobile/lib/main.dart`

### Notes for review

- This phase adds config fetching and caching only; the capture flow is not yet enforcing `maxReportPhotos` or `gpsMaxAccuracyMeters`. That happens in later mobile phases.
- If the backend call fails, startup still succeeds using cached values or the fallback defaults of `15` photos and `10m` max GPS accuracy.

## Phase 8: Mobile multi-photo capture and review flow

- Rebuilt `CreateReportPage` around a multi-photo draft flow instead of a single-image placeholder.
- The report page now opens the camera directly on first entry.
- Users can now:
  - capture additional camera photos
  - add multiple gallery photos
  - review the current batch in-page
  - remove individual photos before submission
  - see the current count against the configured maximum
- Enforced the configured `maxReportPhotos` limit from `MobileConfigService` in the page flow.
- Submit is now disabled when there are no photos in the batch.
- Added a page-local batch submission path that sends repeated `photos` fields plus `photo_metadata` JSON when more than one photo is present, while still using the legacy single-file upload path for one-photo submissions.

### Files changed

- `mobile/lib/features/citizen/pages/create_report_page.dart`

### Notes for review

- This phase focuses on the capture/review UX and the page-level submission flow. The reusable API-client abstraction for multipart batch submission is still intentionally deferred to the later API-client phase.
- Gallery photos are currently added to the review batch without EXIF parsing yet. Strict EXIF validation is still reserved for the later metadata phases.
- Offline fallback still only queues the first photo because the offline queue redesign is a separate later phase.
