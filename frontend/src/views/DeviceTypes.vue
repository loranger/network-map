<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">Types de périphériques</h1>
      <button class="btn btn-primary" @click="openAdd">
        <Plus :size="18" :stroke-width="2" />
        Ajouter
      </button>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div v-for="dt in types" :key="dt.id" class="card bg-base-200">
        <div class="card-body">
          <div class="flex items-center gap-3">
            <span class="w-7 h-7 rounded flex items-center justify-center" :style="{ backgroundColor: dt.color }">
              <img :src="iconDataUrl(dt.icon, '#fff')" class="w-4 h-4" />
            </span>
            <h2 class="card-title">{{ dt.label }}</h2>
          </div>
          <div class="text-sm opacity-60 font-mono">{{ dt.type }}</div>
          <div class="card-actions justify-end mt-2">
            <button class="btn btn-ghost btn-xs" @click="openEdit(dt)">
              <Pencil :size="16" :stroke-width="2" />
            </button>
            <button class="btn btn-ghost btn-xs" @click="deleteType(dt.id)">
              <Trash2 :size="16" :stroke-width="2" />
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

    <dialog ref="addModal" class="modal">
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
              <button type="button" class="btn btn-ghost btn-xs" @click="form.color = randomDarkColor()">
                <Shuffle :size="14" :stroke-width="2" />
                Random
              </button>
            </div>
          </div>
          <div class="form-control mb-3">
            <label class="label"><span class="label-text">Icône</span></label>
            <input v-model="iconSearch" type="search" placeholder="Rechercher…" class="input input-bordered input-sm mb-2" />
            <div class="flex flex-wrap gap-1.5 max-h-40 overflow-y-auto p-2 bg-base-200 rounded-lg">
              <button type="button" v-for="name in filteredIconNames" :key="name"
                class="btn btn-ghost btn-sm"
                :class="{ 'btn-primary': form.icon === name }"
                @click="form.icon = name; iconSearch = ''">
                <img :src="iconDataUrl(name, '#374151')" class="w-5 h-5" :title="name" />
              </button>
            </div>
          </div>
          <div class="modal-action">
            <button type="button" class="btn" @click="addModal?.close()">Annuler</button>
            <button type="submit" class="btn btn-primary">Ajouter</button>
          </div>
        </form>
      </div>
      <form method="dialog" class="modal-backdrop"><button></button></form>
    </dialog>

    <dialog ref="editModal" class="modal">
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
              <button type="button" class="btn btn-ghost btn-xs" @click="editForm.color = randomDarkColor()">
                <Shuffle :size="14" :stroke-width="2" />
                Random
              </button>
            </div>
          </div>
          <div class="form-control mb-3">
            <label class="label"><span class="label-text">Icône</span></label>
            <input v-model="iconSearch" type="search" placeholder="Rechercher…" class="input input-bordered input-sm mb-2" />
            <div class="flex flex-wrap gap-1.5 max-h-40 overflow-y-auto p-2 bg-base-200 rounded-lg">
              <button type="button" v-for="name in filteredIconNames" :key="name"
                class="btn btn-ghost btn-sm"
                :class="{ 'btn-primary': editForm.icon === name }"
                @click="editForm.icon = name; iconSearch = ''">
                <img :src="iconDataUrl(name, '#374151')" class="w-5 h-5" :title="name" />
              </button>
            </div>
          </div>
          <div class="modal-action">
            <button type="button" class="btn" @click="editModal?.close()">Annuler</button>
            <button type="submit" class="btn btn-primary">Enregistrer</button>
          </div>
        </form>
      </div>
      <form method="dialog" class="modal-backdrop"><button></button></form>
    </dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { Plus, Pencil, Trash2, Shuffle } from '@lucide/vue'
import { ICON_NAMES, iconDataUrl } from '../icons.js'

const addModal = ref(null)
const editModal = ref(null)
const types = ref([])
const iconSearch = ref('')

const filteredIconNames = computed(() => {
  const q = iconSearch.value.toLowerCase()
  if (!q) return ICON_NAMES
  return ICON_NAMES.filter(n => n.includes(q))
})

function randomDarkColor() {
  const h = Math.floor(Math.random() * 360)
  const s = 50 + Math.floor(Math.random() * 30)
  const l = 25 + Math.floor(Math.random() * 25)
  return `hsl(${h}, ${s}%, ${l}%)`
}

const form = ref({ type: '', label: '', color: '#6b7280', icon: 'box' })
const editForm = ref({ label: '', color: '', icon: 'box' })

function openAdd() {
  form.value = { type: '', label: '', color: randomDarkColor(), icon: 'box' }
  addModal.value?.showModal()
}

async function fetchTypes() {
  const { data } = await axios.get('/api/device-types')
  types.value = data
}

async function addType() {
  await axios.post('/api/device-types', form.value)
  addModal.value?.close()
  fetchTypes()
}

function openEdit(dt) {
  editForm.value = { id: dt.id, label: dt.label, color: dt.color, icon: dt.icon || 'box' }
  editModal.value?.showModal()
}

async function updateType() {
  await axios.put(`/api/device-types/${editForm.value.id}`, {
    label: editForm.value.label,
    color: editForm.value.color,
    icon: editForm.value.icon,
  })
  editModal.value?.close()
  fetchTypes()
}

async function deleteType(id) {
  if (!confirm('Supprimer ce type ? Les périphériques de ce type ne seront plus colorés.')) return
  await axios.delete(`/api/device-types/${id}`)
  fetchTypes()
}

onMounted(fetchTypes)
</script>