<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">Emplacements</h1>
      <button class="btn btn-primary" onclick="loc_modal.showModal()">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
        Ajouter
      </button>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div v-for="loc in locations" :key="loc.id" class="card bg-base-200">
        <div class="card-body">
          <h2 class="card-title">{{ capitalize(loc.name) }}</h2>
          <div class="text-sm opacity-60">Étage : {{ loc.floor || '-' }}</div>
          <div class="card-actions justify-end mt-2">
            <button class="btn btn-ghost btn-xs" @click="deleteLocation(loc.id)">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
            </button>
          </div>
        </div>
      </div>
      <div v-if="locations.length === 0" class="md:col-span-2 lg:col-span-3">
        <div class="card bg-base-200">
          <div class="card-body text-center text-base-content/50 py-12">
            Aucun emplacement configuré
          </div>
        </div>
      </div>
    </div>

    <dialog id="loc_modal" class="modal">
      <div class="modal-box">
        <h3 class="text-lg font-bold mb-4">Ajouter un emplacement</h3>
        <form @submit.prevent="addLocation">
          <div class="form-control mb-3">
            <label class="label"><span class="label-text">Nom</span></label>
            <input v-model="form.name" class="input input-bordered" required placeholder="ex: garage, bureau..." />
          </div>
          <div class="form-control mb-3">
            <label class="label"><span class="label-text">Étage</span></label>
            <input v-model="form.floor" class="input input-bordered" placeholder="ex: RDC, 1er..." />
          </div>
          <div class="modal-action">
            <button type="button" class="btn" onclick="loc_modal.close()">Annuler</button>
            <button type="submit" class="btn btn-primary">Ajouter</button>
          </div>
        </form>
      </div>
    </dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const locations = ref([])
const form = ref({ name: '', floor: '' })

function capitalize(s) {
  return s ? s.charAt(0).toUpperCase() + s.slice(1) : ''
}

async function fetchLocations() {
  const { data } = await axios.get('/api/locations')
  locations.value = data
}

async function addLocation() {
  await axios.post('/api/locations', form.value)
  form.value = { name: '', floor: '' }
  document.getElementById('loc_modal').close()
  fetchLocations()
}

async function deleteLocation(id) {
  if (!confirm('Supprimer cet emplacement ? Les périphériques associés perdront leur emplacement.')) return
  await axios.delete(`/api/locations/${id}`)
  fetchLocations()
}

onMounted(fetchLocations)
</script>
