# Multi-Photo Report Capture Plan
## Goal
Implement a report flow where one report can contain multiple photos, with:
- camera and gallery support
- per-photo metadata
- EXIF metadata preservation/write
- strict location validation
- offline queueing and reconnect sync
- one map pin per report
## Final Product Rules
1. One report can contain multiple photos.
2. Maximum photo count is dynamic and controlled by backend environment configuration.
3. Mobile should fetch that limit from a backend config endpoint and cache it.
4. Camera photos must use the user's current GPS location only.
5. Gallery photos are allowed.
6. Gallery photos must be rejected unless EXIF contains:
   - GPS coordinates
   - accuracy value
   - accuracy within allowed range
7. Any photo must be rejected if accuracy is greater than `10m`.
8. Shared fields like category, severity, and description apply to the whole batch/report.
9. Users can review and remove photos before submission.
10. Offline submission must work, and reconnecting should trigger sync automatically.
11. Metadata must exist in two places:
   - EXIF in the image file
   - backend-stored metadata in the database
## Current Codebase Findings
### Mobile
- `mobile/lib/features/citizen/pages/create_report_page.dart`
  - current flow supports only one image
  - supports both camera and gallery
  - captures current location once
  - submits one image only
- `mobile/lib/core/offline/sync_service.dart`
  - queue model supports only one `imagePath`
  - sync is not wired to connectivity restore yet
- `mobile/lib/core/di/injection.dart`
  - Hive is initialized, but the pending box is not clearly opened here
- `mobile/lib/main.dart`
  - no reconnect-triggered sync wiring found
- `mobile/lib/features/map/pages/map_page.dart`
  - map is already report-level, which matches the desired model
### Backend
- `backend/app/models/models.py`
  - `Report` currently has one `image_url`
- `backend/app/api/routes/reports.py`
  - `POST /reports` accepts only one image field (`image` or `photo`)
  - already supports `gps_accuracy` and `reported_at`
  - already validates GPS accuracy against config
- `backend/app/core/config.py`
  - existing env-based config pattern already exists
  - current GPS max accuracy default is `50m`
- No current child table for multiple photos
## Implementation Plan
## 1. Add backend runtime config endpoint
### Purpose
Expose report capture rules to mobile at runtime.
### Changes
- Add a small config endpoint for mobile, for example:
  - `GET /config/mobile`
- Return:
  - `max_report_photos`
  - `gps_max_accuracy_meters`
- Add/update backend env vars:
  - `MAX_REPORT_PHOTOS=15`
  - `GPS_MAX_ACCURACY_METERS=10`
### Files likely involved
- `backend/app/core/config.py`
- backend API routing for config endpoint
- response schema file(s)
### Notes
- Mobile should cache this response locally for offline use.
- Backend remains the source of truth.
## 2. Extend backend database schema for multi-photo reports
### Purpose
Allow one report to own many photos.
### Changes
- Add a new `ReportPhoto` model/table linked to `Report`
- Keep `Report` as the parent submission record
### Suggested fields for `report_photos`
- `id`
- `report_id`
- `image_url`
- `source_type` (`camera` or `gallery`)
- `latitude`
- `longitude`
- `gps_accuracy`
- `captured_at`
- `exif_latitude`
- `exif_longitude`
- `exif_accuracy`
- `exif_captured_at`
- `created_at`
### Optional simplification
If duplicated EXIF/raw fields are unnecessary, store only normalized metadata fields and keep EXIF as file-level concern.
### Files likely involved
- `backend/app/models/models.py`
- Alembic migration(s)
- related schema exports/imports
## 3. Update backend report schemas and responses
### Purpose
Return photo collections with reports.
### Changes
- Add `ReportPhotoResponse`
- Add `photos: list[ReportPhotoResponse]` to report detail response
- Optionally expose a thumbnail/cover image for list responses
### Files likely involved
- `backend/app/api/schemas/report.py`
## 4. Update backend report creation API for batch upload
### Purpose
Allow one report submission with multiple images and per-photo metadata.
### Changes
- Extend `POST /reports` to accept:
  - shared report-level fields once
  - multiple uploaded files
  - per-photo metadata payload, likely JSON
