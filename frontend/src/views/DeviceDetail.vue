<template>
  <div v-if="device">
    <div class="flex items-center gap-3 mb-6">
      <router-link to="/devices" class="btn btn-ghost btn-circle">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/></svg>
      </router-link>
      <h1 class="text-2xl font-bold">{{ capitalize(device.name) }}</h1>
      <span class="badge badge-lg" :class="badgeClass(device.device_type)">{{ capitalize(device.device_type) }}</span>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div class="lg:col-span-2">
        <div class="card bg-base-200">
          <div class="card-body">
            <h2 class="card-title">Informations</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="text-sm opacity-60">Fabricant</label>
                <p>{{ device.manufacturer || '-' }}</p>
              </div>
              <div>
                <label class="text-sm opacity-60">Hostname</label>
                <p class="font-mono">{{ device.hostname || '-' }}</p>
              </div>
              <div>
                <label class="text-sm opacity-60">Modèle</label>
                <p>{{ device.model || '-' }}</p>
              </div>
              <div>
                <label class="text-sm opacity-60">Adresse MAC</label>
                <p class="font-mono">{{ device.mac || '-' }}</p>
              </div>
              <div>
                <label class="text-sm opacity-60">Adresse IPv4</label>
                <p class="font-mono">{{ device.ipv4 || '-' }}</p>
              </div>
              <div>
                <label class="text-sm opacity-60">Type IP</label>
                <p>
                  <span v-if="device.ip_type === 'static'" class="badge badge-outline badge-sm">Static</span>
                  <span v-else-if="device.ip_type === 'dhcp'" class="badge badge-outline badge-sm">DHCP</span>
                  <span v-else class="opacity-60">-</span>
                </p>
              </div>
              <div>
                <label class="text-sm opacity-60">Adresse IPv6</label>
                <p class="font-mono">{{ device.ipv6 || '-' }}</p>
              </div>
              <div>
                <label class="text-sm opacity-60">Emplacement</label>
                <p>{{ capitalize(device.location_name) || '-' }}</p>
              </div>
              <div>
                <label class="text-sm opacity-60">Étage</label>
                <p>{{ capitalize(device.location_floor) || '-' }}</p>
              </div>
              <div>
                <label class="text-sm opacity-60">Découvert automatiquement</label>
                <p>{{ device.discovered ? 'Oui' : 'Non' }}</p>
              </div>
            </div>
            <div v-if="device.notes" class="mt-4">
              <label class="text-sm opacity-60">Notes</label>
              <p class="whitespace-pre-wrap">{{ device.notes }}</p>
            </div>
          </div>
        </div>

        <div v-if="device.device_type === 'switch'" class="card bg-base-200 mt-6">
          <div class="card-body">
            <div class="flex items-center justify-between">
              <h2 class="card-title">Ports</h2>
              <button class="btn btn-primary btn-sm" onclick="port_modal.showModal()">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                Ajouter un port
              </button>
            </div>
            <div class="overflow-x-auto mt-2">
              <table class="table table-sm">
                <thead>
                  <tr><th>Port</th><th>Connecté à</th><th>VLAN</th><th>PoE</th><th></th></tr>
                </thead>
                <tbody>
                  <tr v-for="port in sortedPorts" :key="port.id">
                    <td class="font-mono">{{ port.name }}</td>
                    <td>
                      <span v-if="port.connected_device_name" class="link link-hover" @click="navigateTo(port.connected_device_id)">{{ capitalize(port.connected_device_name) }}</span>
                      <span v-else class="opacity-40">-</span>
                    </td>
                    <td>{{ port.vlan || '-' }}</td>
                    <td>{{ port.poe ? 'Oui' : 'Non' }}</td>
                    <td class="flex gap-1 items-center">
                      <input v-if="port.connected_device_id && portConnectionMap[port.connected_device_id]" type="color" :value="portConnectionMap[port.connected_device_id].color || '#94a3b8'" class="w-5 h-5 rounded cursor-pointer border-0 p-0" @input="updateConnColor(portConnectionMap[port.connected_device_id].id, $event.target.value)" title="Couleur du câble" />
                      <button class="btn btn-ghost btn-xs" @click="openConnectPort(port)">
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
                      </button>
                      <button class="btn btn-ghost btn-xs" @click="deletePort(port.id)">
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      <div>
        <div class="card bg-base-200">
          <div class="card-body">
            <h2 class="card-title">Actions</h2>
            <button class="btn btn-outline w-full" onclick="edit_modal.showModal()">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
              Modifier
            </button>
            <button class="btn btn-outline w-full mt-2" @click="enrichDevice" :disabled="enriching">
              <svg v-if="!enriching" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
              <span v-else class="loading loading-spinner loading-xs"></span>
              Enrichir
            </button>
            <button class="btn btn-outline btn-error w-full mt-2" @click="remove">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
              Supprimer
            </button>
          </div>
        </div>


      </div>
    </div>

    <dialog id="edit_modal" class="modal">
      <div class="modal-box">
        <h3 class="text-lg font-bold mb-4">Modifier {{ capitalize(device.name) }}</h3>
        <form @submit.prevent="updateDevice">
          <div class="form-control mb-3">
            <label class="label"><span class="label-text">Nom</span></label>
            <input v-model="editForm.name" class="input input-bordered" required />
          </div>
          <div class="form-control mb-3">
            <label class="label"><span class="label-text">Type</span></label>
            <select v-model="editForm.device_type" class="select select-bordered">
              <option value="computer">Ordinateur</option>
              <option value="router">Routeur</option>
              <option value="modem">Modem</option>
              <option value="ap">Point d'accès</option>
              <option value="switch">Switch</option>
              <option value="server">Serveur</option>
              <option value="iot">IoT</option>
              <option value="other">Autre</option>
            </select>
          </div>
          <div class="form-control mb-3">
            <label class="label"><span class="label-text">Fabricant</span></label>
            <input v-model="editForm.manufacturer" class="input input-bordered" />
          </div>
          <div class="form-control mb-3">
            <label class="label"><span class="label-text">Hostname</span></label>
            <input v-model="editForm.hostname" class="input input-bordered" />
          </div>
          <div class="form-control mb-3">
            <label class="label"><span class="label-text">Type IP</span></label>
            <select v-model="editForm.ip_type" class="select select-bordered">
              <option value="">Automatique / Inconnu</option>
              <option value="static">Static (fixe)</option>
              <option value="dhcp">DHCP (dynamique)</option>
            </select>
          </div>
          <div class="form-control mb-3">
            <label class="label"><span class="label-text">Modèle</span></label>
            <input v-model="editForm.model" class="input input-bordered" />
          </div>
          <div class="form-control mb-3">
            <label class="label"><span class="label-text">IP</span></label>
            <input v-model="editForm.ipv4" class="input input-bordered" />
          </div>
          <div class="form-control mb-3">
            <label class="label"><span class="label-text">MAC</span></label>
            <input v-model="editForm.mac" class="input input-bordered" />
          </div>
          <div class="form-control mb-3">
            <label class="label"><span class="label-text">Emplacement</span></label>
            <select v-model="editForm.location_id" class="select select-bordered">
              <option :value="null">- Aucun -</option>
              <option v-for="loc in locations" :key="loc.id" :value="loc.id">{{ capitalize(loc.name) }} ({{ loc.floor || '?' }})</option>
            </select>
          </div>
          <div class="form-control mb-3">
            <label class="label"><span class="label-text">Notes</span></label>
            <textarea v-model="editForm.notes" class="textarea textarea-bordered" rows="3"></textarea>
          </div>
          <div class="modal-action">
            <button type="button" class="btn" onclick="edit_modal.close()">Annuler</button>
            <button type="submit" class="btn btn-primary">Enregistrer</button>
          </div>
        </form>
      </div>
    </dialog>

    <dialog id="port_modal" class="modal">
      <div class="modal-box">
        <h3 class="text-lg font-bold mb-4">Ajouter un port</h3>
        <form @submit.prevent="addPort">
          <div class="form-control mb-3">
            <label class="label"><span class="label-text">Nom du port</span></label>
            <input v-model="portForm.name" class="input input-bordered" required placeholder="ex: Port 1, GE1" />
          </div>
          <div class="form-control mb-3">
            <label class="label"><span class="label-text">VLAN</span></label>
            <input v-model="portForm.vlan" class="input input-bordered" />
          </div>
          <div class="form-control mb-3">
            <label class="label cursor-pointer">
              <span class="label-text">PoE</span>
              <input type="checkbox" v-model="portForm.poe" class="toggle" />
            </label>
          </div>
          <div class="modal-action">
            <button type="button" class="btn" onclick="port_modal.close()">Annuler</button>
            <button type="submit" class="btn btn-primary">Ajouter</button>
          </div>
        </form>
      </div>
    </dialog>

    <dialog id="connect_port_modal" class="modal">
      <div class="modal-box">
        <h3 class="text-lg font-bold mb-4">Connecter {{ connectPort?.name }}</h3>
        <form @submit.prevent="connectPortSubmit">
          <div class="form-control mb-3">
            <label class="label"><span class="label-text">Périphérique</span></label>
            <select v-model="connectDeviceId" class="select select-bordered">
              <option :value="null">- Déconnecter -</option>
              <option v-for="d in availableDevices" :key="d.id" :value="d.id">{{ capitalize(d.name) }} ({{ d.ipv4 || '?' }})</option>
            </select>
          </div>
          <div class="modal-action">
            <button type="button" class="btn" onclick="connect_port_modal.close()">Annuler</button>
            <button type="submit" class="btn btn-primary">Connecter</button>
          </div>
        </form>
      </div>
    </dialog>
  </div>
  <div v-else class="flex justify-center py-20">
    <span class="loading loading-spinner loading-lg"></span>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'

