<script setup lang="ts">
import { Bug, Check, Copy, Database, FolderOpen, RefreshCw, Terminal, X } from "lucide-vue-next";
import { ref, watch } from "vue";
import Button from "@/components/ui/Button.vue";
import Dialog from "@/components/ui/Dialog.vue";
import { isTauri } from "@/utils/environment";
import { getSources } from "@/api/sources";
import { getLogs } from "@/api/logs";
import { getStats } from "@/api/stats";
import { openDataFolder } from "@/utils/tauri-bridge";
import { useToast } from "@/composables/useToast";

const props = defineProps<{
  open: boolean;
}>();

const emit = defineEmits<{
  (e: "update:open", value: boolean): void;
}>();

const loading = ref(false);
const copied = ref(false);
const devtoolsOpen = ref(false);
const toast = useToast();
const debugInfo = ref<{
  environment: string;
  version: string;
  dataPath: string;
  sourcesCount: number;
  activeSources: number;
  logsCount: number;
  statsTotal: number;
  lastFetch: string | null;
}>({
  environment: "",
  version: "",
  dataPath: "",
  sourcesCount: 0,
  activeSources: 0,
  logsCount: 0,
  statsTotal: 0,
  lastFetch: null,
});

async function fetchDebugInfo(): Promise<void> {
  loading.value = true;
  try {
    const [sources, logs, stats] = await Promise.all([
      getSources(),
      getLogs({ limit: 100 }),
      getStats(7),
    ]);

    const totalRequests = stats.reduce((sum, s) => sum + s.total_requests, 0);
    const activeSources = sources.filter(s => s.is_active).length;

    debugInfo.value = {
      environment: isTauri() ? "Tauri (Desktop)" : "Web (Browser)",
      version: __APP_VERSION__ || "0.5.1",
      dataPath: isTauri() ? "Library/Application Support/RSS Aggregator" : "N/A",
      sourcesCount: sources.length,
      activeSources: activeSources,
      logsCount: logs.length,
      statsTotal: totalRequests,
      lastFetch: logs.length > 0 ? logs[0].created_at : null,
    };
  } catch (error) {
    console.error("Failed to fetch debug info:", error);
  } finally {
    loading.value = false;
  }
}

async function copyToClipboard(): Promise<void> {
  try {
    const text = JSON.stringify(debugInfo.value, null, 2);
    await navigator.clipboard.writeText(text);
    copied.value = true;
    setTimeout(() => {
      copied.value = false;
    }, 2000);
  } catch (error) {
    console.error("Failed to copy:", error);
  }
}

function close(): void {
  emit("update:open", false);
}

async function toggleDevtools(): Promise<void> {
  if (!isTauri()) return;
  
  try {
    const { invoke } = await import("@tauri-apps/api/core");
    const isOpen = await invoke<boolean>("toggle_devtools");
    devtoolsOpen.value = isOpen;
  } catch (error) {
    console.error("Failed to toggle devtools:", error);
  }
}

async function handleOpenDataFolder(): Promise<void> {
  if (!isTauri()) return;
  
  try {
    await openDataFolder();
  } catch (error) {
    console.error("Failed to open data folder:", error);
    toast.error(String(error));
  }
}

watch(() => props.open, (isOpen) => {
  if (isOpen) {
    fetchDebugInfo();
  }
});
</script>

<template>
  <Dialog :open="open" size="lg" @update:open="emit('update:open', $event)">
    <div class="p-6">
      <div class="flex items-center justify-between mb-4">
        <div class="flex items-center gap-2">
          <Bug class="h-5 w-5 text-primary-600" />
          <h2 class="text-lg font-semibold">Debug Info</h2>
        </div>
        <Button variant="ghost" size="icon" @click="close">
          <X class="h-4 w-4" />
        </Button>
      </div>

      <div class="space-y-2 mb-4">
        <!-- First row: General actions -->
        <div class="flex gap-2">
          <Button variant="outline" size="sm" @click="fetchDebugInfo" :disabled="loading">
            <RefreshCw :class="{ 'animate-spin': loading }" class="h-4 w-4 mr-1.5" />
            Refresh
          </Button>
          <Button variant="outline" size="sm" @click="copyToClipboard">
            <Check v-if="copied" class="h-4 w-4 mr-1.5 text-green-500" />
            <Copy v-else class="h-4 w-4 mr-1.5" />
            {{ copied ? "Copied!" : "Copy JSON" }}
          </Button>
        </div>
        
        <!-- Second row: Desktop-specific actions -->
        <div v-if="debugInfo.environment === 'Tauri (Desktop)'" class="flex gap-2">
          <Button variant="outline" size="sm" @click="toggleDevtools">
            <Terminal class="h-4 w-4 mr-1.5" />
            {{ devtoolsOpen ? "Close DevTools" : "Open DevTools" }}
          </Button>
          <Button variant="outline" size="sm" @click="handleOpenDataFolder">
            <FolderOpen class="h-4 w-4 mr-1.5" />
            Open Data Folder
          </Button>
        </div>
      </div>

      <div class="space-y-3 text-sm">
        <div class="grid grid-cols-2 gap-4 p-3 bg-neutral-100 dark:bg-neutral-700 rounded-lg">
          <div>
            <span class="text-neutral-500">Environment</span>
            <p class="font-medium">{{ debugInfo.environment }}</p>
          </div>
          <div>
            <span class="text-neutral-500">Version</span>
            <p class="font-medium">{{ debugInfo.version }}</p>
          </div>
        </div>

        <div class="p-3 bg-neutral-100 dark:bg-neutral-700 rounded-lg">
          <div class="flex items-center gap-2 mb-1">
            <FolderOpen class="h-4 w-4 text-neutral-500" />
            <span class="text-neutral-500">Data Path</span>
          </div>
          <p class="font-mono text-xs break-all">{{ debugInfo.dataPath }}</p>
        </div>

        <div class="grid grid-cols-3 gap-3">
          <div class="p-3 bg-neutral-100 dark:bg-neutral-700 rounded-lg text-center">
            <Database class="h-4 w-4 mx-auto mb-1 text-neutral-500" />
            <p class="text-2xl font-bold">{{ debugInfo.sourcesCount }}</p>
            <span class="text-xs text-neutral-500">Sources</span>
          </div>
          <div class="p-3 bg-neutral-100 dark:bg-neutral-700 rounded-lg text-center">
            <Database class="h-4 w-4 mx-auto mb-1 text-green-500" />
            <p class="text-2xl font-bold">{{ debugInfo.activeSources }}</p>
            <span class="text-xs text-neutral-500">Active</span>
          </div>
          <div class="p-3 bg-neutral-100 dark:bg-neutral-700 rounded-lg text-center">
            <Bug class="h-4 w-4 mx-auto mb-1 text-neutral-500" />
            <p class="text-2xl font-bold">{{ debugInfo.logsCount }}</p>
            <span class="text-xs text-neutral-500">Logs</span>
          </div>
        </div>

        <div class="p-3 bg-neutral-100 dark:bg-neutral-700 rounded-lg">
          <span class="text-neutral-500">Total Requests (7 days)</span>
          <p class="font-medium">{{ debugInfo.statsTotal }}</p>
        </div>

        <div class="p-3 bg-neutral-100 dark:bg-neutral-700 rounded-lg">
          <span class="text-neutral-500">Last Activity</span>
          <p class="font-medium">{{ debugInfo.lastFetch || "N/A" }}</p>
        </div>
      </div>
    </div>
  </Dialog>
</template>