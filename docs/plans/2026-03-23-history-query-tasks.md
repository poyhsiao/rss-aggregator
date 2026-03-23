# History Query Feature - Implementation Tasks

## Task List

### Phase 1: Backend Implementation

#### 1.1 Create HistoryService
- [ ] Create `src/services/history_service.py`
- [ ] Implement `get_history()` method with date range filtering
- [ ] Implement source ID filtering
- [ ] Implement keyword search (reuse FeedService logic)
- [ ] Implement sorting (fetched_at, published_at)
- [ ] Implement pagination with count
- [ ] Handle soft delete conditions

#### 1.2 Create History API Route
- [ ] Create `src/api/routes/history.py`
- [ ] Define query parameters with validation
- [ ] Create response schema with pagination
- [ ] Wire up HistoryService dependency
- [ ] Add API key requirement

#### 1.3 Register Route
- [ ] Update `src/api/routes/__init__.py` to include history router

#### 1.4 Backend Tests
- [ ] Create `tests/services/test_history_service.py`
- [ ] Test date range filtering
- [ ] Test source filtering
- [ ] Test keyword filtering
- [ ] Test pagination
- [ ] Test edge cases (empty results, invalid params)

### Phase 2: Frontend Components

#### 2.1 Pagination Component
- [ ] Create `web/src/components/Pagination.vue`
- [ ] Props: page, pageSize, totalItems, totalPages
- [ ] Emit: update:page
- [ ] Display: prev/next buttons, page numbers, total count
- [ ] Handle edge cases (single page, first/last page)

#### 2.2 DateRangePicker Component
- [ ] Create `web/src/components/DateRangePicker.vue`
- [ ] Props: startDate, endDate
- [ ] Emit: update:startDate, update:endDate
- [ ] Quick buttons: Last 7 days, Last 30 days, This month, Last month
- [ ] Two date inputs (start, end)
- [ ] Sync quick buttons with date inputs

#### 2.3 SourceTags Component
- [ ] Create `web/src/components/SourceTags.vue`
- [ ] Props: modelValue (number[]), sources (Source[])
- [ ] Emit: update:modelValue
- [ ] Display sources as toggle buttons
- [ ] "Select All" and "Clear" buttons
- [ ] Handle empty sources gracefully

### Phase 3: Frontend Page & API

#### 3.1 API Module
- [ ] Create `web/src/types/history.ts` with TypeScript types
- [ ] Create `web/src/api/history.ts` with `getHistory()` function
- [ ] Define request params interface
- [ ] Define response interface

#### 3.2 HistoryPage
- [ ] Create `web/src/pages/HistoryPage.vue`
- [ ] Integrate DateRangePicker component
- [ ] Integrate SourceTags component (fetch sources on mount)
- [ ] Implement search button and query logic
- [ ] Display results as card list
- [ ] Integrate Pagination component
- [ ] Handle loading and empty states

### Phase 4: Routing & Navigation

#### 4.1 Router
- [ ] Update `web/src/router/index.ts`
- [ ] Add `/history` route pointing to HistoryPage

#### 4.2 Navigation
- [ ] Update `web/src/layouts/MainLayout.vue`
- [ ] Add History link to sidebar (desktop)
- [ ] Add History link to bottom nav (mobile)
- [ ] Use `History` icon from lucide-vue-next

### Phase 5: i18n

#### 5.1 English
- [ ] Update `web/src/locales/en.json`
- [ ] Add `nav.history`
- [ ] Add all `history.*` keys

#### 5.2 Chinese Traditional
- [ ] Update `web/src/locales/zh-TW.json`
- [ ] Add `nav.history`
- [ ] Add all `history.*` keys with Chinese translations

### Phase 6: Integration & Testing

#### 6.1 Manual Testing
- [ ] Test all filter combinations
- [ ] Test pagination navigation
- [ ] Test quick date buttons
- [ ] Test source multi-select
- [ ] Test empty state
- [ ] Test mobile responsiveness
- [ ] Test language switching

#### 6.2 Edge Cases
- [ ] No sources available
- [ ] No results for filters
- [ ] Large result sets (performance)
- [ ] Invalid date inputs

## Dependencies

- No new external dependencies required
- Reuse existing patterns from FeedService and FeedPage

## Estimated Effort

| Phase | Effort |
|-------|--------|
| Phase 1: Backend | 2-3 hours |
| Phase 2: Components | 2-3 hours |
| Phase 3: Page & API | 1-2 hours |
| Phase 4: Routing | 30 min |
| Phase 5: i18n | 30 min |
| Phase 6: Testing | 1 hour |
| **Total** | **7-10 hours** |