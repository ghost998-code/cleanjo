# Real-time Report Synchronization Design

This document outlines the architectural and code changes required to move from a poll-based architecture to a real-time event-driven architecture using Kafka, WebSockets, and React Query.

## 1. Backend Database & API
- **Soft-Delete Implementation**:
    - Update `Report` model to include `updated_at` (datetime) and `deleted_at` (datetime, nullable).
    - Apply `where(Report.deleted_at.is_(None))` filter to all `GET` routes in `backend/app/api/routes/reports.py`.
    - Update `delete_report` to set `deleted_at` instead of hard deleting.
- **Event Publishing**:
    - Centralize Kafka event publishing in `backend/app/api/routes/reports.py` for all `POST` (create), `PATCH` (status change), and `DELETE` (soft-delete) actions.
    - Message format: `{"type": "CREATED" | "UPDATED" | "DELETED", "data": <ReportDetail>, "timestamp": ISO8601}`.

## 2. Standalone WebSocket Bridge (`ws_bridge.py`)
- Create a standalone service (`backend/ws_bridge.py`) that:
    - Acts as a Kafka Consumer for the `report.events` topic.
    - Acts as a FastAPI WebSocket server.
    - Implements an auth check using the JWT secret shared with the main backend.
    - Manages active client connections: `Map<user_id, List<WebSocket>>`.
    - Dispatches received Kafka messages to the appropriate WebSocket client based on `report.user_id` or `assigned_to` fields.

## 3. Web Portal (React + TanStack Query)
- **Real-time Hook**: Create `useReportWebSocket` hook that:
    - Connects to the `ws_bridge.py` service.
    - On receipt of a message:
        - `CREATED`: Uses `queryClient.setQueryData` to add to the existing reports list.
        - `UPDATED`: Compares `updated_at` and updates the existing report record in the cache.
        - `DELETED`: Filters the list to remove the record.
- **Integration**: Update `ReportsPage.tsx` to utilize this hook to maintain synchronization without manual refresh.

## 4. Mobile App (Flutter)
- **Eager Submission**:
    - Modify the "Submit Report" button logic in `create_report_page.dart`.
    - Immediate `POST` to backend:
        - On `201 Created`: UI success, discard local draft.
        - On `Error`: Queue to `SyncService` (local Hive) for background retry.
    - Ensure `SyncService` maintains its existing background periodic sync for failed/offline reports.

## 5. Sequence of Implementation
1.  **Backend Migration**: Apply database schema changes (Alembic).
2.  **Backend Logic**: Update `reports.py` to support soft-delete and Kafka event publishing.
3.  **Bridge Development**: Build `ws_bridge.py` and ensure authentication validation is consistent.
4.  **Web Frontend**: Integrate `useWebSocket` hook into `ReportsPage`.
5.  **Mobile Frontend**: Refactor report submission to be eager.
