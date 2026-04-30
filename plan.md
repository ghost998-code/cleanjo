Implementation Plan
Below is a staged plan focused only on what is still missing relative to your specification, based on the current codebase.
1. Align Architecture First
1. Decide target backend contract.
   Current repo uses FastAPI at /api, while your spec says Node/Django and /api/v1.
   Recommendation: keep the existing FastAPI backend and migrate routes to /api/v1 instead of replacing the backend stack.
2. Define canonical enums and field names across backend, web, and mobile.
   Current status/severity/category model is simpler than the spec and differs between clients.
2. Backend Foundation
1. Normalize API versioning and auth contracts.
   Move/alias all endpoints to /api/v1.
   Standardize refresh-token request format.
   Standardize login/register payloads for both web and mobile.
2. Expand database schema to match the report.
   Add to users: last_login.
   Expand reports with gps_accuracy, reported_at, video_url, category, terrain, reachability, density, amount_estimate, admin_notes.
   Add feedback table.
   Rename or map status_history to the spec’s report_status_history.
3. Update enums/workflows.
   Replace current status flow with:
   submitted -> under_review -> scheduled -> cleaned -> rejected
   Add terrain, reachability, density, amount-estimate vocabularies.
4. Add migration scripts for all above changes.
5. Add structured validation.
   Enforce required fields, description max length, GPS accuracy rules, file type/size limits, role checks.
6. Add audit logging.
   Log user_id, action, report ID, status changes, and admin operations.
7. Add rate limiting.
   Apply to auth, OTP, report creation, and feedback endpoints.
8. Add deletion/privacy flows.
   User delete-account request and cascading/anonymized cleanup policy.
3. Authentication and Identity
1. Implement registration with email or phone + OTP verification.
   Current backend partially supports phone OTP and email/password, but not the spec’s unified flow.
2. Implement login with email or phone + password.
   Current mobile uses email/password; web uses phone OTP; these need one shared contract.
3. Implement password reset.
   Missing entirely.
4. Store JWT/refresh token policy per spec.
   Access token 24h, refresh token 30d.
5. Update last_login on successful login.
6. Add optional web 2FA as a later phase.
   Mark as optional MVP+ because your spec says optional.
4. Media and Storage
1. Implement server-side image compression and path strategy.
   Store under /reports/{year}/{month}/{uuid}.jpg or equivalent object-storage key layout.
2. Add video upload support.
   Optional video up to 15s.
3. Choose storage backend.
   Recommendation: start with S3-compatible storage or local dev + S3 in production.
   Current code only supports Cloudinary.
4. Validate file uploads securely.
   MIME checks, extension checks, size limits, image/video processing safeguards.
5. Reporting Workflow Backend
1. Update POST /reports to accept full multipart payload.
   photo, video?, lat, lng, accuracy, timestamp, description, category, severity, terrain, reachability, density, amount.
2. Return response per spec.
   { id, status: "Submitted" } or canonical lowercase equivalent.
3. Add GET /reports/me.
   Current code uses generic /reports; add explicit user-history endpoint.
4. Add GET /reports/{id} with full detail and status history.
   Current version is partial.
5. Add PUT /reports/{id}/status.
   Include comment and role enforcement.
6. Add POST /reports/{id}/feedback.
   Missing entirely.
7. Add reverse geocoding integration.
   Current mobile does device-side geocoding; backend should support or persist locality for consistency.
6. Admin and Inspector Backend
1. Implement filtered admin report listing per spec.
   Support bbox, severity, date range, category, status, terrain.
2. Add inspector/admin notes on reports.
3. Add assignment workflow.
   Current model has assigned_to, but event publication and complete flow are incomplete.
4. Add bulk import endpoint.
   POST /admin/bulk-import for CSV preload locations.
5. Add export endpoints.
   CSV export for report tables.
6. Add analytics endpoints.
   Heatmap/density clusters, reports per area, average response time, priority zones.
7. Mobile App
1. Replace current auth UX with spec-compliant flow.
   Registration: email or phone + OTP.
   Login: email/phone + password.
   Password reset.
2. Fix auth persistence.
   Current token/session restore is incomplete.
3. Rework home flow to match spec exactly.
   Home buttons: Take Photo, View Previous Reports, Settings.
