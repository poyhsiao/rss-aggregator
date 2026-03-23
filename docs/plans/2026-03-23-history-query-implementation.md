# History Query Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a history query feature that allows users to search previously fetched RSS feed items by date range and source names with pagination.

**Architecture:** Backend adds a new HistoryService and `/api/v1/history` endpoint. Frontend creates a new HistoryPage with DateRangePicker, SourceTags, and Pagination components. Follows existing patterns from FeedService and FeedPage.

**Tech Stack:** Python/FastAPI (backend), Vue 3/TypeScript (frontend), SQLAlchemy, Tailwind CSS

---

## Task 1: Backend - Create HistoryService

**Files:**
- Create: `src/services/history_service.py`
- Test: `tests/services/test_history_service.py`

### Step 1: Write the failing test

```python
# tests/services/test_history_service.py
"""Tests for HistoryService."""

import pytest
from datetime import date

from src.services.history_service import HistoryService


@pytest.fixture
def history_service(db_session):
    """Create HistoryService instance."""
    return HistoryService(db_session)


@pytest.mark.asyncio
async def test_get_history_returns_empty_list_when_no_items(history_service):
    """Test that get_history returns empty list when no items exist."""
    items, pagination = await history_service.get_history()

    assert items == []
    assert pagination["total_items"] == 0
    assert pagination["total_pages"] == 0
```

### Step 2: Run test to verify it fails

Run: `uv run pytest tests/services/test_history_service.py::test_get_history_returns_empty_list_when_no_items -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.services.history_service'"

### Step 3: Create HistoryService with minimal implementation

```python
# src/services/history_service.py
"""Service for querying historical feed items."""

from datetime import date
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.models import FeedItem, Source


