<script setup>
import { ref } from 'vue'

defineProps({
  src: String,
})

const hasError = ref(false)
</script>

<template>
  <div
    class="@container aspect-square rounded-full overflow-hidden shrink-0 flex items-center justify-center bg-slate-200"
  >
    <img
      v-if="src && !hasError"
      :src="src"
      @error="hasError = true"
      class="size-full object-cover"
    />
    <i v-else class="pi pi-user text-slate-700 text-[50cqw]!"></i>
  </div>
</template>