4. Rebuild capture flow.
   Open camera.
   Force GPS permission.
   Capture latitude, longitude, accuracy, timestamp.
   Warn if accuracy >20m and allow manual confirm.
   Reject >50m unless override.
5. Expand details form to full required schema.
   Photo compression to <1MB JPEG.
   Optional video max 15s.
   Description, category, severity, terrain, reachability, density, amount estimate.
6. Rebuild submit step.
   Preview map pin.
   HTTPS POST.
   Confirmation with report ID.
7. Upgrade My Reports.
   Thumbnail, status badge, date, detail view, status history, pull-to-refresh.
8. Implement Settings.
   Arabic/English toggle, logout, delete account, privacy policy.
9. Finish offline draft save and auto-sync.
   Current sync queue exists but is not fully wired or initialized.
10. Add role-based inspector features.
   Status updates, field notes, assigned reports.
8. Web Dashboard
1. Standardize login flow to email/password.
   Optional 2FA can be phase 2.
2. Add missing admin route coverage.
   Users page exists but is not routed.
3. Replace Leaflet/OpenStreetMap with Google Maps if you want strict spec compliance.
   If cost-sensitive MVP is preferred, keep current map stack and document the deviation.
4. Build authority-oriented main map view.
   Severity-colored markers, clustering, date/category/status/terrain filters, photo/detail/history popup.
5. Expand report management table.
   Search, CSV export, assign inspector, change status, admin notes.
6. Implement decision-support dashboards.
   Density heatmap, reports per area, average response time, priority zones.
7. Make settings/preferences actually drive UI behavior.
   Current settings are mostly persisted but unused.
8. Add real-time or periodic refresh.
   Current dashboard is not real-time.
9. Notifications and Async Processing
1. Replace placeholder notification worker.
   SMS/email/push provider integration.
2. Publish all needed events.
   Report created, assigned, status changed, feedback added if needed.
3. Decide ML scope.
   Current worker is a stub.
   Recommendation: remove ML from MVP scope unless classification is mandatory.
4. If kept, replace random classification with real inference service and confidence handling.
10. Mapping
1. Decide mapping platform.
   Spec says Google Maps SDK/JS API.
   Current stack uses OpenStreetMap/Leaflet/flutter_map.
2. Add reverse geocoding service layer.
3. Add server-supported GeoJSON/cluster responses for large datasets.
4. Add bbox/date/category/status/terrain filtering to map endpoints.
11. Security and Compliance
1. Enforce HTTPS in deployment topology.
2. Tighten CORS and auth middleware.
3. Sanitize uploads and text inputs.
4. Add user deletion/export privacy operations.
5. Add audit trails for admin/inspector actions.
6. Review Jordanian privacy-policy text and retention policy.
12. Testing and Quality
1. Add backend tests.
   Auth, report creation, status changes, role access, validation, feedback, bulk import.
2. Add mobile tests.
   Auth flow, offline drafts, submission flow, GPS accuracy guardrails.
3. Add web tests.
   Login, map filters, report table actions, analytics rendering.
4. Add performance checks.
   p95 GET latency, upload timing, pagination behavior.
5. Add end-to-end scenarios.
   Citizen creates report -> inspector updates status -> admin sees analytics -> citizen sees updated history.
13. Documentation and Deliverables
1. Update OpenAPI docs to match final contracts.
2. Add user manual and admin manual.
3. Add architecture diagrams.
4. Update Docker Compose for production-like local setup.
   Include backend, DB, Redis, storage emulator if needed.
5. Add release/build instructions for APK/IPA and web deployment.
Suggested Execution Order
1. Backend contract and schema alignment
2. Auth unification
3. Report workflow backend
4. Mobile reporting flow
5. Web admin/report management
6. Notifications, analytics, bulk import/export
7. Security hardening
8. Testing and docs
Highest-Risk Gaps
1. Auth mismatch across backend, web, and mobile
2. Report schema too small for the required workflow
3. Offline sync is only partial
4. Web dashboard is missing several core admin features
5. Storage/media pipeline does not support the required image/video rules
Recommendation
Use a phased delivery:
1. MVP
   Unified auth, full report schema, mobile report flow, user history, inspector status updates, admin map/table, migrations, OpenAPI
2. Phase 2
   Feedback, bulk import, CSV export, analytics improvements, notifications
3. Phase 3
   Optional 2FA, ML classification, deeper compliance tooling, advanced performance tuning
