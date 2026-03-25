<template>
  <span class="status-badge" :data-tone="tone">{{ label }}</span>
</template>

<script setup lang="ts">
import { computed } from "vue";

import { statusLabel } from "../lib/format";

const props = defineProps<{ status: string }>();

const label = computed(() => statusLabel(props.status));
const tone = computed(() => {
  if (props.status === "succeeded") return "success";
  if (props.status === "failed") return "danger";
  if (props.status === "review_required") return "warning";
  return "neutral";
});
</script>
