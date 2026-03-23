<!-- web/src/pages/HistoryPage.vue -->
<script setup lang="ts">
import { Calendar, Search } from "lucide-vue-next";
import { computed, onMounted, ref } from "vue";
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
            <span v-if="item.published_at || item.fetched_at">{{ formatDate((item.published_at ?? item.fetched_at) as string) }}</span>
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