- Validate:
  - at least one photo
  - photo count `<= MAX_REPORT_PHOTOS`
  - all photos must have valid metadata
  - all photos must have accuracy `<= GPS_MAX_ACCURACY_METERS`
  - camera photos must be based on current device GPS flow
  - gallery photos must contain EXIF GPS + EXIF accuracy
### Request design recommendation
Use multipart form data:
- shared text fields in form fields
- multiple photo files under one repeated field like `photos`
- one JSON field like `photo_metadata` containing per-photo metadata array
### Validation rules
- reject missing metadata entries
- reject mismatched file/metadata counts
- reject gallery image if GPS EXIF missing
- reject gallery image if accuracy EXIF missing
- reject any image with accuracy > `10m`
### Files likely involved
- `backend/app/api/routes/reports.py`
- `backend/app/api/schemas/report.py`
- upload helper logic if needed
## 5. Decide handling of legacy `Report.image_url`
### Recommendation
Use the new `report_photos` table as the primary source.
Options:
1. Keep `image_url` temporarily as the first photo for backward compatibility
2. Stop using `image_url` and migrate consumers immediately
### Recommended path
Option 1 during implementation to reduce breakage, then clean up later if desired.
## 6. Redesign the mobile report draft model
### Purpose
Represent one report with many photos and metadata.
### Changes
Replace the current single-image assumptions with:
- one report draft
- shared fields:
  - category
  - severity
  - description
  - address if used
- list of photo drafts:
  - local file path
  - source type
  - latitude
  - longitude
  - accuracy
  - captured at
  - EXIF validation status
### Files likely involved
- `mobile/lib/features/citizen/pages/create_report_page.dart`
- `mobile/lib/core/offline/sync_service.dart`
- possibly new mobile models/helpers
## 7. Add mobile config fetch + cache
### Purpose
Drive capture limit and validation from backend config.
### Changes
- Fetch config when app starts or before entering report flow
- Cache locally for offline use
- Use cached values when offline
- If config fetch fails and no cache exists, use safe fallback defaults
### Mobile values to use
- `max_report_photos`
- `gps_max_accuracy_meters`
### Files likely involved
- API client / endpoints
- app initialization or report flow entry
- local cache mechanism
## 8. Rebuild mobile capture flow
### Purpose
Support up to N photos in one report.
### UX flow
1. User taps `Report Garbage`
2. Camera opens directly
3. User captures one or more photos
4. User can also add from gallery
5. User reaches a review screen
6. User can:
   - remove photos
   - add more photos
   - see current count vs max
   - fill shared report details
7. User submits one report containing the full batch
### Behavior
- hard stop at configured max photo count
- disable submit if no valid photos remain
### Files likely involved
- `mobile/lib/features/citizen/pages/create_report_page.dart`
- possible supporting widgets/components
## 9. Implement camera metadata capture and EXIF writing
### Purpose
Ensure camera photos are tied to current user location and preserved in-file.
### Changes
- Before capture/add:
  - request location permission
  - get current GPS
  - require accuracy `<= 10m`
- For each camera photo:
  - capture timestamp
  - assign current lat/lng
  - assign current accuracy
  - write these values into EXIF
  - also store them in app state for backend submission
### Validation
- reject/stop if current GPS accuracy is worse than allowed
- no manual map-based location editing
### Likely new dependency area
An EXIF read/write package will be needed on mobile.
## 10. Implement gallery import metadata parsing and validation
### Purpose
Allow gallery imports only when trustworthy location metadata exists.
### Changes
- Read EXIF metadata from selected gallery images
- Extract:
  - latitude
  - longitude
  - accuracy
  - timestamp if available
