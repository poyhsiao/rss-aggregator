<script setup lang="ts">
import { Braces, Check, Code, Copy, Database, Download, Eye, FileCode, FileText, X } from "lucide-vue-next";
import { computed, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import type { FeedParams, FeedItem } from "@/api/feed";
import { getFeed, getFormattedFeed } from "@/api/feed";
import Button from "@/components/ui/Button.vue";
import Dialog from "@/components/ui/Dialog.vue";

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

type Format = "rss" | "json" | "markdown";

const selectedFormat = ref<Format>("rss");
const markdownViewMode = ref<'source' | 'preview'>('preview');
const rssContent = ref("");
const jsonContent = ref<FeedItem[] | null>(null);
const markdownContent = ref("");
const loading = ref(false);
const error = ref("");
const copied = ref(false);

// Cache for fetched data
const cache = ref({
	rss: "",
	json: null as FeedItem[] | null,
	markdown: "",
});

// JSON formatter with syntax highlighting
function formatJson(data: FeedItem[]): string {
	return JSON.stringify(data, null, 2);
}

// Syntax highlighter for JSON
function highlightJson(json: string): string {
	// Escape HTML entities first
	json = json
		.replace(/&/g, "&amp;")
		.replace(/</g, "&lt;")
		.replace(/>/g, "&gt;");

	// Process character by character to properly identify keys vs values
	let result = '';
	let i = 0;
	
	while (i < json.length) {
		// Check for string
		if (json[i] === '"') {
			let stringStart = i;
			i++; // skip opening quote
			while (i < json.length) {
				if (json[i] === '\\' && i + 1 < json.length) {
					i += 2; // skip escaped character
				} else if (json[i] === '"') {
					i++; // include closing quote
					break;
				} else {
					i++;
				}
			}
			const stringContent = json.substring(stringStart, i);
			
			// Check if this is a key (followed by colon)
			let j = i;
			while (j < json.length && /\s/.test(json[j])) j++;
			const isKey = json[j] === ':';
			
			if (isKey) {
				result += `<span class="json-key">${stringContent}</span>`;
			} else {
				result += `<span class="json-string">${stringContent}</span>`;
			}
		}
		// Check for number (including negative)
		else if (/-?\d/.test(json[i]) && (json[i] !== '-' || (i + 1 < json.length && /\d/.test(json[i + 1])))) {
			let numStart = i;
			if (json[i] === '-') i++;
			while (i < json.length && /[\d.eE+-]/.test(json[i])) i++;
			result += `<span class="json-number">${json.substring(numStart, i)}</span>`;
		}
		// Check for true/false
		else if (json.substring(i, i + 4) === 'true') {
			result += '<span class="json-boolean">true</span>';
			i += 4;
		}
		else if (json.substring(i, i + 5) === 'false') {
			result += '<span class="json-boolean">false</span>';
			i += 5;
		}
		// Check for null
		else if (json.substring(i, i + 4) === 'null') {
			result += '<span class="json-null">null</span>';
			i += 4;
		}
		// Regular character
		else {
			result += json[i];
			i++;
		}
	}
	
	return result;
}

// Add line numbers for JSON
function addLineNumbersJson(json: string): string {
	const lines = json.split("\n");
	const maxLineNum = lines.length;
	const lineNumWidth = maxLineNum.toString().length;

	return lines
		.map((line, index) => {
			const lineNum = (index + 1).toString().padStart(lineNumWidth, " ");
			return `<div class="json-line"><span class="json-line-number">${lineNum}</span><span class="json-line-content">${line || " "}</span></div>`;
		})
		.join("");
}

// Render Markdown to HTML for preview
function renderMarkdown(markdown: string): string {
	// Convert Markdown to HTML
	let html = markdown;

	// Headers
	html = html.replace(/^### (.+)$/gm, '<h3 class="text-lg font-semibold text-slate-100 mt-4 mb-2">$1</h3>');
	html = html.replace(/^## (.+)$/gm, '<h2 class="text-xl font-bold text-slate-100 mt-6 mb-3">$1</h2>');
	html = html.replace(/^# (.+)$/gm, '<h1 class="text-2xl font-bold text-slate-100 mt-6 mb-4">$1</h1>');

	// Bold
	html = html.replace(/\*\*([^*]+)\*\*/g, '<strong class="font-semibold">$1</strong>');

	// Links
	html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener" class="text-sky-400 hover:text-sky-300 underline">$1</a>');

	// List items
	html = html.replace(/^- (.+)$/gm, '<li class="ml-4 text-slate-300">$1</li>');

	// Horizontal rules
	html = html.replace(/^---$/gm, '<hr class="border-slate-700 my-4" />');

	// Paragraphs (wrap lines that don't start with HTML tags)
	html = html.split('\n').map(line => {
		if (line.trim() && !line.match(/^<(h[1-6]|li|hr|ul|ol)/)) {
			return `<p class="text-slate-300 my-2">${line}</p>`;
		}
		return line;
	}).join('\n');

	return html;
}

// Syntax highlighter for Markdown
function highlightMarkdown(markdown: string): string {
	// Escape HTML entities first
	markdown = markdown
		.replace(/&/g, "&amp;")
		.replace(/</g, "&lt;")
		.replace(/>/g, "&gt;");

	// Highlight headers (# ## ###)
	markdown = markdown.replace(/^(#{1,3})\s(.+)$/gm, (_match, hashes, text) => {
		return `<span class="md-header">${hashes}</span> <span class="md-header-text">${text}</span>`;
	});

	// Highlight bold text (**text**)
	markdown = markdown.replace(/\*\*([^*]+)\*\*/g, (_match, text) => {
		return `<span class="md-bold">**${text}**</span>`;
	});

	// Highlight links [text](url)
	markdown = markdown.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_match, text, url) => {
		return `[<span class="md-link-text">${text}</span>](<span class="md-link-url">${url}</span>)`;
	});

	// Highlight list items (-)
	markdown = markdown.replace(/^(\s*)-\s(.+)$/gm, (_match, indent, text) => {
		return `${indent}<span class="md-list">-</span> ${text}`;
	});

	// Highlight horizontal rules
	markdown = markdown.replace(/^---$/gm, '<span class="md-hr">---</span>');

	return markdown;
}

// Add line numbers for Markdown
function addLineNumbersMarkdown(markdown: string): string {
	const lines = markdown.split("\n");
	const maxLineNum = lines.length;
	const lineNumWidth = maxLineNum.toString().length;

	return lines
		.map((line, index) => {
			const lineNum = (index + 1).toString().padStart(lineNumWidth, " ");
			return `<div class="md-line"><span class="md-line-number">${lineNum}</span><span class="md-line-content">${line || " "}</span></div>`;
		})
		.join("");
}

// XML formatter with syntax highlighting
function formatXml(xml: string): string {
	let formatted = "";
	let indent = 0;
	const indentSize = 2;

	// Remove extra whitespace between tags
	xml = xml.replace(/>\s+</g, "><").trim();

	// Split by tags
	const tokens = xml.split(/(<[^>]+>)/g).filter((t) => t.trim());

	for (const token of tokens) {
		if (token.startsWith("</")) {
			// Closing tag
			indent = Math.max(0, indent - 1);
			formatted += " ".repeat(indent * indentSize) + token + "\n";
		} else if (token.startsWith("<")) {
			// Opening tag or self-closing tag
			formatted += " ".repeat(indent * indentSize) + token + "\n";
			if (!token.startsWith("<?") && !token.startsWith("<!") && !token.endsWith("/>")) {
				indent++;
			}
		} else if (token.trim()) {
			// Text content
			formatted += " ".repeat(indent * indentSize) + token + "\n";
		}
	}

	return formatted.trim();
}

// Syntax highlighter for XML
function highlightXml(xml: string): string {
	// Escape HTML entities first
	xml = xml
		.replace(/&/g, "&amp;")
		.replace(/</g, "&lt;")
		.replace(/>/g, "&gt;");

	// Highlight tags
	xml = xml.replace(/(&lt;\/?)([\w:.-]+)(&gt;)/g, (_match, open, tag, close) => {
		return `<span class="xml-tag-bracket">${open}</span><span class="xml-tag-name">${tag}</span><span class="xml-tag-bracket">${close}</span>`;
	});

	// Highlight attributes and values
	xml = xml.replace(/(\s)([\w:.-]+)(=)(&quot;[^&]*&quot;)/g, (_match, space, attr, eq, value) => {
		return `${space}<span class="xml-attr-name">${attr}</span>${eq}<span class="xml-attr-value">${value}</span>`;
	});

	// Highlight CDATA sections
	xml = xml.replace(/(&lt;\!\[CDATA\[)([\s\S]*?)(\]\]&gt;)/g, (_match, open, content, close) => {
		return `<span class="xml-cdata">${open}${content}${close}</span>`;
	});

	// Highlight comments
	xml = xml.replace(/(&lt;!--)([\s\S]*?)(--&gt;)/g, (_match, open, content, close) => {
		return `<span class="xml-comment">${open}${content}${close}</span>`;
	});

	// Highlight processing instructions
	xml = xml.replace(/(&lt;\?)([\w:.-]+)(.*?)(\?&gt;)/g, (_match, open, target, content, close) => {
		return `<span class="xml-pi">${open}${target}${content}${close}</span>`;
	});

	return xml;
}

// Add line numbers
function addLineNumbers(xml: string): string {
	const lines = xml.split("\n");
	const maxLineNum = lines.length;
	const lineNumWidth = maxLineNum.toString().length;

	return lines
		.map((line, index) => {
			const lineNum = (index + 1).toString().padStart(lineNumWidth, " ");
			return `<div class="xml-line"><span class="xml-line-number">${lineNum}</span><span class="xml-line-content">${line || " "}</span></div>`;
		})
		.join("");
}

// Computed property for formatted and highlighted content based on selected format
const formattedContent = computed(() => {
	if (selectedFormat.value === "rss") {
		if (!rssContent.value) return "";
		const formatted = formatXml(rssContent.value);
		const highlighted = highlightXml(formatted);
		return addLineNumbers(highlighted);
	} else if (selectedFormat.value === "json") {
		if (!jsonContent.value) return "";
		const formatted = formatJson(jsonContent.value);
		const highlighted = highlightJson(formatted);
		return addLineNumbersJson(highlighted);
	} else if (selectedFormat.value === "markdown") {
		if (!markdownContent.value) return "";
		const highlighted = highlightMarkdown(markdownContent.value);
		return addLineNumbersMarkdown(highlighted);
	}
	return "";
});

// Computed property for rendered Markdown HTML
const markdownHtml = computed(() => {
	if (!markdownContent.value) return "";
	return renderMarkdown(markdownContent.value);
});

// Computed properties for header information
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
	// Find source name from the first item if available
	if (jsonContent.value && jsonContent.value.length > 0) {
		return jsonContent.value[0].source;
	}
	return null;
});