const route = useRoute()
const router = useRouter()
const device = ref(null)
const allDevices = ref([])
const connections = ref([])
const locations = ref([])

const editForm = ref({})
const portForm = ref({ name: '', vlan: '', poe: false })
const connectPort = ref(null)
const enriching = ref(false)
const connectDeviceId = ref(null)

const sortedPorts = computed(() =>
  device.value?.ports ? [...device.value.ports].sort((a, b) => a.name.localeCompare(b.name, undefined, { numeric: true })) : []
)

const deviceConnections = computed(() =>
  connections.value.filter(c =>
    c.device_a_id === device.value?.id || c.device_b_id === device.value?.id
  )
)

const portConnectionMap = computed(() => {
  const map = {}
  if (!device.value) return map
  for (const c of deviceConnections.value) {
    const otherId = c.device_a_id === device.value.id ? c.device_b_id : c.device_a_id
    map[otherId] = c
  }
  return map
})

const availableDevices = computed(() =>
  allDevices.value.filter(d => d.id !== device.value?.id)
)

function capitalize(s) {
  return s ? s.charAt(0).toUpperCase() + s.slice(1) : ''
}

function badgeClass(type) {
  const map = {
    router: 'badge-info', modem: 'badge-secondary', ap: 'badge-accent',
    switch: 'badge-warning', computer: 'badge-success', server: 'badge-error',
    iot: 'badge-ghost',
  }
  return map[type] || ''
}

