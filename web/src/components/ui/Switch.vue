<script setup lang="ts">
const props = defineProps<{
  modelValue: boolean
  disabled?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
}>()

function toggle() {
  if (!props.disabled) {
    emit('update:modelValue', !props.modelValue)
  }
}

const trackWidth = 72
const thumbSize = 40
const padding = 5
const thumbOnPos = trackWidth - thumbSize - padding
</script>

<template>
  <button
    type="button"
    role="switch"
    :aria-checked="modelValue"
    :disabled="disabled"
    class="group relative inline-flex h-11 w-[72px] items-center rounded-full transition-all duration-500 ease-out focus:outline-none focus:ring-4 focus:ring-primary-500/30 focus:ring-offset-2"
    :style="{ '--thumb-on-pos': `${thumbOnPos}px` }"
    :class="[
      modelValue
        ? 'bg-gradient-to-b from-primary-500 to-primary-600 shadow-[inset_0_2px_4px_rgba(0,0,0,0.15),0px_4px_16px_rgba(34,197,94,0.35)]'
        : 'bg-gradient-to-b from-neutral-400 to-neutral-500 shadow-[inset_0_2px_4px_rgba(0,0,0,0.15),0px_4px_12px_rgba(0,0,0,0.2)]',
      disabled && 'opacity-40 cursor-not-allowed'
    ]"
    @click="toggle"
  >
    <!-- Track glow effect when ON -->
    <span
      v-if="modelValue"
      class="absolute inset-0 rounded-full bg-primary-400/20 blur-xl transition-opacity duration-500"
    />

    <!-- Thumb - iOS style: 40px diameter, sits inside track with 5px padding -->
    <span
      class="relative h-10 w-10 rounded-full bg-gradient-to-b from-white to-neutral-100 shadow-[0px_4px_8px_rgba(0,0,0,0.25),0px_2px_4px_rgba(0,0,0,0.15),inset_0px_1px_2px_rgba(255,255,255,1)] transition-all duration-500 ease-out"
      :class="modelValue ? '[transform:translateX(var(--thumb-on-pos))]' : 'translate-x-[5px]'"
    >
      <!-- Thumb shine/gloss effect -->
      <span class="absolute inset-x-2 top-1.5 h-3 rounded-full bg-gradient-to-b from-white/60 to-transparent opacity-50" />
    </span>

    <!-- OFF label - hidden when ON -->
    <span
      class="absolute left-3 text-[10px] font-semibold tracking-wide text-white/80 transition-all duration-500 ease-out"
      :class="modelValue ? 'opacity-0 -translate-x-2' : 'opacity-100 translate-x-0'"
    >
      OFF
    </span>

    <!-- ON label - visible only when ON -->
    <span
      class="absolute right-3 text-[10px] font-semibold tracking-wide text-white transition-all duration-500 ease-out"
      :class="modelValue ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-2'"
    >
      ON
    </span>
  </button>
</template>