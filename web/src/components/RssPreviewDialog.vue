<script setup lang="ts">
import { Braces, Check, Copy, Database, Download, FileCode, FileText, X } from "lucide-vue-next";
import { computed, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import type { FeedParams } from "@/api/feed";
import { buildFeedPathUrl } from "@/api/feed";
import Button from "@/components/ui/Button.vue";
import Dialog from "@/components/ui/Dialog.vue";
import JsonPreview from "@/components/JsonPreview.vue";
import MarkdownPreview from "@/components/MarkdownPreview.vue";
import RssXmlPreview from "@/components/RssXmlPreview.vue";
import { useFeedCache, type Format } from "@/composables/useFeedCache";

const props = withDefaults(
	defineProps<{
		open: boolean;
		params?: FeedParams;
		title?: string;
	}>(),
	{
		open: false,
	},
);

const emit = defineEmits<(e: "update:open", value: boolean) => void>();

const { t } = useI18n();

const selectedFormat = ref<Format>("rss");
const copied = ref(false);
const copiedPath = ref<string | null>(null);
const showApiPaths = ref(false);

const feedFormats: Format[] = ["rss", "json", "markdown"];

const apiPaths = computed(() => {
	return feedFormats.map((format) => ({
		format,
		url: buildFeedPathUrl(format, props.params),
	}));
});

async function copyPath(url: string): Promise<void> {
	try {
		await navigator.clipboard.writeText(url);
		copiedPath.value = url;
		setTimeout(() => {
			copiedPath.value = null;
		}, 2000);
	} catch (error) {
		console.error("Failed to copy path:", error);
	}
}

const {
	rssContent,
	jsonContent,
	markdownContent,
	loading,
	error,
	fetchRssContent,
	fetchContentForFormat,
	resetCache,
} = useFeedCache();

const itemCount = computed(() => {
	return jsonContent.value?.length ?? 0;
});

const displayTitle = computed(() => {
	if (props.title) return props.title;
	if (props.params?.source_id) return t('feed.preview_source_title');
	return t(`feed.format_${selectedFormat.value}`) + ' ' + t('feed.preview_title');
});

const sourceName = computed(() => {
	if (!props.params?.source_id) return null;
	if (jsonContent.value && jsonContent.value.length > 0) {
		return jsonContent.value[0].source;
	}
	return null;
});

function close(): void {
	emit("update:open", false);
}

async function copyToClipboard(): Promise<void> {
	try {
		let content = "";
		if (selectedFormat.value === "rss") {
			content = rssContent.value;
		} else if (selectedFormat.value === "json") {
			content = JSON.stringify(jsonContent.value || [], null, 2);
		} else if (selectedFormat.value === "markdown") {
			content = markdownContent.value;
		}
		await navigator.clipboard.writeText(content);
		copied.value = true;
		setTimeout(() => {
			copied.value = false;
		}, 2000);
	} catch (error) {
		console.error('Failed to copy to clipboard:', error)
	}
}

function downloadRss(): void {
	let content = "";
	let mimeType = "";
	let filename = "";

	if (selectedFormat.value === "rss") {
		content = rssContent.value;
		mimeType = "application/xml";
		filename = "rss-feed.xml";
	} else if (selectedFormat.value === "json") {
		content = JSON.stringify(jsonContent.value || [], null, 2);
		mimeType = "application/json";
		filename = "rss-feed.json";
	} else if (selectedFormat.value === "markdown") {
		content = markdownContent.value;
		mimeType = "text/markdown";
		filename = "rss-feed.md";
	}

	const blob = new Blob([content], { type: mimeType });
	const url = URL.createObjectURL(blob);
	const a = document.createElement("a");
	a.href = url;
	a.download = filename;
	document.body.appendChild(a);
	a.click();
	document.body.removeChild(a);
	URL.revokeObjectURL(url);
}

watch(
	() => props.open,
	(isOpen) => {
		if (isOpen) {
			resetCache();
			selectedFormat.value = "rss";
			fetchRssContent(props.params);
		}
	},
);

watch(
	selectedFormat,
	async (newFormat) => {
		if (props.open) {
			await fetchContentForFormat(newFormat, props.params);
		}
	},
);
</script>

<template>
  <Dialog :open="open" size="2xl" @update:open="close">
    <div class="p-6 overflow-hidden">
      <div class="flex items-start justify-between mb-6">
        <div class="flex-1 min-w-0">
          <h2 class="text-xl font-semibold text-neutral-900 dark:text-neutral-100 mb-1">
            {{ displayTitle }}
          </h2>
          <div class="flex items-center gap-3 text-sm text-neutral-500 dark:text-neutral-400">
            <span v-if="sourceName" class="flex items-center gap-1">
              <Database class="h-3.5 w-3.5" />
              {{ sourceName }}
            </span>
            <span v-if="itemCount > 0" class="flex items-center gap-1">
              <FileText class="h-3.5 w-3.5" />
              {{ itemCount }} {{ itemCount === 1 ? t('feed.item') : t('feed.items') }}
            </span>
          </div>
        </div>
        <button
          @click="close"
          class="p-2 rounded-lg hover:bg-neutral-100 dark:hover:bg-neutral-700 transition-colors"
        >
          <X class="h-5 w-5 text-neutral-500 dark:text-neutral-400" />
        </button>
      </div>

      <div v-if="loading" class="space-y-4">
        <div class="bg-neutral-100 dark:bg-slate-900 rounded-xl overflow-hidden border border-neutral-200 dark:border-slate-800">
          <div class="h-12 bg-neutral-200 dark:bg-slate-800 border-b border-neutral-300 dark:border-slate-700 animate-pulse" />
          <div class="p-4 space-y-2">
            <div v-for="i in 8" :key="i" class="h-4 bg-neutral-200 dark:bg-slate-800 rounded animate-pulse" :style="{ width: `${60 + Math.random() * 40}%` }" />
          </div>
        </div>
      </div>

      <div v-else-if="error" class="text-center py-12">
        <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-red-100 dark:bg-red-900/30 mb-4">
          <X class="h-8 w-8 text-red-500 dark:text-red-400" />
        </div>
        <p class="text-red-500 dark:text-red-400 font-medium">{{ error }}</p>
      </div>

        <div v-else class="space-y-4">
        <div class="bg-neutral-100 dark:bg-slate-800 p-1 rounded-xl inline-flex">
          <button
            @click="selectedFormat = 'rss'"
            :class="[
              'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all',
              selectedFormat === 'rss'
                ? 'bg-white dark:bg-slate-700 text-neutral-900 dark:text-neutral-100 shadow-sm'
                : 'text-neutral-500 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-100'
            ]"
          >
            <FileText class="h-4 w-4" />
            {{ t('feed.format_rss') }}
          </button>
          <button
            @click="selectedFormat = 'json'"
            :class="[
              'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all',
              selectedFormat === 'json'
                ? 'bg-white dark:bg-slate-700 text-neutral-900 dark:text-neutral-100 shadow-sm'
                : 'text-neutral-500 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-100'
            ]"
          >
            <Braces class="h-4 w-4" />
            {{ t('feed.format_json') }}
          </button>
          <button
            @click="selectedFormat = 'markdown'"
            :class="[
              'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all',
              selectedFormat === 'markdown'
                ? 'bg-white dark:bg-slate-700 text-neutral-900 dark:text-neutral-100 shadow-sm'
                : 'text-neutral-500 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-100'
            ]"
          >
            <FileCode class="h-4 w-4" />
            {{ t('feed.format_markdown') }}
          </button>
        </div>

        <div class="bg-slate-100 dark:bg-slate-950 rounded-lg overflow-hidden border border-slate-200 dark:border-slate-800">
          <div v-if="selectedFormat !== 'markdown'" class="flex items-center justify-between px-4 py-3 bg-slate-200 dark:bg-slate-900 border-b border-slate-300 dark:border-slate-800">
            <span class="text-sm font-medium text-slate-700 dark:text-slate-300">
              {{ t(`feed.format_${selectedFormat}`) }}
            </span>
          </div>

          <div v-if="selectedFormat === 'rss'" class="p-4 max-h-[40vh] overflow-auto bg-white dark:bg-slate-950">
            <RssXmlPreview :content="rssContent" />
          </div>

          <div v-else-if="selectedFormat === 'json'" class="p-4 max-h-[40vh] overflow-auto bg-white dark:bg-slate-950">
            <JsonPreview :content="jsonContent" />
          </div>

          <div v-else-if="selectedFormat === 'markdown'" class="bg-white dark:bg-slate-950">
            <MarkdownPreview :content="markdownContent" />
          </div>
        </div>

        <div class="flex justify-end gap-2">
          <Button
            variant="outline"
            size="sm"
            @click="showApiPaths = !showApiPaths"
            class="gap-2"
          >
            <svg 
              class="h-4 w-4 transition-transform" 
              :class="{ 'rotate-90': showApiPaths }"
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
            </svg>
            {{ t('feed.share_links') }}
          </Button>
          <Button
            variant="outline"
            size="sm"
            @click="copyToClipboard"
            class="gap-2"
          >
            <Check v-if="copied" class="h-4 w-4 text-green-500" />
            <Copy v-else class="h-4 w-4" />
            {{ copied ? t('keys.copied') : t('keys.copy') }}
          </Button>
          <Button
            variant="outline"
            size="sm"
            @click="downloadRss"
            class="gap-2"
          >
            <Download class="h-4 w-4" />
            {{ t('feed.download', { format: t(`feed.format_${selectedFormat}`) }) }}
          </Button>
        </div>

        <!-- Share Links Expanded Section -->
        <Transition
          enter-active-class="transition-all duration-200 ease-out"
          enter-from-class="opacity-0 max-h-0"
          enter-to-class="opacity-100 max-h-40"
          leave-active-class="transition-all duration-200 ease-in"
          leave-from-class="opacity-100 max-h-40"
          leave-to-class="opacity-0 max-h-0"
        >
          <div v-show="showApiPaths" class="bg-slate-100 dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 p-3 overflow-hidden">
            <div class="space-y-1">
              <div
                v-for="{ format, url } in apiPaths"
                :key="format"
                class="flex items-center justify-between text-sm"
              >
                <span class="text-slate-600 dark:text-slate-400 w-16">
                  {{ t(`feed.format_${format}`) }}
                </span>
                <code class="flex-1 text-xs bg-white dark:bg-slate-800 px-2 py-1 rounded text-slate-700 dark:text-slate-300 truncate ml-2">
                  {{ url }}
                </code>
                <button
                  @click="copyPath(url)"
                  class="ml-2 p-1.5 rounded hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
                  :title="t('feed.copy_path')"
                >
                  <Check v-if="copiedPath === url" class="h-4 w-4 text-green-500" />
                  <Copy v-else class="h-4 w-4 text-slate-500 dark:text-slate-400" />
                </button>
              </div>
            </div>
          </div>
        </Transition>
      </div>
    </div>
  </Dialog>
</template>