class HistoryService:
    """Service for querying historical feed items."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the service with a database session.

        Args:
            session: AsyncSession for database operations.
        """
        self.session = session

    async def get_history(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
        source_ids: list[int] | None = None,
        keywords: str | None = None,
        sort_by: str = "fetched_at",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Get historical feed items with filtering and pagination.

        Args:
            start_date: Filter by start date (inclusive).
            end_date: Filter by end date (inclusive).
            source_ids: Filter by source IDs.
            keywords: Keywords for title filtering (semicolon-separated).
            sort_by: Sort field ('fetched_at' or 'published_at').
            sort_order: Sort direction ('asc' or 'desc').
            page: Page number (1-indexed).
            page_size: Number of items per page.

        Returns:
            Tuple of (items list, pagination info dict).
        """
        return [], {"page": page, "page_size": page_size, "total_items": 0, "total_pages": 0}
```

### Step 4: Run test to verify it passes

Run: `uv run pytest tests/services/test_history_service.py::test_get_history_returns_empty_list_when_no_items -v`
Expected: PASS

### Step 5: Commit

```bash
git add src/services/history_service.py tests/services/test_history_service.py
git commit -m "feat: add HistoryService skeleton"
```

---

## Task 2: Backend - Implement date range filtering

**Files:**
- Modify: `src/services/history_service.py`
- Modify: `tests/services/test_history_service.py`

### Step 1: Write the failing test

```python
# Add to tests/services/test_history_service.py
from datetime import datetime

from src.models import FeedItem, Source
from src.utils.time import now


@pytest.mark.asyncio
async def test_get_history_filters_by_date_range(db_session):
    """Test that get_history filters by date range."""
    # Create test source
    source = Source(name="Test Source", url="https://example.com/feed.xml")
    db_session.add(source)
    await db_session.flush()

    # Create test items with different fetched_at dates
    old_item = FeedItem(
        source_id=source.id,
        title="Old Item",
        link="https://example.com/old",
        fetched_at=datetime(2024, 1, 10, 12, 0, 0),
    )
    new_item = FeedItem(
        source_id=source.id,
        title="New Item",
        link="https://example.com/new",
        fetched_at=datetime(2024, 1, 20, 12, 0, 0),
    )
    db_session.add_all([old_item, new_item])
    await db_session.commit()

    service = HistoryService(db_session)

    # Query for items between Jan 15 and Jan 25
    items, pagination = await service.get_history(
        start_date=date(2024, 1, 15),
        end_date=date(2024, 1, 25),
    )

    assert len(items) == 1
    assert items[0]["title"] == "New Item"
    assert pagination["total_items"] == 1
```

### Step 2: Run test to verify it fails

Run: `uv run pytest tests/services/test_history_service.py::test_get_history_filters_by_date_range -v`
Expected: FAIL (returns 0 items because query not implemented)

### Step 3: Implement date range filtering

```python
# Update src/services/history_service.py get_history method:
from datetime import datetime, time
from sqlalchemy import and_

async def get_history(
    self,
    start_date: date | None = None,
    end_date: date | None = None,
    source_ids: list[int] | None = None,
    keywords: str | None = None,
    sort_by: str = "fetched_at",
    sort_order: str = "desc",
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Get historical feed items with filtering and pagination."""
    # Build base query with soft delete filters
    query = (
        select(FeedItem)
        .options(joinedload(FeedItem.source))
        .where(
            FeedItem.deleted_at.is_(None),
            FeedItem.source.has(Source.is_active == True),  # noqa: E712
            FeedItem.source.has(Source.deleted_at.is_(None)),
        )
    )

    # Apply date range filter
    if start_date is not None:
        start_datetime = datetime.combine(start_date, time.min)
        query = query.where(FeedItem.fetched_at >= start_datetime)

    if end_date is not None:
        end_datetime = datetime.combine(end_date, time.max)
        query = query.where(FeedItem.fetched_at <= end_datetime)

    # Apply source filter
    if source_ids:
        query = query.where(FeedItem.source_id.in_(source_ids))

    # Apply keyword filter
    if keywords:
        keyword_list = [k.strip() for k in keywords.split(";") if k.strip()]
        if keyword_list:
            from sqlalchemy import or_
            conditions = [FeedItem.title.ilike(f"%{kw}%") for kw in keyword_list]
            query = query.where(or_(*conditions))

    # Count total items
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await self.session.execute(count_query)
    total_items = total_result.scalar() or 0

    # Calculate pagination
    total_pages = (total_items + page_size - 1) // page_size if total_items > 0 else 0
    offset = (page - 1) * page_size

    # Apply sorting
    if sort_by == "published_at":
        order_col = FeedItem.published_at
    else:
        order_col = FeedItem.fetched_at

    if sort_order == "desc":
        query = query.order_by(order_col.desc())
    else:
        query = query.order_by(order_col.asc())

    # Apply pagination
    query = query.offset(offset).limit(page_size)

    # Execute query
    result = await self.session.execute(query)
    items = list(result.unique().scalars().all())

    # Format response
    return [
        {
            "id": item.id,
            "source_id": item.source_id,
            "source": item.source.name if item.source else "",
            "title": item.title,
            "link": item.link,
            "description": item.description or "",
            "published_at": item.published_at.isoformat() if item.published_at else None,
            "fetched_at": item.fetched_at.isoformat() if item.fetched_at else None,
        }
        for item in items
    ], {
        "page": page,
        "page_size": page_size,
        "total_items": total_items,
        "total_pages": total_pages,
    }
```

### Step 4: Run test to verify it passes

Run: `uv run pytest tests/services/test_history_service.py::test_get_history_filters_by_date_range -v`
Expected: PASS

### Step 5: Commit

```bash
git add src/services/history_service.py tests/services/test_history_service.py
git commit -m "feat: implement date range filtering in HistoryService"
```

---

## Task 3: Backend - Create History API Route

**Files:**
- Create: `src/api/routes/history.py`
- Create: `src/schemas/history.py`
- Modify: `src/api/routes/__init__.py`

### Step 1: Create response schema

```python
# src/schemas/history.py
"""Pydantic schemas for history API."""

from datetime import datetime
from pydantic import BaseModel, Field


class HistoryItem(BaseModel):
    """Schema for a history feed item."""

    id: int
    source_id: int
    source: str
    title: str
    link: str
    description: str
    published_at: str | None
    fetched_at: str | None


class PaginationInfo(BaseModel):
    """Schema for pagination info."""

    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1, le=100)
    total_items: int = Field(..., ge=0)
    total_pages: int = Field(..., ge=0)


