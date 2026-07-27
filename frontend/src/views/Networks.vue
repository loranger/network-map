<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">Réseaux</h1>
      <button class="btn btn-primary" onclick="net_modal.showModal()">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
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
            <button class="btn btn-ghost btn-xs" @click="deleteNetwork(net.id)">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
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
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const networks = ref([])
const form = ref({ name: '', type: 'wifi', ssid: '', subnet: '', gateway: '' })

async function fetchNetworks() {
  const { data } = await axios.get('/api/networks')
  networks.value = data
}

async function addNetwork() {
  await axios.post('/api/networks', form.value)
  form.value = { name: '', type: 'wifi', ssid: '', subnet: '', gateway: '' }
  document.getElementById('net_modal').close()
  fetchNetworks()
}

async function deleteNetwork(id) {
  if (!confirm('Supprimer ce réseau ?')) return
  await axios.delete(`/api/networks/${id}`)
  fetchNetworks()
}

onMounted(fetchNetworks)
</script>