async function fetchRssContent(): Promise<void> {
	loading.value = true;
	error.value = "";
	try {
		const response = await getFormattedFeed('rss', props.params);
		rssContent.value = response.content;
		cache.value.rss = rssContent.value;
	} catch (err) {
		error.value = t("common.error");
		console.error("Failed to fetch RSS:", err);
	} finally {
		loading.value = false;
	}
}

async function fetchJsonContent(): Promise<void> {
	loading.value = true;
	error.value = "";
	try {
		jsonContent.value = await getFeed(props.params);
		cache.value.json = jsonContent.value;
	} catch (err) {
		error.value = t("common.error");
		console.error("Failed to fetch JSON:", err);
	} finally {
		loading.value = false;
	}
}

async function fetchMarkdownContent(): Promise<void> {
	loading.value = true;
	error.value = "";
	try {
		const response = await getFormattedFeed('markdown', props.params);
		markdownContent.value = response.content;
		cache.value.markdown = markdownContent.value;
		// Also fetch JSON for item count display
		if (!cache.value.json) {
			cache.value.json = await getFeed(props.params);
		}
		jsonContent.value = cache.value.json;
	} catch (err) {
		error.value = t("common.error");
		console.error("Failed to fetch Markdown:", err);
	} finally {
		loading.value = false;
	}
}

