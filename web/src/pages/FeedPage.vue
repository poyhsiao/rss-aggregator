<script setup lang="ts">
import { Clock, Database, Eye, FileText, RefreshCw, Rss } from "lucide-vue-next";
import { onMounted, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { getFeed } from "@/api/feed";
import { refreshAllSources } from "@/api/sources";
import RssPreviewDialog from "@/components/RssPreviewDialog.vue";
import ArticlePreviewDialog from "@/components/ArticlePreviewDialog.vue";
import Button from "@/components/ui/Button.vue";
import Input from "@/components/ui/Input.vue";
import type { FeedItem } from "@/types/feed";
import { useToast } from "@/composables/useToast";
import { formatDate } from "@/utils/format";

const { t } = useI18n();
const toast = useToast();

const feedItems = ref<FeedItem[]>([]);
const loading = ref(true);
const refreshing = ref(false);
const sortBy = ref<"published_at" | "source">("published_at");
const keywords = ref("");
const rssDialogOpen = ref(false);
const articlePreviewOpen = ref(false);
const selectedArticle = ref<{ url: string; title: string } | null>(null);

async function fetchFeed(): Promise<void> {
	loading.value = true;
	try {
		feedItems.value = await getFeed({
			sort_by: sortBy.value,
			keywords: keywords.value || undefined,
		});
	} finally {
		loading.value = false;
	}
}

async function handleRefreshAll(): Promise<void> {
	refreshing.value = true;
	try {
		await refreshAllSources();
		await fetchFeed();
		toast.success(t('common.success'));
	} catch {
		toast.error(t('common.error'));
	} finally {
		refreshing.value = false;
	}
}

function openArticlePreview(item: FeedItem): void {
	selectedArticle.value = {
		url: item.link,
		title: item.title,
	};
	articlePreviewOpen.value = true;
}

onMounted(fetchFeed);

watch([sortBy, keywords], () => {
	fetchFeed();
});
</script>

<template>
  <div class="space-y-6">
    <!-- Header Row -->
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-2">
        <Rss class="h-6 w-6" />
        <h1 class="text-2xl font-semibold">{{ t('feed.title') }}</h1>
      </div>
    </div>
    
    <!-- Controls -->
    <div class="flex items-center justify-between gap-2">
      <!-- Left: Sort + Search -->
      <div class="flex items-center gap-2">
        <!-- Sort Buttons -->
        <div class="inline-flex items-center gap-1 bg-neutral-100 dark:bg-neutral-800 p-1 rounded-lg shrink-0">
          <Button
            :variant="sortBy === 'published_at' ? 'default' : 'ghost'"
            size="sm"
            :title="t('feed.sort_time')"
            class="whitespace-nowrap"
            @click="sortBy = 'published_at'"
          >
            <Clock class="h-4 w-4" />
            <span class="hidden sm:inline ml-1.5">{{ t('feed.sort_time') }}</span>
          </Button>
          <Button
            :variant="sortBy === 'source' ? 'default' : 'ghost'"
            size="sm"
            :title="t('feed.sort_source')"
            class="whitespace-nowrap"
            @click="sortBy = 'source'"
          >
            <Database class="h-4 w-4" />
            <span class="hidden sm:inline ml-1.5">{{ t('feed.sort_source') }}</span>
          </Button>
        </div>

        <!-- Search -->
        <Input
          v-model="keywords"
          :placeholder="t('feed.search_placeholder')"
          class="w-28 sm:w-40 shrink min-w-0"
        />
      </div>

      <!-- Right: Action Buttons -->
      <div class="flex items-center gap-2 shrink-0">
        <Button
          variant="outline"
          size="sm"
          :title="t('feed.refresh')"
          :disabled="refreshing"
          class="whitespace-nowrap"
          @click="handleRefreshAll"
        >
          <RefreshCw :class="{ 'animate-spin': refreshing }" class="h-4 w-4" />
          <span class="hidden sm:inline ml-1.5">{{ t('feed.refresh') }}</span>
        </Button>

        <Button
          variant="outline"
          size="sm"
          :title="t('feed.preview_feed')"
          class="whitespace-nowrap"
          @click="rssDialogOpen = true"
        >
          <FileText class="h-4 w-4" />
          <span class="hidden sm:inline ml-1.5">{{ t('feed.preview_feed') }}</span>
        </Button>
      </div>
    </div>
    
    <div v-if="loading" class="text-center py-12 text-neutral-500">
      {{ t('common.loading') }}
    </div>
    
    <div v-else-if="!feedItems.length" class="text-center py-12 text-neutral-500">
      😴 {{ t('feed.empty') }}
    </div>
    
    <div v-else class="grid gap-4">
      <div
        v-for="item in feedItems"
        :key="item.id"
        class="block p-6 bg-white dark:bg-neutral-800 rounded-xl border border-neutral-200 dark:border-neutral-700 hover:shadow-md transition-shadow"
      >
        <div class="flex items-start justify-between gap-3">
          <a
            :href="item.link"
            target="_blank"
            class="flex-1 min-w-0"
          >
            <div class="flex items-center gap-2 text-sm text-neutral-500 mb-2">
              <span class="text-primary-600 dark:text-primary-400">{{ item.source }}</span>
              <span>•</span>
              <span>{{ formatDate(item.published_at) }}</span>
            </div>
            
            <h3 class="text-lg font-medium text-neutral-900 dark:text-neutral-100 mb-2">
              {{ item.title }}
            </h3>
            
            <p class="text-neutral-600 dark:text-neutral-400 line-clamp-2">
              {{ item.description }}
            </p>
          </a>
          
          <button
            type="button"
            class="p-2 rounded-lg hover:bg-neutral-100 dark:hover:bg-neutral-700 text-neutral-500 dark:text-neutral-400 transition-colors shrink-0"
            :title="t('preview.preview_article')"
            @click="openArticlePreview(item)"
          >
            <Eye class="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>

    <RssPreviewDialog
      v-model:open="rssDialogOpen"
      :params="{
        sort_by: sortBy,
        keywords: keywords || undefined,
      }"
    />

    <ArticlePreviewDialog
      v-model:open="articlePreviewOpen"
      :url="selectedArticle?.url || ''"
      :title="selectedArticle?.title"
    />
  </div>
</template>