class HistoryResponse(BaseModel):
    """Schema for history API response."""

    items: list[HistoryItem]
    pagination: PaginationInfo
```

### Step 2: Create history route

```python
# src/api/routes/history.py
"""History API routes."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from src.api.deps import get_history_service, require_api_key
from src.schemas.history import HistoryResponse
from src.services.history_service import HistoryService

router = APIRouter(prefix="/history", tags=["history"])


@router.get("", response_model=HistoryResponse)
async def get_history(
    start_date: date | None = Query(
        None,
        description="Start date (ISO 8601 format, e.g., 2024-01-01)",
    ),
    end_date: date | None = Query(
        None,
        description="End date (ISO 8601 format, e.g., 2024-01-31)",
    ),
    source_ids: str | None = Query(
        None,
        description="Source IDs (comma-separated, e.g., 1,2,3)",
    ),
    keywords: str | None = Query(
        None,
        description="Keywords for title filtering (semicolon-separated)",
    ),
    sort_by: str = Query(
        "fetched_at",
        pattern="^(fetched_at|published_at)$",
        description="Sort field",
    ),
    sort_order: str = Query(
        "desc",
        pattern="^(asc|desc)$",
        description="Sort direction",
    ),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    history_service: HistoryService = Depends(get_history_service),
    _: str = Depends(require_api_key),
) -> HistoryResponse:
    """Get historical feed items with filtering and pagination.

    Query params:
    - start_date: Filter by start date (inclusive)
    - end_date: Filter by end date (inclusive)
    - source_ids: Filter by source IDs (comma-separated)
    - keywords: Keywords for title filtering (semicolon-separated)
    - sort_by: Sort field ('fetched_at' or 'published_at')
    - sort_order: Sort direction ('asc' or 'desc')
    - page: Page number (1-indexed)
    - page_size: Number of items per page (max 100)
    """
    # Parse source_ids from comma-separated string
    source_id_list = None
    if source_ids:
        source_id_list = [int(sid.strip()) for sid in source_ids.split(",") if sid.strip()]

    items, pagination = await history_service.get_history(
        start_date=start_date,
        end_date=end_date,
        source_ids=source_id_list,
        keywords=keywords,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )

    return HistoryResponse(items=items, pagination=pagination)
```

### Step 3: Create schemas __init__.py if needed

```python
# src/schemas/__init__.py
"""Schemas package."""

from src.schemas.history import HistoryItem, HistoryResponse, PaginationInfo

__all__ = ["HistoryItem", "HistoryResponse", "PaginationInfo"]
```

### Step 4: Register route in __init__.py

```python
# Update src/api/routes/__init__.py
from fastapi import APIRouter

from src.api.routes import feed, health, history, keys, logs, sources, stats

router = APIRouter()
router.include_router(health.router)
router.include_router(feed.router)
router.include_router(sources.router)
router.include_router(keys.router)
router.include_router(stats.router)
router.include_router(logs.router)
router.include_router(history.router)  # Add this line
```

### Step 5: Add dependency to deps.py

```python
# Add to src/api/deps.py
from src.services.history_service import HistoryService

async def get_history_service(
    session: AsyncSession = Depends(get_session),
) -> HistoryService:
    """Get HistoryService instance."""
    return HistoryService(session)
```

### Step 6: Test the endpoint manually

Run: `uv run uvicorn src.main:app --reload`

Then test: `curl http://localhost:8000/api/v1/history -H "X-API-Key: your-key"`

### Step 7: Commit

```bash
git add src/api/routes/history.py src/api/routes/__init__.py src/schemas/history.py src/schemas/__init__.py src/api/deps.py
git commit -m "feat: add /api/v1/history endpoint"
```

---

## Task 4: Frontend - Create Pagination Component

**Files:**
- Create: `web/src/components/Pagination.vue`

### Step 1: Create Pagination component

```vue
<!-- web/src/components/Pagination.vue -->
<script setup lang="ts">
import { ChevronLeft, ChevronRight } from "lucide-vue-next";
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import Button from "./ui/Button.vue";

const props = defineProps<{
  page: number;
  pageSize: number;
  totalItems: number;
  totalPages: number;
}>();

const emit = defineEmits<{
  (e: "update:page", page: number): void;
}>();

const { t } = useI18n();

const pageNumbers = computed(() => {
  const pages: number[] = [];
  const maxVisible = 5;

  if (props.totalPages <= maxVisible) {
    for (let i = 1; i <= props.totalPages; i++) {
      pages.push(i);
    }
  } else {
    if (props.page <= 3) {
      for (let i = 1; i <= 4; i++) pages.push(i);
      pages.push(-1); // ellipsis
      pages.push(props.totalPages);
    } else if (props.page >= props.totalPages - 2) {
      pages.push(1);
      pages.push(-1);
      for (let i = props.totalPages - 3; i <= props.totalPages; i++) pages.push(i);
    } else {
      pages.push(1);
      pages.push(-1);
      for (let i = props.page - 1; i <= props.page + 1; i++) pages.push(i);
      pages.push(-1);
      pages.push(props.totalPages);
    }
  }

  return pages;
});

function goToPage(p: number) {
  if (p >= 1 && p <= props.totalPages && p !== props.page) {
    emit("update:page", p);
  }
}

function prevPage() {
  if (props.page > 1) {
    emit("update:page", props.page - 1);
  }
}

function nextPage() {
  if (props.page < props.totalPages) {
    emit("update:page", props.page + 1);
  }
}
</script>

<template>
  <div v-if="totalPages > 1" class="flex items-center justify-center gap-2">
    <Button
      variant="outline"
      size="sm"
      :disabled="page <= 1"
      :title="t('pagination.prev')"
      @click="prevPage"
    >
      <ChevronLeft class="h-4 w-4" />
    </Button>

    <template v-for="p in pageNumbers" :key="p">
      <span v-if="p === -1" class="px-2 text-neutral-400">...</span>
      <Button
        v-else
        :variant="p === page ? 'default' : 'outline'"
        size="sm"
        class="min-w-[2rem]"
        @click="goToPage(p)"
      >
        {{ p }}
      </Button>
    </template>

    <Button
      variant="outline"
      size="sm"
      :disabled="page >= totalPages"
      :title="t('pagination.next')"
      @click="nextPage"
    >
      <ChevronRight class="h-4 w-4" />
    </Button>
  </div>
</template>
```

### Step 2: Add i18n keys for pagination

```json
// Add to web/src/locales/en.json
{
  "pagination": {
    "prev": "Previous",
    "next": "Next"
  }
}
```

```json
// Add to web/src/locales/zh-TW.json
{
  "pagination": {
    "prev": "上一頁",
    "next": "下一頁"
  }
}
```

### Step 3: Commit

```bash
git add web/src/components/Pagination.vue web/src/locales/en.json web/src/locales/zh-TW.json
git commit -m "feat: add Pagination component"
```

---

## Task 5: Frontend - Create DateRangePicker Component

**Files:**
- Create: `web/src/components/DateRangePicker.vue`

### Step 1: Create DateRangePicker component

```vue
<!-- web/src/components/DateRangePicker.vue -->
<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import Button from "./ui/Button.vue";
import Input from "./ui/Input.vue";

const props = defineProps<{
  startDate: string;
  endDate: string;
}>();

const emit = defineEmits<{
  (e: "update:startDate", date: string): void;
  (e: "update:endDate", date: string): void;
}>();

const { t } = useI18n();

function setQuickRange(range: string) {
  const today = new Date();
  let start: Date;
  let end: Date;

  switch (range) {
    case "last_7_days":
      end = today;
      start = new Date(today);
      start.setDate(start.getDate() - 6);
      break;
    case "last_30_days":
      end = today;
      start = new Date(today);
      start.setDate(start.getDate() - 29);
      break;
    case "this_month":
      start = new Date(today.getFullYear(), today.getMonth(), 1);
      end = new Date(today.getFullYear(), today.getMonth() + 1, 0);
      break;
    case "last_month":
      start = new Date(today.getFullYear(), today.getMonth() - 1, 1);
      end = new Date(today.getFullYear(), today.getMonth(), 0);
      break;
    default:
      return;
  }

  emit("update:startDate", formatDate(start));
  emit("update:endDate", formatDate(end));
}

function formatDate(date: Date): string {
  return date.toISOString().split("T")[0];
}

const quickButtons = computed(() => [
  { key: "last_7_days", label: t("history.quick.last_7_days") },
  { key: "last_30_days", label: t("history.quick.last_30_days") },
  { key: "this_month", label: t("history.quick.this_month") },
  { key: "last_month", label: t("history.quick.last_month") },
]);
</script>

<template>
  <div class="space-y-3">
    <!-- Quick buttons -->
    <div class="flex flex-wrap gap-2">
      <Button
        v-for="btn in quickButtons"
        :key="btn.key"
        variant="outline"
        size="sm"
        class="whitespace-nowrap"
        @click="setQuickRange(btn.key)"
      >
        {{ btn.label }}
      </Button>
    </div>

    <!-- Date inputs -->
    <div class="flex items-center gap-2">
      <Input
        type="date"
        :model-value="startDate"
        :title="t('history.filter.start_date')"
        class="w-auto"
        @update:model-value="emit('update:startDate', $event)"
      />
      <span class="text-neutral-400">~</span>
      <Input
        type="date"
        :model-value="endDate"
        :title="t('history.filter.end_date')"
        class="w-auto"
        @update:model-value="emit('update:endDate', $event)"
      />
    </div>
  </div>
</template>
```

### Step 2: Commit

```bash
git add web/src/components/DateRangePicker.vue
git commit -m "feat: add DateRangePicker component"
```

---

## Task 6: Frontend - Create SourceTags Component

**Files:**
- Create: `web/src/components/SourceTags.vue`

### Step 1: Create SourceTags component

```vue
<!-- web/src/components/SourceTags.vue -->
<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import Button from "./ui/Button.vue";

interface Source {
  id: number;
  name: string;
}

const props = defineProps<{
  modelValue: number[];
  sources: Source[];
}>();

const emit = defineEmits<{
  (e: "update:modelValue", ids: number[]): void;
}>();

const { t } = useI18n();

const allSelected = computed(() => {
  return props.sources.length > 0 && props.modelValue.length === props.sources.length;
});

const someSelected = computed(() => {
  return props.modelValue.length > 0 && props.modelValue.length < props.sources.length;
});

function isSelected(sourceId: number): boolean {
  return props.modelValue.includes(sourceId);
}

function toggleSource(sourceId: number) {
  if (isSelected(sourceId)) {
    emit("update:modelValue", props.modelValue.filter((id) => id !== sourceId));
  } else {
    emit("update:modelValue", [...props.modelValue, sourceId]);
  }
}

function selectAll() {
  emit("update:modelValue", props.sources.map((s) => s.id));
}

function clear() {
  emit("update:modelValue", []);
}
</script>

<template>
  <div v-if="sources.length === 0" class="text-neutral-500 text-sm">
    {{ t("history.no_sources") }}
  </div>
  <div v-else class="space-y-2">
    <!-- Control buttons -->
    <div class="flex gap-2">
      <Button variant="outline" size="sm" @click="selectAll">
        {{ t("history.filter.select_all") }}
      </Button>
      <Button variant="outline" size="sm" @click="clear">
        {{ t("history.filter.clear") }}
      </Button>
    </div>

    <!-- Source tags -->
    <div class="flex flex-wrap gap-2">
      <button
        v-for="source in sources"
        :key="source.id"
        type="button"
        :class="[
          'px-3 py-1.5 rounded-full text-sm font-medium transition-colors',
          isSelected(source.id)
            ? 'bg-primary-600 text-white dark:bg-primary-500'
            : 'bg-neutral-100 text-neutral-700 hover:bg-neutral-200 dark:bg-neutral-800 dark:text-neutral-300 dark:hover:bg-neutral-700',
        ]"
        @click="toggleSource(source.id)"
      >
        {{ source.name }}
      </button>
    </div>
  </div>
</template>
```

### Step 2: Commit

```bash
git add web/src/components/SourceTags.vue
git commit -m "feat: add SourceTags component"
```

---

## Task 7: Frontend - Create History API Module

**Files:**
- Create: `web/src/types/history.ts`
- Create: `web/src/api/history.ts`

### Step 1: Create TypeScript types

```typescript
// web/src/types/history.ts
export interface HistoryItem {
  id: number;
  source_id: number;
  source: string;
  title: string;
  link: string;
  description: string;
  published_at: string | null;
  fetched_at: string | null;
}

export interface PaginationInfo {
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
}

export interface HistoryResponse {
  items: HistoryItem[];
  pagination: PaginationInfo;
}

export interface HistoryParams {
  start_date?: string;
  end_date?: string;
  source_ids?: string;
  keywords?: string;
  sort_by?: "fetched_at" | "published_at";
  sort_order?: "asc" | "desc";
  page?: number;
  page_size?: number;
}
```

### Step 2: Create API module

```typescript
// web/src/api/history.ts
import api from "./axios";
import type { HistoryParams, HistoryResponse } from "@/types/history";

export async function getHistory(params: HistoryParams): Promise<HistoryResponse> {
  const response = await api.get<HistoryResponse>("/history", { params });
  return response.data;
}
```

### Step 3: Commit

```bash
git add web/src/types/history.ts web/src/api/history.ts
git commit -m "feat: add history API module"
```

---

## Task 8: Frontend - Create HistoryPage

**Files:**
- Create: `web/src/pages/HistoryPage.vue`

### Step 1: Create HistoryPage

```vue
<!-- web/src/pages/HistoryPage.vue -->
<script setup lang="ts">
import { Calendar, Search } from "lucide-vue-next";
import { computed, onMounted, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { getHistory } from "@/api/history";
import { getSources } from "@/api/sources";
import DateRangePicker from "@/components/DateRangePicker.vue";
import Pagination from "@/components/Pagination.vue";
import SourceTags from "@/components/SourceTags.vue";
import Button from "@/components/ui/Button.vue";
import type { HistoryItem, HistoryParams } from "@/types/history";
import type { Source } from "@/types/source";
import { useToast } from "@/composables/useToast";
import { formatDate } from "@/utils/format";

const { t } = useI18n();
const toast = useToast();

// Filter state
const startDate = ref("");
const endDate = ref("");
const selectedSourceIds = ref<number[]>([]);
const keywords = ref("");

// Results state
const items = ref<HistoryItem[]>([]);
const sources = ref<Source[]>([]);
const loading = ref(false);
const currentPage = ref(1);
const totalPages = ref(0);
const totalItems = ref(0);
const pageSize = 20;

// Fetch sources on mount
onMounted(async () => {
  try {
    sources.value = await getSources();
  } catch {
    toast.error(t("common.error"));
  }
});

// Build query params
const queryParams = computed<HistoryParams>(() => {
  const params: HistoryParams = {
    page: currentPage.value,
    page_size: pageSize,
  };

  if (startDate.value) params.start_date = startDate.value;
  if (endDate.value) params.end_date = endDate.value;
  if (selectedSourceIds.value.length > 0) {
    params.source_ids = selectedSourceIds.value.join(",");
  }
  if (keywords.value) params.keywords = keywords.value;

  return params;
});

// Fetch history
async function fetchHistory(): Promise<void> {
  loading.value = true;
  try {
    const response = await getHistory(queryParams.value);
    items.value = response.items;
    totalItems.value = response.pagination.total_items;
    totalPages.value = response.pagination.total_pages;
  } catch {
    toast.error(t("common.error"));
  } finally {
    loading.value = false;
  }
}

// Handle search button click
function handleSearch(): void {
  currentPage.value = 1;
  fetchHistory();
}

// Handle page change
function handlePageChange(page: number): void {
  currentPage.value = page;
  fetchHistory();
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-semibold">📜 {{ t("history.title") }}</h1>
    </div>

    <!-- Filter Section -->
    <div class="bg-white dark:bg-neutral-800 rounded-xl border border-neutral-200 dark:border-neutral-700 p-4 space-y-4">
      <!-- Date Range -->
      <div>
        <label class="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
          <Calendar class="h-4 w-4 inline mr-1" />
          {{ t("history.filter.start_date") }} / {{ t("history.filter.end_date") }}
        </label>
        <DateRangePicker
          v-model:start-date="startDate"
          v-model:end-date="endDate"
        />
      </div>

      <!-- Source Tags -->
      <div>
        <label class="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
          {{ t("history.filter.source") }}
        </label>
        <SourceTags
          v-model="selectedSourceIds"
          :sources="sources"
        />
      </div>

      <!-- Keywords -->
      <div>
        <label class="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
          {{ t("feed.search_placeholder") }}
        </label>
        <div class="flex gap-2">
          <input
            v-model="keywords"
            type="text"
            :placeholder="t('feed.search_placeholder')"
            class="flex-1 px-3 py-2 rounded-lg border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 text-neutral-900 dark:text-neutral-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
          <Button @click="handleSearch">
            <Search class="h-4 w-4" />
            <span class="ml-1.5">{{ t("history.filter.search") }}</span>
          </Button>
        </div>
      </div>
    </div>

    <!-- Results Section -->
    <div v-if="loading" class="text-center py-12 text-neutral-500">
      {{ t("common.loading") }}
    </div>

    <div v-else-if="items.length === 0" class="text-center py-12 text-neutral-500">
      😴 {{ t("history.empty") }}
    </div>

    <template v-else>
      <!-- Total count -->
      <div class="text-sm text-neutral-500">
        {{ t("history.result.total", { count: totalItems }) }}
      </div>

      <!-- Items list -->
      <div class="grid gap-4">
        <a
          v-for="item in items"
          :key="item.id"
          :href="item.link"
          target="_blank"
          class="block p-6 bg-white dark:bg-neutral-800 rounded-xl border border-neutral-200 dark:border-neutral-700 hover:shadow-md transition-shadow"
        >
          <div class="flex items-center gap-2 text-sm text-neutral-500 mb-2">
            <span class="text-primary-600 dark:text-primary-400">{{ item.source }}</span>
            <span>•</span>
            <span>{{ formatDate(item.published_at || item.fetched_at) }}</span>
          </div>

          <h3 class="text-lg font-medium text-neutral-900 dark:text-neutral-100 mb-2">
            {{ item.title }}
          </h3>

          <p class="text-neutral-600 dark:text-neutral-400 line-clamp-2">
            {{ item.description }}
          </p>
        </a>
      </div>

      <!-- Pagination -->
      <Pagination
        :page="currentPage"
        :page-size="pageSize"
        :total-items="totalItems"
        :total-pages="totalPages"
        @update:page="handlePageChange"
      />
    </template>
  </div>
</template>
```

### Step 2: Commit

```bash
git add web/src/pages/HistoryPage.vue
git commit -m "feat: add HistoryPage"
```

---

## Task 9: Frontend - Add Routing

**Files:**
- Modify: `web/src/router/index.ts`

### Step 1: Add history route

```typescript
// Add to web/src/router/index.ts routes array
{
  path: "/history",
  name: "history",
  component: () => import("@/pages/HistoryPage.vue"),
  meta: { requiresAuth: true },
},
```

### Step 2: Commit

```bash
git add web/src/router/index.ts
git commit -m "feat: add /history route"
```

---

## Task 10: Frontend - Add Navigation

**Files:**
- Modify: `web/src/layouts/MainLayout.vue`

### Step 1: Add history nav link

Find the navigation section and add:

```vue
<!-- Add to sidebar nav items -->
<RouterLink
  to="/history"
  class="flex items-center gap-3 px-3 py-2 rounded-lg text-neutral-600 hover:bg-neutral-100 dark:text-neutral-400 dark:hover:bg-neutral-800 transition-colors"
  active-class="bg-primary-50 text-primary-600 dark:bg-primary-900/20 dark:text-primary-400"
>
  <History class="h-5 w-5" />
  <span>{{ t('nav.history') }}</span>
</RouterLink>
```

### Step 2: Import History icon

```typescript
import { History, ... } from "lucide-vue-next";
```

### Step 3: Commit

```bash
git add web/src/layouts/MainLayout.vue
git commit -m "feat: add history navigation link"
```

---

## Task 11: Frontend - Add i18n Keys

**Files:**
- Modify: `web/src/locales/en.json`
- Modify: `web/src/locales/zh-TW.json`

### Step 1: Add English keys

```json
// Add to web/src/locales/en.json
{
  "nav": {
    "history": "History"
  },
  "history": {
    "title": "History",
    "filter": {
      "start_date": "Start Date",
      "end_date": "End Date",
      "source": "Source",
      "select_all": "Select All",
      "clear": "Clear",
      "search": "Search"
    },
    "quick": {
      "last_7_days": "Last 7 Days",
      "last_30_days": "Last 30 Days",
      "this_month": "This Month",
      "last_month": "Last Month"
    },
    "result": {
      "total": "Total {count} items"
    },
    "empty": "No results found",
    "no_sources": "No sources available"
  },
  "pagination": {
    "prev": "Previous",
    "next": "Next"
  }
}
```

### Step 2: Add Chinese Traditional keys

```json
// Add to web/src/locales/zh-TW.json
{
  "nav": {
    "history": "歷史查詢"
  },
  "history": {
    "title": "歷史查詢",
    "filter": {
      "start_date": "開始日期",
      "end_date": "結束日期",
      "source": "來源",
      "select_all": "全選",
      "clear": "清除",
      "search": "查詢"
    },
    "quick": {
      "last_7_days": "最近 7 天",
      "last_30_days": "最近 30 天",
      "this_month": "本月",
      "last_month": "上月"
    },
    "result": {
      "total": "共 {count} 筆"
    },
    "empty": "沒有找到結果",
    "no_sources": "沒有可用的來源"
  },
  "pagination": {
    "prev": "上一頁",
    "next": "下一頁"
  }
}
```

### Step 3: Commit

```bash
git add web/src/locales/en.json web/src/locales/zh-TW.json
git commit -m "feat: add history i18n keys"
```

---

## Task 12: Final Verification

### Step 1: Run backend tests

```bash
uv run pytest tests/ -v
```

### Step 2: Build frontend

```bash
cd web && pnpm build
```

### Step 3: Manual test

1. Start backend: `uv run uvicorn src.main:app --reload`
2. Start frontend: `cd web && pnpm dev`
3. Navigate to `/history`
4. Test all filter combinations
5. Test pagination
6. Test language switching

### Step 4: Final commit

```bash
git add -A
git commit -m "feat: complete history query feature"
```

---

## Execution Options

**Plan complete and saved to `docs/plans/2026-03-23-history-query-implementation.md`.**

**Two execution options:**

1. **Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

2. **Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**