async function fetchContentForFormat(format: Format): Promise<void> {
	// Use cached data if available
	if (format === "rss" && cache.value.rss) {
		rssContent.value = cache.value.rss;
		return;
	}
	if (format === "json" && cache.value.json) {
		jsonContent.value = cache.value.json;
		return;
	}
	if (format === "markdown" && cache.value.markdown) {
		markdownContent.value = cache.value.markdown;
		return;
	}

	// Fetch data based on format
	if (format === "rss") {
		await fetchRssContent();
	} else if (format === "json") {
		await fetchJsonContent();
	} else if (format === "markdown") {
		await fetchMarkdownContent();
	}
}

function close(): void {
	emit("update:open", false);
}

async function copyToClipboard(): Promise<void> {
	try {
		let content = "";
		if (selectedFormat.value === "rss") {
			content = formatXml(rssContent.value);
		} else if (selectedFormat.value === "json") {
			content = formatJson(jsonContent.value || []);
		} else if (selectedFormat.value === "markdown") {
			content = markdownContent.value;
		}
		await navigator.clipboard.writeText(content);
		copied.value = true;
		setTimeout(() => {
			copied.value = false;
		}, 2000);
	} catch (err) {
		console.error("Failed to copy:", err);
	}
}

function downloadRss(): void {
	let content = "";
	let mimeType = "";
	let filename = "";

	if (selectedFormat.value === "rss") {
		content = formatXml(rssContent.value);
		mimeType = "application/xml";
		filename = "rss-feed.xml";
	} else if (selectedFormat.value === "json") {
		content = formatJson(jsonContent.value || []);
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
			// Reset cache when dialog opens
			cache.value = {
				rss: "",
				json: null,
				markdown: "",
			};
			selectedFormat.value = "rss";
			fetchRssContent();
		}
	},
);

