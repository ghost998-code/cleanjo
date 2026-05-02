# On-Device Inference + Backend Persistence Plan
## Goal
Keep all AI inference on the phone, but continue using the backend as the source of truth for reports, photos, metadata, and inference results.
## Product Direction
1. Inference runs only on the mobile device.
2. Backend does not classify or re-run ML on uploaded reports.
3. Mobile uploads:
   - photos
   - shared report fields
   - per-photo GPS/EXIF metadata
   - per-photo inference results
   - optional report-level inference summary
4. Backend stores:
   - report data
   - photo files
   - per-photo metadata
   - per-photo inference results
   - optional report-level inference summary
5. Backend file storage should not depend on Cloudinary.
6. Offline mobile drafts must preserve inference results and sync them later unchanged.
## Scope Changes From Current Work
### Keep
- multi-photo backend model and API direction
- backend as report storage system
- mobile multi-photo draft/capture flow
- mobile runtime config fetch/cache
- offline sync direction
### Change
- remove backend-side ML responsibility
- remove Cloudinary as primary media storage dependency
- add mobile inference pipeline
- add backend persistence for inference metadata
- expand mobile offline payload to include inference results
## Architecture
### Mobile responsibilities
- capture/import photos
- read/write EXIF as required
- run on-device model inference per photo
- store inference results in draft state
- upload report batch plus inference payload
- preserve exact payload offline for later sync
### Backend responsibilities
- validate request structure and metadata
- store uploaded photos
- store report + photo + inference metadata
- expose inference results in report responses
- never run server-side inference
## Inference Data Model
## Per-photo inference result
Recommended fields:
- `predicted_category`
- `prediction_confidence`
- `predicted_severity` (optional)
- `severity_confidence` (optional)
- `labels` or `top_predictions` (optional structured list)
- `model_name`
- `model_version`
- `inference_ran_at`
- `inference_device` (optional)
- `inference_source = "mobile"`
## Optional report-level summary
Recommended fields:
- `summary_category`
- `summary_confidence`
- `summary_strategy`
- `derived_from_photo_count`
- `model_version`
### Summary strategy recommendation
Use per-photo inference as primary truth and optionally compute a report-level summary on mobile using a deterministic rule, for example:
- highest-confidence photo wins
- or majority category across photos
- tie-break by highest confidence
## Backend Implementation Plan
## 1. Remove backend AI responsibility
### Purpose
Ensure backend is only a storage/validation layer.
### Changes
- stop relying on backend ML worker for report classification
- remove or disable Kafka-triggered ML flow if it only supports inference
- remove backend TensorFlow dependency if no server-side ML remains
- keep backend eventing only if still needed for non-ML features
### Files likely involved
- `backend/app/workers/ml_worker.py`
- `backend/app/workers/__init__.py`
- `backend/app/services/kafka.py`
- `backend/app/api/routes/reports.py`
- `backend/requirements.txt`
- `README.md` or run instructions
## 2. Replace Cloudinary with backend-managed storage
### Purpose
Store uploaded media without third-party media hosting.
### Recommended path
Use local/server-managed file storage as the default backend storage path.
### Changes
- remove Cloudinary as required dependency
- keep or refine local file storage under backend-managed uploads directory
- serve uploaded files from backend
- ensure returned URLs remain stable
### Notes
- this can later be swapped for S3-compatible object storage if needed
- backend should own file naming and file paths
### Files likely involved
- `backend/app/services/image.py`
- `backend/app/main.py`
- `backend/app/core/config.py`
- `backend/requirements.txt`
- `backend/.env.example`
## 3. Extend backend database for inference persistence
### Purpose
Store inference results sent from mobile.
### Recommended shape
Add inference fields to `ReportPhoto`, since inference is per-photo.
### Suggested `report_photos` additions
- `predicted_category`
- `prediction_confidence`
- `predicted_severity` (nullable)
- `severity_confidence` (nullable)
- `model_name`
- `model_version`
- `inference_ran_at`
- `inference_source` default `"mobile"`
- `top_predictions` JSON nullable
### Optional report-level summary storage
Either:
1. add summary fields on `Report`
2. or add a small `report_inference_summary` child table
### Recommendation
Start with nullable summary fields on `Report` to keep implementation smaller.
Suggested `Report` additions if summary is desired:
- `inference_summary_category`
- `inference_summary_confidence`
- `inference_summary_strategy`
- `inference_model_version`
### Files likely involved
- `backend/app/models/models.py`
- Alembic migration(s)
- `backend/app/models/__init__.py`
- `backend/alembic/env.py`
## 4. Extend backend schemas and responses
### Purpose
Expose inference results through the API.
### Changes
Add inference fields to photo response schema.
Add optional report-level summary fields to report detail response if implemented.
### Files likely involved
- `backend/app/api/schemas/report.py`
## 5. Extend backend report creation API
### Purpose
Accept per-photo inference metadata from mobile.
### Request design
Continue using multipart form-data with:
- repeated `photos`
- `photo_metadata` JSON array
- optional `report_inference_summary` JSON object
### Extend each `photo_metadata` entry with inference fields
Example shape:
```json
{
  "source_type": "camera",
  "latitude": 31.95,
  "longitude": 35.91,
  "gps_accuracy": 4.2,
  "captured_at": "2026-05-01T12:00:00Z",
  "exif_latitude": 31.95,
  "exif_longitude": 35.91,
  "exif_accuracy": 4.2,
  "exif_captured_at": "2026-05-01T12:00:00Z",
  "predicted_category": "mixed",
  "prediction_confidence": 0.91,
  "predicted_severity": "medium",
  "severity_confidence": 0.76,
  "model_name": "garbage_classifier",
  "model_version": "1.0.0",
  "inference_ran_at": "2026-05-01T12:00:02Z",
  "top_predictions": [
    { "label": "mixed", "confidence": 0.91 },
    { "label": "household", "confidence": 0.07 }
  ]
}
Backend validation rules
- accept only mobile-provided inference
- validate required inference fields for each photo
- validate confidence ranges
- do not recompute inference
- persist exactly what mobile sent
Files likely involved
- backend/app/api/routes/reports.py
- backend/app/api/schemas/report.py
Mobile Implementation Plan
6. Add on-device inference stack
Purpose
Run image classification entirely on device.
Recommended dependency direction
Use a small TFLite model with Flutter integration.
Likely package:
- tflite_flutter
Optional helpers depending on preprocessing needs:
- image
- tflite_flutter_helper if compatible/desired
Changes
- add inference service
- load model from assets
- preprocess image
- run inference
- map outputs to backend categories/severity values
- return structured inference result
Files likely involved
- mobile/pubspec.yaml
- new files under something like:
  - mobile/lib/core/inference/
  - mobile/assets/models/
7. Extend mobile draft models for inference
Purpose
Persist per-photo inference in draft state before submission.
Changes
Add inference fields to ReportPhotoDraft.
Suggested fields:
- predictedCategory
- predictionConfidence
- predictedSeverity
- severityConfidence
- topPredictions
- modelName
- modelVersion
- inferenceRanAt
Optionally add report-level summary fields to ReportDraft.
Files likely involved
- mobile/lib/features/citizen/models/report_draft.dart
8. Run inference after photo capture/import
Purpose
Ensure every photo draft has inference metadata before submission.
Behavior
- after camera capture: run inference on captured photo
- after gallery import: run inference on each accepted photo
- store inference result on each photo draft
- if inference fails:
  - either block submission
  - or mark photo invalid until retried
Recommendation
Block submission for photos that do not have completed inference results, unless you explicitly want inference to be optional.
UX
Show for each photo:
- predicted category
- confidence
- optional predicted severity
- loading state while inference runs
- failure state if inference fails
Files likely involved
- mobile/lib/features/citizen/pages/create_report_page.dart
- new inference service files
9. Compute optional report-level summary on mobile
Purpose
Provide a quick aggregate interpretation for backend/UI use.
Changes
- derive a report-level summary from per-photo results
- store it in draft state
- include it in submission payload if desired
Recommendation
Use highest-confidence winning category as phase 1 summary logic.
10. Extend mobile submission payload
Purpose
Send per-photo inference data to backend.
Changes
- add inference fields to photo_metadata
- add optional report_inference_summary
- keep order aligned with photos
Files likely involved
- mobile/lib/features/citizen/pages/create_report_page.dart
- later reusable API client helper if extracted
11. Extend offline queue for multi-photo + inference
Purpose
Preserve inference and metadata across offline retries.
Changes
Replace old queue shape with:
- shared report fields
- list of photo file paths
- per-photo metadata including inference
- optional report-level summary
- created-at timestamp
- local draft ID / sync state
Files likely involved
- mobile/lib/core/offline/sync_service.dart
Requirements
- do not rerun inference during sync if already present
- sync the stored payload as-is
- remove pending entry only after backend confirms success
12. Show inference results in UI
Purpose
Expose mobile AI output in report review and report detail screens.
Changes
Mobile capture/review page should show:
- per-photo predicted category
- confidence
- optional severity prediction
Report detail page can show:
- per-photo inference result
- optional report summary
- clear labeling that inference came from device
Files likely involved
- mobile/lib/features/citizen/pages/create_report_page.dart
- report detail/map detail UI files
Data Contract Recommendation
Backend categories
Mobile model outputs should map to backend-supported categories only:
- household
- construction
- green
- hazardous
- electronic
- bulky
- mixed
- other
Confidence
Use normalized float values in range 0.0 - 1.0.
Versioning
Always send:
- model_name
- model_version
so backend-stored inference can be audited later.
Validation Checklist
Backend
- stores uploaded files without Cloudinary
- accepts per-photo inference metadata
- stores inference fields in DB
- returns inference results in report detail response
- does not run TensorFlow/server ML
- does not depend on Kafka for inference
Mobile
- model loads on device
- inference runs after capture
- inference runs for gallery imports
- draft state preserves per-photo inference
- batch submission includes inference payload
- offline queue preserves inference payload
- reconnect sync submits same stored inference payload
Integration
- backend receives report + photos + metadata + inference
- report detail returns photo inference results
- map/list flows do not break
- no server-side reclassification occurs
Suggested Execution Order
1. Remove backend ML responsibility
2. Replace Cloudinary with backend-managed storage only
3. Add backend DB fields for per-photo inference
4. Extend backend schemas/responses
5. Extend backend create-report API for inference payload
6. Add mobile on-device inference service and model asset
7. Extend mobile draft models with inference fields
8. Run inference after capture/import
9. Add report-level summary logic on mobile
10. Send inference payload in submission
11. Extend offline queue with inference results
12. Surface inference results in UI
13. Run end-to-end verification
Risks / Attention Points
1. Model-to-backend label mapping
- mobile model labels must map cleanly into backend categories
- define mapping explicitly in code, not ad hoc in UI
2. Multi-photo inference latency
- running inference for several photos may delay review flow
- queue inference work and show progress per photo
3. Offline payload size
- per-photo predictions and top-k outputs increase payload size
- keep top_predictions concise
4. Model version drift
- reports may be created from different app/model versions
- version fields are required for traceability
5. Trust model
- backend will trust mobile inference payload
- this is acceptable if inference is advisory metadata, not a security boundary
Decision Summary
- inference is per-photo
- optional report-level summary is derived on mobile
- backend stores and returns inference metadata
- backend does not run ML
- backend remains source of truth for reports and uploads
- Cloudinary should be removed from the long-term architecture
If you want, I can next turn this into:
1. a file-by-file implementation checklist
2. a replacement execution order aligned with the phases already completed
3. an updated `multi_photo_report` addendum focused on on-device inference only