function navigateTo(id) {
  router.push(`/devices/${id}`)
}

async function fetchData() {
  const [devRes, devsRes, connRes, locRes] = await Promise.all([
    axios.get(`/api/devices/${route.params.id}`),
    axios.get('/api/devices'),
    axios.get('/api/connections'),
    axios.get('/api/locations'),
  ])
  device.value = devRes.data
  allDevices.value = devsRes.data
  connections.value = connRes.data
  locations.value = locRes.data
  editForm.value = { ...devRes.data }
}

async function updateDevice() {
  await axios.put(`/api/devices/${device.value.id}`, editForm.value)
  document.getElementById('edit_modal').close()
  fetchData()
}

async function enrichDevice() {
  enriching.value = true
  try {
    const { data } = await axios.post(`/api/enrich/${device.value.id}`)
    device.value = data.device
    editForm.value = { ...data.device }
  } catch (e) {
    console.error('Enrich failed:', e)
  }
  enriching.value = false
}

async function remove() {
  if (!confirm('Supprimer ce périphérique ?')) return
  await axios.delete(`/api/devices/${device.value.id}`)
  router.push('/devices')
}

async function addPort() {
  await axios.post(`/api/devices/${device.value.id}/ports`, portForm.value)
  portForm.value = { name: '', vlan: '', poe: false }
  document.getElementById('port_modal').close()
  fetchData()
}

async function deletePort(id) {
  if (!confirm('Supprimer ce port ?')) return
  await axios.delete(`/api/ports/${id}`)
  fetchData()
}

function openConnectPort(port) {
  connectPort.value = port
  connectDeviceId.value = port.connected_device_id || null
  document.getElementById('connect_port_modal').showModal()
}

async function connectPortSubmit() {
  await axios.put(`/api/ports/${connectPort.value.id}`, {
    connected_device_id: connectDeviceId.value,
  })
  document.getElementById('connect_port_modal').close()
  fetchData()
}

async function updateConnColor(connId, color) {
  await axios.put(`/api/connections/${connId}`, { color })
  connections.value = connections.value.map(c =>
    c.id === connId ? { ...c, color } : c
  )
}

async function deleteConnection(id) {
  if (!confirm('Supprimer cette connexion ?')) return
  await axios.delete(`/api/connections/${id}`)
  fetchData()
}

onMounted(fetchData)

watch(() => route.params.id, (newId, oldId) => {
  if (newId !== oldId) {
    device.value = null
    fetchData()
  }
})
</script>