- Reject image if:
  - GPS EXIF missing
  - accuracy EXIF missing
  - accuracy out of range
### UX
- show clear rejection message per failed image
- allow remaining valid images to stay in the batch
## 11. Redesign offline queue for multi-photo reports
### Purpose
Keep one pending report with many photos and metadata.
### Changes
Replace `PendingReport.imagePath` with:
- list of photo file paths
- per-photo metadata list
- shared report fields
- created-at timestamp
- possibly local draft ID / sync state
### Files likely involved
- `mobile/lib/core/offline/sync_service.dart`
### Requirements
- preserve all local paths until sync succeeds
- remove pending draft only after backend confirms success
## 12. Wire reconnect-triggered sync properly
### Purpose
Actually perform sync when connectivity returns.
### Changes
- open/init the pending reports Hive box properly
- sync on app startup
- subscribe to connectivity changes
- trigger `syncPendingReports()` when network is restored
- avoid duplicate concurrent sync runs
### Files likely involved
- `mobile/lib/core/offline/sync_service.dart`
- `mobile/lib/core/di/injection.dart`
- `mobile/lib/main.dart`
## 13. Extend mobile API client for multipart batch submission
### Purpose
Support multi-file report upload.
### Changes
- add an API client method for multi-file multipart report submission
- send:
  - repeated photo file fields
  - shared form fields
  - metadata JSON field
### Files likely involved
- `mobile/lib/core/network/api_client.dart`
## 14. Update report details and map-related UI
### Purpose
Display multi-photo reports cleanly.
### Changes
- report details should show photo gallery/carousel/grid
- map marker bottom sheet/detail should show report photo gallery
- still keep one marker per report location
### Files likely involved
- `mobile/lib/features/map/pages/map_page.dart`
- `mobile/lib/features/citizen/pages/my_reports_page.dart`
- any detail sheet widgets involved
## 15. Verification checklist
### Backend
- migration applies cleanly
- report creation accepts valid multi-photo submissions
- config endpoint returns correct env-backed values
- invalid gallery EXIF is rejected
- accuracy > `10m` is rejected
- count > max is rejected
### Mobile
- camera opens from report entry
- multiple captures work
- gallery import works for valid images
- invalid gallery images are rejected with clear feedback
- EXIF is written for camera images
- review/remove flow works
- offline draft is stored
- reconnect triggers sync
- successful sync removes pending draft
### Integrated
- report appears on map as one pin
- report details show all photos
- report list still works
- existing single-photo assumptions do not break other flows
## Suggested Execution Order
1. Add backend config env + config endpoint
2. Add `ReportPhoto` model and migration
3. Update backend report schemas
4. Update backend `POST /reports` for multi-file upload
5. Add mobile config fetch/cache
6. Redesign mobile draft model
7. Add EXIF read/write support
8. Rebuild report capture/review flow
9. Extend offline queue model
10. Wire reconnect-triggered sync
11. Update detail/map views
12. Run end-to-end verification
## Risks / Attention Points
1. EXIF accuracy availability is inconsistent across gallery images
- This is intended to be strict per product rule
- Many gallery images may be rejected
2. Backward compatibility with existing report consumers
- Existing code assumes one image in some places
- Any response/model change should be reviewed carefully
3. Offline batch upload complexity
- must preserve local photo paths
- must handle partial failures safely
- avoid uploading duplicate reports on retry
4. Multipart file-to-metadata alignment
- backend and mobile must agree on ordering/index mapping
- should validate exact match between files and metadata records
5. Hive initialization
- current queue path should be reviewed to ensure the box is opened before use
## Open Implementation Notes
1. Mobile will likely need one or more new packages for EXIF read/write.
2. A clear metadata JSON contract between mobile and backend should be defined before coding.
3. Consider whether `Report.image_url` remains as a legacy cover image during migration.
If you want, I can next turn this into a shorter build-agent version with:
1. exact file-by-file task list
2. acceptance criteria
3. implementation order with checkpoints
