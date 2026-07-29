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
            <span v-if="net.color" class="w-3 h-3 rounded-sm" :style="{ backgroundColor: net.color }"></span>
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
          <div v-if="net.ap_device_ids?.length" class="text-sm">
            <span class="opacity-60">APs:</span>
            <span v-for="(aid, i) in net.ap_device_ids" :key="aid">
              {{ i > 0 ? ', ' : '' }}{{ apMap[aid] || '?' }}
            </span>
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

    <dialog ref="netModal" class="modal">
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
          <div class="form-control mb-3">
            <label class="label"><span class="label-text">Couleur</span></label>
            <div class="flex items-center gap-3">
              <input v-model="form.color" type="color" class="w-10 h-10 rounded cursor-pointer border-0 p-0" />
              <span class="text-sm font-mono">{{ form.color }}</span>
            </div>
          </div>
          <div class="modal-action">
            <button type="button" class="btn" @click="closeAdd">Annuler</button>
            <button type="submit" class="btn btn-primary">Ajouter</button>
          </div>
        </form>
      </div>
    </dialog>

    <dialog ref="editNetModal" class="modal">
      <div class="modal-box max-w-xl">
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
          <div v-if="editForm.type === 'wifi' || editForm.type === 'mesh'" class="form-control mb-3">
            <label class="label"><span class="label-text">Points d'accès</span></label>
            <div class="max-h-40 overflow-y-auto border border-base-300 rounded-lg p-2 space-y-1">
              <label v-for="ap in apDevices" :key="ap.id" class="flex items-center gap-2 cursor-pointer text-sm">
                <input type="checkbox" :value="ap.id" v-model="editForm.ap_device_ids" class="checkbox checkbox-xs" />
                <span>{{ ap.name }}</span>
                <span v-if="ap.ips?.[0]?.ipv4" class="text-xs opacity-50 font-mono">{{ ap.ips[0].ipv4 }}</span>
              </label>
              <div v-if="apDevices.length === 0" class="text-sm opacity-50 text-center py-2">Aucun point d'accès trouvé</div>
            </div>
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
          <div class="form-control mb-3">
            <label class="label"><span class="label-text">Couleur</span></label>
            <div class="flex items-center gap-3">
              <input v-model="editForm.color" type="color" class="w-10 h-10 rounded cursor-pointer border-0 p-0" />
              <span class="text-sm font-mono">{{ editForm.color }}</span>
            </div>
          </div>
          <div class="modal-action">
            <button type="button" class="btn" @click="closeEdit">Annuler</button>
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
const apDevices = ref([])
const apMap = ref({})
const netModal = ref(null)
const editNetModal = ref(null)

function randomDarkColor() {
  const h = Math.floor(Math.random() * 360)
  const s = 50 + Math.floor(Math.random() * 30)
  const l = 25 + Math.floor(Math.random() * 25)
  return `hsl(${h}, ${s}%, ${l}%)`
}

const form = ref({ name: '', type: 'wifi', ssid: '', subnet: '', gateway: '', color: '' })
const editForm = ref({ name: '', type: 'wifi', ssid: '', subnet: '', gateway: '', color: '', ap_device_ids: [] })

async function fetchNetworks() {
  const { data } = await axios.get('/api/networks')
  networks.value = data
}

async function fetchApDevices() {
  const { data } = await axios.get('/api/devices', { params: { type: 'ap' } })
  apDevices.value = data
  const map = {}
  for (const d of data) {
    map[d.id] = d.name
  }
  apMap.value = map
}

function openAdd() {
  form.value = { name: '', type: 'wifi', ssid: '', subnet: '', gateway: '', color: randomDarkColor() }
  netModal.value?.showModal()
}

function closeAdd() {
  netModal.value?.close()
}

async function addNetwork() {
  await axios.post('/api/networks', form.value)
  netModal.value?.close()
  fetchNetworks()
}

function openEdit(net) {
  editForm.value = { id: net.id, name: net.name, type: net.type, ssid: net.ssid || '', subnet: net.subnet || '', gateway: net.gateway || '', color: net.color || '', ap_device_ids: net.ap_device_ids ? [...net.ap_device_ids] : [] }
  editNetModal.value?.showModal()
}

function closeEdit() {
  editNetModal.value?.close()
}

async function updateNetwork() {
  const payload = {
    name: editForm.value.name,
    type: editForm.value.type,
    ssid: editForm.value.ssid,
    subnet: editForm.value.subnet,
    gateway: editForm.value.gateway,
    color: editForm.value.color,
  }
  if (editForm.value.type === 'wifi' || editForm.value.type === 'mesh') {
    payload.ap_device_ids = editForm.value.ap_device_ids
  }
  await axios.put(`/api/networks/${editForm.value.id}`, payload)
  editNetModal.value?.close()
  fetchNetworks()
}

async function deleteNetwork(id) {
  if (!confirm('Supprimer ce réseau ?')) return
  await axios.delete(`/api/networks/${id}`)
  fetchNetworks()
}

onMounted(() => {
  fetchNetworks()
  fetchApDevices()
})
</script>