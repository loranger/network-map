<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">Étages</h1>
      <button class="btn btn-primary" @click="openAdd">
        <Plus :size="18" :stroke-width="2" />
        Ajouter
      </button>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div v-for="floor in floors" :key="floor.id" class="card bg-base-200">
        <div class="card-body">
          <h2 class="card-title">{{ floor.name }}</h2>
          <div class="text-sm opacity-60">
            <span v-if="floor.is_default" class="badge badge-primary badge-sm">Par défaut</span>
            <span v-else class="text-base-content/40">—</span>
          </div>
          <div class="card-actions justify-end mt-2">
            <button class="btn btn-ghost btn-xs" @click="openEdit(floor)">
              <Pencil :size="16" :stroke-width="2" />
            </button>
            <button class="btn btn-ghost btn-xs" @click="deleteFloor(floor.id)">
              <Trash2 :size="16" :stroke-width="2" />
            </button>
          </div>
        </div>
      </div>
      <div v-if="floors.length === 0" class="md:col-span-2 lg:col-span-3">
        <div class="card bg-base-200">
          <div class="card-body text-center text-base-content/50 py-12">
            Aucun étage configuré
          </div>
        </div>
      </div>
    </div>

    <dialog id="floor_modal" class="modal">
      <div class="modal-box">
        <h3 class="text-lg font-bold mb-4">Ajouter un étage</h3>
        <form @submit.prevent="addFloor">
          <div class="form-control mb-3">
            <label class="label"><span class="label-text">Nom</span></label>
            <input v-model="form.name" class="input input-bordered" required placeholder="ex: RDC, R+1..." />
          </div>
          <div class="form-control mb-3">
            <label class="label cursor-pointer justify-start gap-3">
              <input v-model="form.is_default" type="checkbox" class="checkbox checkbox-primary" />
              <span class="label-text">Étage par défaut</span>
            </label>
            <p class="text-xs opacity-50 mt-1">
              Les périphériques sans emplacement seront connectés à l'AP de cet étage
            </p>
          </div>
          <div class="modal-action">
            <button type="button" class="btn" onclick="floor_modal.close()">Annuler</button>
            <button type="submit" class="btn btn-primary">Ajouter</button>
          </div>
        </form>
      </div>
    </dialog>

    <dialog id="edit_floor_modal" class="modal">
      <div class="modal-box">
        <h3 class="text-lg font-bold mb-4">Modifier l'étage</h3>
        <form @submit.prevent="updateFloor">
          <div class="form-control mb-3">
            <label class="label"><span class="label-text">Nom</span></label>
            <input v-model="editForm.name" class="input input-bordered" required />
          </div>
          <div class="form-control mb-3">
            <label class="label cursor-pointer justify-start gap-3">
              <input v-model="editForm.is_default" type="checkbox" class="checkbox checkbox-primary" />
              <span class="label-text">Étage par défaut</span>
            </label>
          </div>
          <div class="modal-action">
            <button type="button" class="btn" onclick="edit_floor_modal.close()">Annuler</button>
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

const floors = ref([])
const form = ref({ name: '', is_default: false })
const editForm = ref({ name: '', is_default: false })

async function fetchFloors() {
  const { data } = await axios.get('/api/floors')
  floors.value = data
}

function openAdd() {
  form.value = { name: '', is_default: false }
  document.getElementById('floor_modal').showModal()
}

async function addFloor() {
  await axios.post('/api/floors', form.value)
  form.value = { name: '', is_default: false }
  document.getElementById('floor_modal').close()
  fetchFloors()
}

function openEdit(floor) {
  editForm.value = { id: floor.id, name: floor.name, is_default: floor.is_default }
  document.getElementById('edit_floor_modal').showModal()
}

async function updateFloor() {
  await axios.put(`/api/floors/${editForm.value.id}`, {
    name: editForm.value.name,
    is_default: editForm.value.is_default,
  })
  document.getElementById('edit_floor_modal').close()
  fetchFloors()
}

async function deleteFloor(id) {
  if (!confirm('Supprimer cet étage ? Les emplacements associés perdront leur étage.')) return
  await axios.delete(`/api/floors/${id}`)
  fetchFloors()
}

onMounted(fetchFloors)
</script>
