<!-- web/src/components/SourceTags.vue -->
<script setup lang="ts">
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