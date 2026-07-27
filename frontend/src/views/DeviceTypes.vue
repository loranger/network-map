<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">Types de périphériques</h1>
      <button class="btn btn-primary" onclick="dt_modal.showModal()">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
        Ajouter
      </button>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div v-for="dt in types" :key="dt.id" class="card bg-base-200">
        <div class="card-body">
          <div class="flex items-center gap-3">
            <span class="w-5 h-5 rounded" :style="{ backgroundColor: dt.color }"></span>
            <h2 class="card-title">{{ dt.label }}</h2>
          </div>
          <div class="text-sm opacity-60 font-mono">{{ dt.type }}</div>
          <div class="card-actions justify-end mt-2">
            <button class="btn btn-ghost btn-xs" @click="openEdit(dt)">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
            </button>
            <button class="btn btn-ghost btn-xs" @click="deleteType(dt.id)">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
            </button>
          </div>
        </div>
      </div>
      <div v-if="types.length === 0" class="md:col-span-2 lg:col-span-3">
        <div class="card bg-base-200">
          <div class="card-body text-center text-base-content/50 py-12">
            Aucun type configuré
          </div>
        </div>
      </div>
    </div>

    <dialog id="dt_modal" class="modal">
      <div class="modal-box">
        <h3 class="text-lg font-bold mb-4">Ajouter un type</h3>
        <form @submit.prevent="addType">
          <div class="form-control mb-3">
            <label class="label"><span class="label-text">Type (identifiant)</span></label>
            <input v-model="form.type" class="input input-bordered" required placeholder="ex: printer" />
          </div>
          <div class="form-control mb-3">
            <label class="label"><span class="label-text">Libellé</span></label>
            <input v-model="form.label" class="input input-bordered" required placeholder="ex: Imprimante" />
          </div>
          <div class="form-control mb-3">
            <label class="label"><span class="label-text">Couleur</span></label>
            <div class="flex items-center gap-3">
              <input v-model="form.color" type="color" class="w-10 h-10 rounded cursor-pointer border-0 p-0" />
              <span class="text-sm font-mono">{{ form.color }}</span>
            </div>
          </div>
          <div class="modal-action">
            <button type="button" class="btn" onclick="dt_modal.close()">Annuler</button>
            <button type="submit" class="btn btn-primary">Ajouter</button>
          </div>
        </form>
      </div>
    </dialog>

    <dialog id="edit_dt_modal" class="modal">
      <div class="modal-box">
        <h3 class="text-lg font-bold mb-4">Modifier le type</h3>
        <form @submit.prevent="updateType">
          <div class="form-control mb-3">
            <label class="label"><span class="label-text">Libellé</span></label>
            <input v-model="editForm.label" class="input input-bordered" required />
          </div>
          <div class="form-control mb-3">
            <label class="label"><span class="label-text">Couleur</span></label>
            <div class="flex items-center gap-3">
              <input v-model="editForm.color" type="color" class="w-10 h-10 rounded cursor-pointer border-0 p-0" />
              <span class="text-sm font-mono">{{ editForm.color }}</span>
            </div>
          </div>
          <div class="modal-action">
            <button type="button" class="btn" onclick="edit_dt_modal.close()">Annuler</button>
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

const types = ref([])
const form = ref({ type: '', label: '', color: '#6b7280' })
const editForm = ref({ label: '', color: '' })

async function fetchTypes() {
  const { data } = await axios.get('/api/device-types')
  types.value = data
}

async function addType() {
  await axios.post('/api/device-types', form.value)
  form.value = { type: '', label: '', color: '#6b7280' }
  document.getElementById('dt_modal').close()
  fetchTypes()
}

function openEdit(dt) {
  editForm.value = { id: dt.id, label: dt.label, color: dt.color }
  document.getElementById('edit_dt_modal').showModal()
}

async function updateType() {
  await axios.put(`/api/device-types/${editForm.value.id}`, {
    label: editForm.value.label,
    color: editForm.value.color,
  })
  document.getElementById('edit_dt_modal').close()
  fetchTypes()
}

async function deleteType(id) {
  if (!confirm('Supprimer ce type ? Les périphériques de ce type ne seront plus colorés.')) return
  await axios.delete(`/api/device-types/${id}`)
  fetchTypes()
}

onMounted(fetchTypes)
</script>