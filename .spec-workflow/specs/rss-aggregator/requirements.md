# Requirements Document

## Introduction

RSS Aggregator provides a unified RSS feed by aggregating multiple RSS/Atom sources. Users can configure sources via environment variables or API, filter content by time and keywords, and receive a standard RSS 2.0 output.

## Alignment with Product Vision

This feature enables the core product purpose: consolidating multiple RSS feeds into a single, filterable output for personal use and API consumption.

## Requirements

### Requirement 1: RSS Feed Aggregation

**User Story:** As a user, I want to receive a single aggregated RSS feed from multiple sources, so that I can consume content from all my subscriptions in one place.

#### Acceptance Criteria

1. WHEN a user requests `/api/v1/feed` THEN the system SHALL return an RSS 2.0 formatted response containing items from all active sources
2. IF no sources are configured THEN the system SHALL return an empty RSS feed with channel metadata
3. WHEN a source is inactive (is_active=false) THEN the system SHALL exclude its items from the aggregated feed

### Requirement 2: Source Management

**User Story:** As a user, I want to manage RSS sources via API, so that I can dynamically add, update, or remove feeds without restarting the service.

#### Acceptance Criteria

1. WHEN a user POSTs to `/api/v1/sources` with valid data THEN the system SHALL create a new source and return 201
2. IF a source URL already exists THEN the system SHALL return 400 with error message
3. WHEN a user DELETEs a source THEN the system SHALL soft-delete the source (set deleted_at)
4. WHEN a user PUTs to `/api/v1/sources/{id}` THEN the system SHALL update the source and return 200

### Requirement 3: Time-Based Filtering

**User Story:** As a user, I want to filter RSS items by time range, so that I can see only recent content.

#### Acceptance Criteria

1. WHEN a user provides `valid_time=24` THEN the system SHALL return only items published within the last 24 hours
2. IF `valid_time` is not provided THEN the system SHALL return all items
3. IF `valid_time` is invalid (non-positive) THEN the system SHALL return 422 validation error

### Requirement 4: Keyword Filtering

**User Story:** As a user, I want to filter RSS items by keywords, so that I can find content matching my interests.

#### Acceptance Criteria

1. WHEN a user provides `keywords=早上;中午` THEN the system SHALL return items whose titles contain "早上" OR "中午"
2. IF no items match the keywords THEN the system SHALL return an empty RSS feed
3. IF keywords are empty string THEN the system SHALL ignore the filter

### Requirement 5: Sorting

**User Story:** As a user, I want to sort RSS items by time or source, so that I can organize content according to my preference.

#### Acceptance Criteria

1. WHEN a user provides `sort_by=published_at&sort_order=desc` THEN the system SHALL return items sorted by publication time (newest first)
2. WHEN a user provides `sort_by=source&sort_order=asc` THEN the system SHALL return items sorted by source name alphabetically
3. IF sort parameters are not provided THEN the system SHALL default to `published_at DESC`

### Requirement 6: Scheduled Fetching

**User Story:** As a system, I want to fetch RSS sources periodically, so that the aggregated feed contains up-to-date content.

#### Acceptance Criteria

1. WHEN the scheduler runs THEN the system SHALL fetch all active sources where `last_fetched_at + fetch_interval <= NOW`
2. IF a fetch fails THEN the system SHALL retry N times before logging the error
3. WHEN a source is fetched successfully THEN the system SHALL update `last_fetched_at` and store feed items

### Requirement 7: Manual Refresh

**User Story:** As a user, I want to manually trigger a refresh of RSS sources, so that I can get the latest content immediately.

#### Acceptance Criteria

1. WHEN a user POSTs to `/api/v1/refresh` THEN the system SHALL trigger a refresh of all active sources
2. WHEN a user POSTs to `/api/v1/sources/{id}/refresh` THEN the system SHALL trigger a refresh of that specific source
3. IF the source does not exist THEN the system SHALL return 404

### Requirement 8: API Authentication

**User Story:** As a system administrator, I want to protect API endpoints with API keys, so that only authorized users can access the service.

#### Acceptance Criteria

1. WHEN a request is made without `X-API-Key` header THEN the system SHALL return 401
2. WHEN a request is made with an invalid API key THEN the system SHALL return 401
3. WHEN a request is made to `/health` THEN the system SHALL not require API key

### Requirement 9: Rate Limiting

**User Story:** As a system administrator, I want to limit API requests per key, so that the service is protected from abuse.

#### Acceptance Criteria

1. WHEN a user exceeds the rate limit THEN the system SHALL return 429 with `Retry-After` header
2. WHEN a user is within the limit THEN the system SHALL include `X-RateLimit-Remaining` header in response
3. IF rate limiting is disabled THEN the system SHALL not check or enforce limits

### Requirement 10: Statistics and Logs

**User Story:** As a system administrator, I want to view usage statistics and error logs, so that I can monitor the service health.

#### Acceptance Criteria

1. WHEN a user GETs `/api/v1/stats` THEN the system SHALL return request counts and fetch statistics
2. WHEN a user GETs `/api/v1/logs` THEN the system SHALL return recent error logs
3. IF a source_id filter is provided THEN the system SHALL return logs for that source only

## Non-Functional Requirements

### Code Architecture and Modularity

- **Single Responsibility Principle**: Each file should have a single, well-defined purpose
- **Modular Design**: Services, models, and routes should be isolated and reusable
- **Dependency Management**: Use dependency injection for services
- **Clear Interfaces**: Define clear contracts between layers

### Performance

- API response time < 500ms for 95% of requests
- Support concurrent feed fetching with configurable limit
- Database queries should use proper indexing

### Security

- API keys should be stored securely (hashed if sensitive)
- Input validation on all endpoints
- Sanitize RSS content before storage
- Use HTTPS for external requests

### Reliability

- Graceful error handling with proper logging
- Retry mechanism for failed fetches
- Soft delete for data recovery
- Health check endpoint for monitoring