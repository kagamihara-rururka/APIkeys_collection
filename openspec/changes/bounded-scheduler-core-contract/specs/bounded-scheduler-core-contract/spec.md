## ADDED Requirements

### Requirement: Scheduler contract remains Core-only
RRKAL Core SHALL define bounded scheduler planning surfaces without importing downstream renderer, compressor, or prototype repositories.

#### Scenario: Downstream imports remain forbidden
- **WHEN** a scheduler contract module, report, or test is added
- **THEN** it MUST NOT import `RRKAL_displaytools`, `rrkal-visual-compressor`, `vis_2_dis`, Taichi, PyQt, renderer payload readers, `.npz` readers, or compression runtime modules

### Requirement: Scheduler readiness stays conservative
RRKAL Core SHALL report bounded scheduler readiness as incomplete until unified runtime, persistence, cancellation/retry, timeout, status stream, and cross-process write coordination evidence exists.

#### Scenario: Existing Tk hardening is not full readiness
- **WHEN** a readiness or planning report includes Tk background policy registry and process-local SQLite write gate evidence
- **THEN** the report MUST still distinguish those surfaces from a unified scheduler runtime and MUST NOT claim `ready_for_scheduler_runtime_poc=true` unless all required evidence is present

### Requirement: Job contract surfaces are explicit
RRKAL Core SHALL describe scheduler jobs with explicit identity, stage, status, owner, concurrency policy, timeout policy, retry policy, cancellation policy, write policy, review policy, evidence source, and next action.

#### Scenario: Agent-readable job contract
- **WHEN** the scheduler contract is exposed as JSON
- **THEN** the JSON MUST separate existing evidence, missing evidence, blocked surfaces, planned surfaces, safety flags, and next safe actions

### Requirement: Persistence starts as dry-run or owned-test only
RRKAL Core SHALL require dry-run or owned-test persistence evidence before adding durable scheduler queue writes to user databases.

#### Scenario: User database queue writes are blocked
- **WHEN** an implementation slice proposes scheduler queue tables or durable job records
- **THEN** the slice MUST first provide dry-run DDL or owned-test database evidence and MUST NOT write user DB queue records without a later approved migration guard

### Requirement: Lifecycle events remain explicit
RRKAL Core SHALL NOT emit lifecycle events automatically from scheduler job completion unless a later `o_1`-reviewed change explicitly authorizes the event boundary.

#### Scenario: Job completion does not auto-emit lifecycle event
- **WHEN** a scheduler job reaches completed, failed, review-required, or blocked status
- **THEN** Core MUST record scheduler/job evidence only and MUST NOT call visual lifecycle event writers automatically

### Requirement: SQLite write coordination is scoped honestly
RRKAL Core SHALL describe the current SQLite write gate as process-local and per-SQLite-path unless and until cross-process coordination is implemented and tested.

#### Scenario: Process-local gate is reported accurately
- **WHEN** scheduler planning output references SQLite write protection
- **THEN** it MUST label the current gate as process-local and MUST list cross-process coordination as missing evidence

### Requirement: UI consumes scheduler display payloads
Future Tk, Web, or Qt scheduler UI SHALL consume backend display/status payloads rather than deriving business rules from raw scheduler status tokens.

#### Scenario: UI receives next action from Core
- **WHEN** a scheduler status is shown in a UI surface
- **THEN** the UI MUST render the backend-provided label, tone, and next action, and MUST NOT decide retry, import, review, or lifecycle policy locally
