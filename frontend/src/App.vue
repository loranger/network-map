<template>
  <div class="drawer lg:drawer-open">
    <input id="drawer-toggle" type="checkbox" class="drawer-toggle" />
    <div class="drawer-content flex flex-col">
      <div class="navbar bg-base-200 border-b border-base-300 lg:hidden">
        <div class="flex-none">
          <label for="drawer-toggle" class="btn btn-square btn-ghost">
            <Menu :size="24" :stroke-width="2" />
          </label>
        </div>
        <div class="flex-1">
          <a class="text-xl font-semibold">Network Map</a>
        </div>
      </div>
      <main class="p-4">
        <router-view />
      </main>
    </div>
    <div class="drawer-side z-40">
      <label for="drawer-toggle" class="drawer-overlay"></label>
      <aside class="bg-base-200 min-h-full w-64 p-4 border-r border-base-300 flex flex-col">
        <div class="hidden lg:block text-2xl font-bold mb-8 mt-2">Network Map</div>
        <ul class="menu menu-md gap-1">
          <li>
            <router-link to="/devices" class="flex items-center gap-3">
              <Monitor :size="20" :stroke-width="2" />
              Périphériques
            </router-link>
          </li>
          <li>
            <router-link to="/graph" class="flex items-center gap-3">
              <Network :size="20" :stroke-width="2" />
              Cartographie
            </router-link>
          </li>
          <li>
            <details>
              <summary class="flex items-center gap-3">
                <Settings :size="20" :stroke-width="2" />
                Réglages
              </summary>
              <ul class="ml-6">
                <li>
                  <router-link to="/device-types" class="flex items-center gap-3">
                    <Shapes :size="18" :stroke-width="2" />
                    Types
                  </router-link>
                </li>
                <li>
                  <router-link to="/networks" class="flex items-center gap-3">
                    <Wifi :size="18" :stroke-width="2" />
                    Réseaux
                  </router-link>
                </li>
                <li>
                  <router-link to="/floors" class="flex items-center gap-3">
                    <Layers :size="18" :stroke-width="2" />
                    Étages
                  </router-link>
                </li>
                <li>
                  <router-link to="/locations" class="flex items-center gap-3">
                    <MapPin :size="18" :stroke-width="2" />
                    Emplacements
                  </router-link>
                </li>
                <li>
                  <router-link to="/access" class="flex items-center gap-3">
                    <ShieldKeyhole :size="18" :stroke-width="2" />
                    Accès
                  </router-link>
                </li>
              </ul>
            </details>
          </li>
        </ul>
        <div class="mt-auto border-t border-base-300 pt-3">
          <button class="btn btn-ghost btn-sm w-full justify-start gap-3" @click="toggleTheme">
            <component :is="themeIcon" :size="18" :stroke-width="2" />
            {{ themeLabel }}
          </button>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { Menu, Monitor, Network, Wifi, MapPin, Shapes, Settings, Layers, Sun, Moon, ShieldKeyhole } from '@lucide/vue'

const theme = ref('system')

function applyTheme(t) {
  const el = document.documentElement
  if (t === 'system') {
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    el.setAttribute('data-theme', prefersDark ? 'dark' : 'light')
  } else {
    el.setAttribute('data-theme', t)
  }
  localStorage.setItem('theme', t)
}

function toggleTheme() {
  const order = ['light', 'dark', 'system']
  const idx = order.indexOf(theme.value)
  theme.value = order[(idx + 1) % order.length]
}

const themeIcon = computed(() => {
  if (theme.value === 'dark') return Moon
  if (theme.value === 'system') {
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    return prefersDark ? Moon : Sun
  }
  return Sun
})

const themeLabel = computed(() => {
  if (theme.value === 'dark') return 'Sombre'
  if (theme.value === 'system') return 'Auto'
  return 'Clair'
})

onMounted(() => {
  theme.value = localStorage.getItem('theme') || 'system'
  applyTheme(theme.value)
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    if (theme.value === 'system') applyTheme('system')
  })
})

watch(theme, applyTheme)
</script>