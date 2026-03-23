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