watch(
	selectedFormat,
	async (newFormat) => {
		if (props.open) {
			await fetchContentForFormat(newFormat);
		}
	},
);
</script>

<template>
  <Dialog :open="open" size="2xl" @update:open="close">
    <div class="p-6 overflow-hidden">
      <!-- Header -->
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

      <!-- Loading Skeleton -->
      <div v-if="loading" class="space-y-4">
        <div class="bg-neutral-100 dark:bg-slate-900 rounded-xl overflow-hidden border border-neutral-200 dark:border-slate-800">
          <div class="h-12 bg-neutral-200 dark:bg-slate-800 border-b border-neutral-300 dark:border-slate-700 animate-pulse" />
          <div class="p-4 space-y-2">
            <div v-for="i in 8" :key="i" class="h-4 bg-neutral-200 dark:bg-slate-800 rounded animate-pulse" :style="{ width: `${60 + Math.random() * 40}%` }" />
          </div>
        </div>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="text-center py-12">
        <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-red-100 dark:bg-red-900/30 mb-4">
          <X class="h-8 w-8 text-red-500 dark:text-red-400" />
        </div>
        <p class="text-red-500 dark:text-red-400 font-medium">{{ error }}</p>
      </div>

      <!-- Content -->
      <div v-else class="space-y-4">
        <!-- Format Switcher - Segmented Control Style -->
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

        <!-- Preview Area - Simple Style -->
        <div class="bg-slate-100 dark:bg-slate-950 rounded-lg overflow-hidden border border-slate-200 dark:border-slate-800">
          <!-- Preview Header -->
          <div class="flex items-center justify-between px-4 py-3 bg-slate-200 dark:bg-slate-900 border-b border-slate-300 dark:border-slate-800">
            <span class="text-sm font-medium text-slate-700 dark:text-slate-300">
              {{ t(`feed.format_${selectedFormat}`) }}
            </span>
            <!-- Markdown View Toggle - Right aligned in header -->
            <div v-if="selectedFormat === 'markdown'" class="flex gap-1">
              <button
                @click="markdownViewMode = 'source'"
                :class="[
                  'flex items-center gap-1.5 px-2 py-1 rounded text-xs font-medium transition-colors',
                  markdownViewMode === 'source'
                    ? 'bg-slate-400 dark:bg-slate-700 text-white'
                    : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-white'
                ]"
              >
                <Code class="h-3 w-3" />
                {{ t('feed.view_source') }}
              </button>
              <button
                @click="markdownViewMode = 'preview'"
                :class="[
                  'flex items-center gap-1.5 px-2 py-1 rounded text-xs font-medium transition-colors',
                  markdownViewMode === 'preview'
                    ? 'bg-slate-400 dark:bg-slate-700 text-white'
                    : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-white'
                ]"
              >
                <Eye class="h-3 w-3" />
                {{ t('feed.view_preview') }}
              </button>
            </div>
          </div>

          <!-- Code Content for RSS/JSON -->
          <div v-if="selectedFormat !== 'markdown'" class="p-4 max-h-[40vh] overflow-auto bg-white dark:bg-slate-950">
            <div
              class="text-xs font-mono whitespace-pre code-content"
              v-html="formattedContent"
            ></div>
          </div>

          <!-- Source view for Markdown -->
          <div v-else-if="selectedFormat === 'markdown' && markdownViewMode === 'source'" class="p-4 max-h-[40vh] overflow-auto bg-white dark:bg-slate-950">
            <div
              class="text-xs font-mono whitespace-pre code-content"
              v-html="formattedContent"
            ></div>
          </div>

          <!-- Preview view for Markdown -->
          <div v-else class="p-4 max-h-[40vh] overflow-auto prose dark:prose-invert bg-white dark:bg-slate-950">
            <div v-html="markdownHtml" />
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="flex justify-end gap-2">
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
      </div>
    </div>
  </Dialog>
