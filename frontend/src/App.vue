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
      <aside class="bg-base-200 min-h-full w-64 p-4 border-r border-base-300">
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
            <router-link to="/networks" class="flex items-center gap-3">
              <Wifi :size="20" :stroke-width="2" />
              Réseaux
            </router-link>
          </li>
          <li>
            <router-link to="/locations" class="flex items-center gap-3">
              <MapPin :size="20" :stroke-width="2" />
              Emplacements
            </router-link>
          </li>
          <li>
            <router-link to="/device-types" class="flex items-center gap-3">
              <Palette :size="20" :stroke-width="2" />
              Types
            </router-link>
          </li>
        </ul>
      </aside>
    </div>
  </div>
</template>

<script setup>
import { Menu, Monitor, Network, Wifi, MapPin, Palette } from '@lucide/vue'
</script>