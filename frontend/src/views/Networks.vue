<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">Réseaux</h1>
      <button class="btn btn-primary" @click="openAdd">
        <Plus :size="18" :stroke-width="2" />
        Ajouter
      </button>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div v-for="net in networks" :key="net.id" class="card bg-base-200">
        <div class="card-body">
          <h2 class="card-title">
            {{ net.name }}
            <span v-if="net.type === 'mesh'" class="badge badge-accent badge-sm">Mesh</span>
            <span v-else-if="net.type === 'wifi'" class="badge badge-info badge-sm">WiFi</span>
            <span v-else class="badge badge-ghost badge-sm">{{ net.type }}</span>
          </h2>
          <div v-if="net.ssid" class="text-sm">
            <span class="opacity-60">SSID:</span> {{ net.ssid }}
          </div>
          <div v-if="net.subnet" class="text-sm font-mono">
            <span class="opacity-60">Sous-réseau:</span> {{ net.subnet }}
          </div>
          <div v-if="net.gateway" class="text-sm font-mono">
            <span class="opacity-60">Passerelle:</span> {{ net.gateway }}
          </div>
          <div class="card-actions justify-end mt-2">
            <button class="btn btn-ghost btn-xs" @click="openEdit(net)">
              <Pencil :size="16" :stroke-width="2" />
            </button>
            <button class="btn btn-ghost btn-xs" @click="deleteNetwork(net.id)">
              <Trash2 :size="16" :stroke-width="2" />
            </button>
          </div>
        </div>
      </div>
      <div v-if="networks.length === 0" class="md:col-span-2 lg:col-span-3">
        <div class="card bg-base-200">
          <div class="card-body text-center text-base-content/50 py-12">
            Aucun réseau configuré
          </div>
        </div>
      </div>
    </div>

    <dialog id="net_modal" class="modal">
      <div class="modal-box">
        <h3 class="text-lg font-bold mb-4">Ajouter un réseau</h3>
        <form @submit.prevent="addNetwork">
          <div class="form-control mb-3">
            <label class="label"><span class="label-text">Nom</span></label>
            <input v-model="form.name" class="input input-bordered" required />
          </div>
          <div class="form-control mb-3">
            <label class="label"><span class="label-text">Type</span></label>
            <select v-model="form.type" class="select select-bordered" required>
              <option value="wifi">WiFi</option>
              <option value="mesh">Mesh</option>
              <option value="wired">Filaire</option>
            </select>
          </div>
          <div class="form-control mb-3">
            <label class="label"><span class="label-text">SSID</span></label>
            <input v-model="form.ssid" class="input input-bordered" />
          </div>
          <div class="form-control mb-3">
            <label class="label"><span class="label-text">Sous-réseau</span></label>
            <input v-model="form.subnet" class="input input-bordered" placeholder="192.168.1.0/24" />
          </div>
          <div class="form-control mb-3">
            <label class="label"><span class="label-text">Passerelle</span></label>
            <input v-model="form.gateway" class="input input-bordered" />
          </div>
          <div class="modal-action">
            <button type="button" class="btn" onclick="net_modal.close()">Annuler</button>
            <button type="submit" class="btn btn-primary">Ajouter</button>
          </div>
        </form>
      </div>
    </dialog>

    <dialog id="edit_net_modal" class="modal">
      <div class="modal-box">
        <h3 class="text-lg font-bold mb-4">Modifier le réseau</h3>
        <form @submit.prevent="updateNetwork">
          <div class="form-control mb-3">
            <label class="label"><span class="label-text">Nom</span></label>
            <input v-model="editForm.name" class="input input-bordered" required />
          </div>
          <div class="form-control mb-3">
            <label class="label"><span class="label-text">Type</span></label>
            <select v-model="editForm.type" class="select select-bordered" required>
              <option value="wifi">WiFi</option>
              <option value="mesh">Mesh</option>
              <option value="wired">Filaire</option>
            </select>
          </div>
          <div class="form-control mb-3">
            <label class="label"><span class="label-text">SSID</span></label>
            <input v-model="editForm.ssid" class="input input-bordered" />
          </div>
          <div class="form-control mb-3">
            <label class="label"><span class="label-text">Sous-réseau</span></label>
            <input v-model="editForm.subnet" class="input input-bordered" placeholder="192.168.1.0/24" />
          </div>
          <div class="form-control mb-3">
            <label class="label"><span class="label-text">Passerelle</span></label>
            <input v-model="editForm.gateway" class="input input-bordered" />
          </div>
          <div class="modal-action">
            <button type="button" class="btn" onclick="edit_net_modal.close()">Annuler</button>
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

const networks = ref([])
const form = ref({ name: '', type: 'wifi', ssid: '', subnet: '', gateway: '' })
const editForm = ref({ name: '', type: 'wifi', ssid: '', subnet: '', gateway: '' })

async function fetchNetworks() {
  const { data } = await axios.get('/api/networks')
  networks.value = data
}

function openAdd() {
  form.value = { name: '', type: 'wifi', ssid: '', subnet: '', gateway: '' }
  document.getElementById('net_modal').showModal()
}

async function addNetwork() {
  await axios.post('/api/networks', form.value)
  document.getElementById('net_modal').close()
  fetchNetworks()
}

function openEdit(net) {
  editForm.value = { id: net.id, ...net }
  document.getElementById('edit_net_modal').showModal()
}

async function updateNetwork() {
  await axios.put(`/api/networks/${editForm.value.id}`, {
    name: editForm.value.name,
    type: editForm.value.type,
    ssid: editForm.value.ssid,
    subnet: editForm.value.subnet,
    gateway: editForm.value.gateway,
  })
  document.getElementById('edit_net_modal').close()
  fetchNetworks()
}

async function deleteNetwork(id) {
  if (!confirm('Supprimer ce réseau ?')) return
  await axios.delete(`/api/networks/${id}`)
  fetchNetworks()
}

onMounted(fetchNetworks)
</script>