</template>

<style scoped>
/* Base code content styling - Light mode default */
:deep(.code-content) {
	color: #334155;
}

:deep(.code-content .xml-line-number),
:deep(.code-content .json-line-number),
:deep(.code-content .md-line-number) {
	color: #94a3b8;
	user-select: none;
}

:deep(.code-content .xml-line-content),
:deep(.code-content .json-line-content),
:deep(.code-content .md-line-content) {
	color: #1e293b;
}

/* XML Syntax Highlighting Styles - Light Mode */
:deep(.xml-line),
:deep(.json-line),
:deep(.md-line) {
	display: flex;
	line-height: 1.6;
}

:deep(.xml-line-number),
:deep(.json-line-number),
:deep(.md-line-number) {
	flex-shrink: 0;
	width: 3rem;
	text-align: right;
	padding-right: 1rem;
	user-select: none;
}

:deep(.xml-line-content),
:deep(.json-line-content),
:deep(.md-line-content) {
	flex: 1;
	user-select: text;
}

:deep(.xml-tag-bracket) { color: #6366f1; }
:deep(.xml-tag-name) { color: #0369a1; font-weight: 600; }
:deep(.xml-attr-name) { color: #059669; }
:deep(.xml-attr-value) { color: #dc2626; }
:deep(.xml-cdata) { color: #7c3aed; font-style: italic; }
:deep(.xml-comment) { color: #6b7280; font-style: italic; }
:deep(.xml-pi) { color: #d97706; }

:deep(.json-key) { color: #059669; font-weight: 500; }
:deep(.json-string) { color: #dc2626; }
:deep(.json-number) { color: #7c3aed; }
:deep(.json-boolean) { color: #d97706; font-weight: 500; }
:deep(.json-null) { color: #6b7280; font-style: italic; }

:deep(.md-header) { color: #0369a1; font-weight: 600; }
:deep(.md-header-text) { color: #0f172a; font-weight: 600; }
:deep(.md-bold) { font-weight: 700; color: #1e293b; }
:deep(.md-link-text) { color: #0369a1; text-decoration: underline; }
:deep(.md-link-url) { color: #059669; }
:deep(.md-list) { color: #6366f1; }
:deep(.md-hr) { color: #94a3b8; }

/* Rendered Markdown Preview Styles - Light Mode */
:deep(.prose h1) { font-size: 1.5rem; font-weight: 700; color: #0f172a; margin-top: 1.5rem; margin-bottom: 1rem; }
:deep(.prose h2) { font-size: 1.25rem; font-weight: 700; color: #1e293b; margin-top: 1.5rem; margin-bottom: 0.75rem; }
:deep(.prose h3) { font-size: 1.125rem; font-weight: 600; color: #334155; margin-top: 1rem; margin-bottom: 0.5rem; }
:deep(.prose p) { color: #475569; margin-top: 0.5rem; margin-bottom: 0.5rem; line-height: 1.6; }
:deep(.prose a) { color: #0369a1; text-decoration: underline; }
:deep(.prose a:hover) { color: #0284c7; }
:deep(.prose ul) { list-style-type: disc; padding-left: 1.5rem; margin-top: 0.5rem; margin-bottom: 0.5rem; }
:deep(.prose li) { color: #475569; margin-top: 0.25rem; margin-bottom: 0.25rem; }
:deep(.prose hr) { border-color: #e2e8f0; margin-top: 1rem; margin-bottom: 1rem; }
:deep(.prose strong) { font-weight: 600; color: #1e293b; }
</style>

<style>
/* Dark Mode - Use global style to target parent .dark class */
.dark .code-content { color: #e2e8f0; }
.dark .code-content .xml-line-number,
.dark .code-content .json-line-number,
.dark .code-content .md-line-number { color: #64748b; }
.dark .code-content .xml-line-content,
.dark .code-content .json-line-content,
.dark .code-content .md-line-content { color: #e2e8f0; }

.dark .xml-tag-bracket { color: #818cf8; }
.dark .xml-tag-name { color: #38bdf8; }
.dark .xml-attr-name { color: #34d399; }
.dark .xml-attr-value { color: #fb7185; }
.dark .xml-cdata { color: #a78bfa; }
.dark .xml-comment { color: #64748b; }
.dark .xml-pi { color: #fbbf24; }

.dark .json-key { color: #34d399; }
.dark .json-string { color: #fb7185; }
.dark .json-number { color: #a78bfa; }
.dark .json-boolean { color: #fbbf24; }
.dark .json-null { color: #64748b; }

.dark .md-header { color: #38bdf8; }
.dark .md-header-text { color: #f1f5f9; }
.dark .md-bold { color: #f1f5f9; }
.dark .md-link-text { color: #38bdf8; }
.dark .md-link-url { color: #34d399; }
.dark .md-list { color: #94a3b8; }
.dark .md-hr { color: #64748b; }

/* Dark mode prose */
.dark .prose h1 { color: #f1f5f9; }
.dark .prose h2 { color: #f1f5f9; }
.dark .prose h3 { color: #f1f5f9; }
.dark .prose p { color: #cbd5e1; }
.dark .prose a { color: #38bdf8; }
.dark .prose a:hover { color: #7dd3fc; }
.dark .prose li { color: #cbd5e1; }
.dark .prose hr { border-color: #334155; }
.dark .prose strong { color: #f1f5f9; }
</style>
