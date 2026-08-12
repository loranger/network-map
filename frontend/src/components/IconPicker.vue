<template>
  <div>
    <div class="flex items-center gap-2 mb-2">
      <input v-model="search" type="search" placeholder="Rechercher une icône…" class="input input-bordered input-sm flex-1" />
      <button v-if="modelValue" type="button" class="btn btn-ghost btn-xs" @click="$emit('update:modelValue', null)">
        <X :size="14" :stroke-width="2" />
        Réinitialiser
      </button>
    </div>
    <div class="flex flex-wrap gap-1.5 max-h-40 overflow-y-auto p-2 bg-base-200 rounded-lg">
      <button type="button" v-for="name in filtered" :key="name"
        class="btn btn-ghost btn-sm"
        :class="{ 'btn-primary': modelValue === name }"
        @click="$emit('update:modelValue', name)">
        <img :src="iconDataUrl(name, '#374151')" class="w-5 h-5" :title="name" />
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { X } from '@lucide/vue'
import { ICON_NAMES, iconDataUrl } from '../icons.js'

const props = defineProps({ modelValue: { type: String, default: null } })
defineEmits(['update:modelValue'])

const search = ref('')
const filtered = computed(() => {
  const q = search.value.toLowerCase()
  if (!q) return ICON_NAMES
  return ICON_NAMES.filter(n => n.includes(q))
})
</script>
