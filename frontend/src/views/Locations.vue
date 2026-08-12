<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">Emplacements</h1>
      <button class="btn btn-primary" @click="openAdd">
        <Plus :size="18" :stroke-width="2" />
        Ajouter
      </button>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div v-for="loc in locations" :key="loc.id" class="card bg-base-200">
        <div class="card-body">
          <h2 class="card-title">{{ capitalize(loc.name) }}</h2>
          <div class="text-sm opacity-60">Étage : {{ loc.floor_name || '-' }}</div>
          <div class="card-actions justify-end mt-2">
            <button class="btn btn-ghost btn-xs" @click="openEdit(loc)">
              <Pencil :size="16" :stroke-width="2" />
            </button>
            <button class="btn btn-ghost btn-xs" @click="deleteLocation(loc.id)">
              <Trash2 :size="16" :stroke-width="2" />
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
            <select v-model="form.floor_id" class="select select-bordered">
              <option :value="null">— Aucun —</option>
              <option v-for="f in floors" :key="f.id" :value="f.id">{{ f.name }}</option>
            </select>
          </div>
          <div class="modal-action">
            <button type="button" class="btn" onclick="loc_modal.close()">Annuler</button>
            <button type="submit" class="btn btn-primary">Ajouter</button>
          </div>
        </form>
      </div>
    </dialog>

    <dialog id="edit_loc_modal" class="modal">
      <div class="modal-box">
        <h3 class="text-lg font-bold mb-4">Modifier l'emplacement</h3>
        <form @submit.prevent="updateLocation">
          <div class="form-control mb-3">
            <label class="label"><span class="label-text">Nom</span></label>
            <input v-model="editForm.name" class="input input-bordered" required />
          </div>
          <div class="form-control mb-3">
            <label class="label"><span class="label-text">Étage</span></label>
            <select v-model="editForm.floor_id" class="select select-bordered">
              <option :value="null">— Aucun —</option>
              <option v-for="f in floors" :key="f.id" :value="f.id">{{ f.name }}</option>
            </select>
          </div>
          <div class="modal-action">
            <button type="button" class="btn" onclick="edit_loc_modal.close()">Annuler</button>
            <button type="submit" class="btn btn-primary">Enregistrer</button>
          </div>
        </form>
      </div>
    </dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { Plus, Pencil, Trash2 } from '@lucide/vue'

const locations = ref([])
const floors = ref([])
const form = ref({ name: '', floor_id: null })
const editForm = ref({ name: '', floor_id: null })

function capitalize(s) {
  return s ? s.charAt(0).toUpperCase() + s.slice(1) : ''
}

async function fetchLocations() {
  const { data } = await axios.get('/api/locations')
  locations.value = data
}

async function fetchFloors() {
  const { data } = await axios.get('/api/floors')
  floors.value = data
}

function openAdd() {
  form.value = { name: '', floor_id: null }
  document.getElementById('loc_modal').showModal()
}

async function addLocation() {
  await axios.post('/api/locations', form.value)
  form.value = { name: '', floor_id: null }
  document.getElementById('loc_modal').close()
  fetchLocations()
}

function openEdit(loc) {
  editForm.value = { id: loc.id, name: loc.name, floor_id: loc.floor_id }
  document.getElementById('edit_loc_modal').showModal()
}

async function updateLocation() {
  await axios.put(`/api/locations/${editForm.value.id}`, {
    name: editForm.value.name,
    floor_id: editForm.value.floor_id,
  })
  document.getElementById('edit_loc_modal').close()
  fetchLocations()
}

async function deleteLocation(id) {
  if (!confirm('Supprimer cet emplacement ? Les périphériques associés perdront leur emplacement.')) return
  await axios.delete(`/api/locations/${id}`)
  fetchLocations()
}

onMounted(() => {
  fetchLocations()
  fetchFloors()
})
</script>
