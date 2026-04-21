<script setup lang="ts">
import { Settings, X } from "lucide-vue-next";
import Dialog from "@/components/ui/Dialog.vue";
import { useFeatureFlagsStore } from "@/stores/featureFlags";
import { useI18n } from "vue-i18n";

defineProps<{
  open: boolean;
}>();

const emit = defineEmits<{
  (e: "update:open", value: boolean): void;
}>();

const { t } = useI18n();
const store = useFeatureFlagsStore();

function close(): void {
  emit("update:open", false);
}

async function handleToggleGroups(): Promise<void> {
  await store.toggle("feature_groups");
}

async function handleToggleSchedules(): Promise<void> {
  await store.toggle("feature_schedules");
}

async function handleToggleShareLinks(): Promise<void> {
  await store.toggle("feature_share_links");
}
</script>

<template>
  <Dialog :open="open" size="md" @update:open="emit('update:open', $event)">
    <div class="p-6">
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center gap-2">
          <Settings class="h-5 w-5 text-primary-600" />
          <h2 class="text-lg font-semibold">{{ t("featureFlags.title") }}</h2>
        </div>
        <button
          type="button"
          class="close-btn inline-flex items-center justify-center rounded-md p-2 hover:bg-neutral-100 dark:hover:bg-neutral-700 transition-colors"
          @click="close"
          :aria-label="$t('common.close')"
        >
          <X class="h-4 w-4" />
        </button>
      </div>

      <div class="space-y-4">
        <!-- Feature Groups Toggle -->
        <div class="flex items-center justify-between">
          <span class="label-groups text-sm font-medium">{{ t("featureFlags.groups") }}</span>
          <button
            type="button"
            role="switch"
            :aria-checked="store.feature_groups"
            class="toggle-switch toggle-groups relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
            :class="store.feature_groups ? 'bg-primary-600' : 'bg-neutral-200 dark:bg-neutral-600'"
            @click="handleToggleGroups"
          >
            <span
              class="inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform"
              :class="store.feature_groups ? 'translate-x-6' : 'translate-x-1'"
            />
          </button>
        </div>

        <!-- Feature Schedules Toggle -->
        <div class="flex items-center justify-between">
          <span class="label-schedules text-sm font-medium">{{ t("featureFlags.schedules") }}</span>
          <button
            type="button"
            role="switch"
            :aria-checked="store.feature_schedules"
            class="toggle-switch toggle-schedules relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
            :class="store.feature_schedules ? 'bg-primary-600' : 'bg-neutral-200 dark:bg-neutral-600'"
            @click="handleToggleSchedules"
          >
            <span
              class="inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform"
              :class="store.feature_schedules ? 'translate-x-6' : 'translate-x-1'"
            />
          </button>
        </div>

        <!-- Feature Share Links Toggle -->
        <div class="flex items-center justify-between">
          <span class="label-shareLinks text-sm font-medium">{{ t("featureFlags.shareLinks") }}</span>
          <button
            type="button"
            role="switch"
            :aria-checked="store.feature_share_links"
            class="toggle-switch toggle-shareLinks relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
            :class="store.feature_share_links ? 'bg-primary-600' : 'bg-neutral-200 dark:bg-neutral-600'"
            @click="handleToggleShareLinks"
          >
            <span
              class="inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform"
              :class="store.feature_share_links ? 'translate-x-6' : 'translate-x-1'"
            />
          </button>
        </div>
      </div>
    </div>
  </Dialog>
</template>
