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