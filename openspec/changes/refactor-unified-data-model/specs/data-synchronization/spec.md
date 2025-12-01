## ADDED Requirements

### Requirement: Unified Data Model

The system SHALL provide a unified data model (`UnifiedOvertimeRecord`) that integrates attendance data from multiple SSP pages into a single coherent structure.

#### Scenario: Merge attendance anomaly and personal records

- **GIVEN** attendance anomaly data from `FW99001Z.aspx#tabs-2`
- **AND** personal record data from `FW21003Z.aspx`
- **WHEN** `DataSyncService.sync_all()` is called
- **THEN** system SHALL merge records by date
- **AND** return `List[UnifiedOvertimeRecord]` with integrated fields:
  - Punch times from anomaly data
  - Submission details from personal records
  - Calculated overtime hours
  - Submission status and cumulative totals

#### Scenario: Handle missing personal record

- **GIVEN** an attendance anomaly record exists
- **AND** no corresponding personal record exists (not yet submitted)
- **WHEN** merging data
- **THEN** system SHALL create `UnifiedOvertimeRecord` with:
  - `submitted = False`
  - `submission_content = None`
  - `submission_status = None`
  - All punch and anomaly data populated

### Requirement: Data Synchronization Service

The system SHALL provide a `DataSyncService` that manages all SSP data fetching with intelligent caching.

#### Scenario: Full data synchronization

- **GIVEN** user is authenticated with valid session
- **WHEN** `DataSyncService.sync_all()` is called
- **THEN** system SHALL:
  - Fetch attendance page (`FW99001Z.aspx#tabs-1`)
  - Fetch anomaly page (`FW99001Z.aspx#tabs-2`)
  - Fetch personal record page (`FW21003Z.aspx`)
  - Parse all tables using dedicated parsers
  - Merge data into `AttendanceSnapshot`
  - Cache result with timestamp
  - Return complete `AttendanceSnapshot`

#### Scenario: Cache hit within validity period

- **GIVEN** valid cache exists (age < 5 minutes)
- **WHEN** `sync_all(force_refresh=False)` is called
- **THEN** system SHALL return cached `AttendanceSnapshot`
- **AND** SHALL NOT make HTTP requests

#### Scenario: Cache miss or expired

- **GIVEN** no cache exists OR cache age > 5 minutes
- **WHEN** `sync_all(force_refresh=False)` is called
- **THEN** system SHALL fetch fresh data from SSP
- **AND** update cache with new snapshot

#### Scenario: Force refresh bypasses cache

- **GIVEN** valid cache exists
- **WHEN** `sync_all(force_refresh=True)` is called
- **THEN** system SHALL ignore cache
- **AND** fetch fresh data from SSP
- **AND** update cache with new snapshot

### Requirement: Incremental Status Update

The system SHALL support incremental synchronization to update only overtime submission statuses without full data reload.

#### Scenario: Update submission statuses

- **GIVEN** cached `AttendanceSnapshot` exists
- **WHEN** `DataSyncService.sync_overtime_status()` is called
- **THEN** system SHALL:
  - Fetch only personal record page
  - Update `submission_status`, `monthly_total`, `quarterly_total` in cached records
  - Return updated `List[UnifiedOvertimeRecord]`
  - NOT fetch punch or anomaly data

#### Scenario: No cache available

- **GIVEN** no cached snapshot exists
- **WHEN** `sync_overtime_status()` is called
- **THEN** system SHALL fallback to `sync_all()`

### Requirement: Attendance Quota Tracking

The system SHALL track remaining leave quotas (annual leave, compensatory leave) from SSP attendance page.

#### Scenario: Parse quota information

- **GIVEN** attendance page HTML contains quota table (`dvNotes019`)
- **WHEN** parsing attendance page
- **THEN** system SHALL extract:
  - Annual leave remaining (days)
  - Compensatory leave remaining (days)
  - Overtime threshold (minutes until eligible for comp leave)
- **AND** populate `AttendanceQuota` model

### Requirement: Leave Record Tracking

The system SHALL track leave usage by category from SSP attendance page.

#### Scenario: Parse leave records

- **GIVEN** attendance page HTML contains leave table (`gvNotes011`)
- **WHEN** parsing attendance page
- **THEN** system SHALL extract all leave records with:
  - Leave type name (e.g., "114 年公出")
  - Days used
  - Hours used
- **AND** return `List[LeaveRecord]`

### Requirement: Punch Record Tracking

The system SHALL track raw punch (clock-in/clock-out) records from SSP attendance page.

#### Scenario: Parse punch records

- **GIVEN** attendance page HTML contains punch table (`gvNotes005`)
- **WHEN** parsing attendance page
- **THEN** system SHALL extract punch records with:
  - Punch date (YYYY/MM/DD)
  - All punch times for that date
- **AND** return `List[PunchRecord]`

### Requirement: Backward Compatibility Adapters

The system SHALL provide adapter methods to maintain compatibility with existing UI components expecting legacy data models.

#### Scenario: Adapt to AttendanceRecord format

- **GIVEN** UI expects `List[AttendanceRecord]`
- **WHEN** `DataSyncService.get_attendance_records()` is called
- **THEN** system SHALL transform `UnifiedOvertimeRecord` to `AttendanceRecord` format
- **AND** return compatible list

#### Scenario: Adapt to OvertimeSubmissionRecord format

- **GIVEN** UI expects `List[OvertimeSubmissionRecord]`
- **WHEN** `DataSyncService.get_submission_records()` is called
- **THEN** system SHALL transform `UnifiedOvertimeRecord` to `OvertimeSubmissionRecord` format
- **AND** return compatible list

#### Scenario: Adapt to PersonalRecord format

- **GIVEN** UI expects `(List[PersonalRecord], PersonalRecordSummary)`
- **WHEN** `DataSyncService.get_personal_records()` is called
- **THEN** system SHALL:
  - Filter submitted records
  - Transform to `PersonalRecord` format
  - Calculate `PersonalRecordSummary`
  - Return tuple `(records, summary)`

### Requirement: Configurable Cache Duration

The system SHALL allow cache duration to be configured via `Settings.CACHE_DURATION_SECONDS`.

#### Scenario: Use default cache duration

- **GIVEN** `CACHE_DURATION_SECONDS` not configured
- **WHEN** checking cache validity
- **THEN** system SHALL use default 300 seconds (5 minutes)

#### Scenario: Use custom cache duration

- **GIVEN** `CACHE_DURATION_SECONDS = 600`
- **WHEN** checking cache validity
- **THEN** system SHALL use 600 seconds (10 minutes)

### Requirement: Statistics Calculation

The system SHALL automatically calculate overtime statistics from unified records.

#### Scenario: Calculate statistics

- **GIVEN** list of `UnifiedOvertimeRecord`
- **WHEN** creating `AttendanceSnapshot`
- **THEN** system SHALL calculate `OvertimeStatistics` with:
  - Total records count
  - Total overtime hours (sum of all calculated overtime)
  - Average overtime hours (mean)
  - Maximum overtime hours (max)
  - Submitted records count
  - Pending records count (not submitted)
