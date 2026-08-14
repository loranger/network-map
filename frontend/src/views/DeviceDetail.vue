<template>
  <div v-if="device">
    <div class="flex items-center gap-3 mb-6">
      <router-link to="/devices" class="btn btn-ghost btn-circle">
        <ArrowLeft :size="20" :stroke-width="2" />
      </router-link>
      <h1 class="text-2xl font-bold">{{ capitalize(device.name) }}</h1>
      <span class="badge badge-lg text-white border-0" :style="{ backgroundColor: typeColor(device.device_type) }">{{ typeLabel(device.device_type) }}</span>
    </div>

    <div class="card bg-base-200">
      <div class="card-body">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="text-sm opacity-60">Nom</label>
            <p class="font-medium">{{ capitalize(device.name) }}</p>
          </div>
          <div>
            <label class="text-sm opacity-60">Hostname</label>
            <p class="font-mono">{{ device.hostname || '-' }}</p>
          </div>
          <div>
            <label class="text-sm opacity-60">Emplacement</label>
            <p>{{ capitalize(device.location_name) || '-' }} <span v-if="device.location_floor" class="opacity-50">({{ capitalize(device.location_floor) }})</span></p>
          </div>
          <div>
            <label class="text-sm opacity-60">Fabricant</label>
            <p>{{ device.manufacturer || '-' }}</p>
          </div>
          <div>
            <label class="text-sm opacity-60">Modèle</label>
            <p>{{ device.model || '-' }}</p>
          </div>
          <div>
            <label class="text-sm opacity-60">Découvert automatiquement</label>
            <p>{{ device.discovered ? 'Oui' : 'Non' }}</p>
          </div>
          <div v-if="device.admin_url">
            <label class="text-sm opacity-60">Interface d'administration</label>
            <p>
              <a v-if="resolvedAdminUrl" :href="resolvedAdminUrl" target="_blank" rel="noopener noreferrer" class="link link-primary font-mono break-all">{{ resolvedAdminUrl }}</a>
              <span v-else class="font-mono opacity-70">{{ device.admin_url }}</span>
            </p>
            <p v-if="device.admin_url.includes('{ip}')" class="text-xs opacity-50 mt-1">Placeholder <code class="bg-base-300 px-1 rounded">{ip}</code> résolu en {{ firstIp }}</p>
          </div>
        </div>

         <div class="mt-4">
          <label class="text-sm opacity-60 block mb-1">Adresses IP</label>
          <div v-if="device.ips && device.ips.length > 0" class="space-y-1">
            <div v-for="ip in device.ips" :key="ip.id" class="flex items-center gap-2 font-mono text-sm flex-wrap">
              <span>{{ ip.ipv4 }}</span>
              <span v-if="ip.network_name" class="badge badge-sm border-0 text-white" :style="{ backgroundColor: networkColor(ip.network_id) }">{{ ip.network_name }}</span>
              <span v-if="ip.ip_type === 'static'" class="badge badge-outline badge-xs">Static</span>
              <span v-else-if="ip.ip_type === 'dhcp'" class="badge badge-outline badge-xs">DHCP</span>
              <span v-if="ip.mac" class="text-xs opacity-50">{{ ip.mac }}</span>
            </div>
          </div>
          <p v-else class="text-sm opacity-50">-</p>
        </div>

        <div v-if="device.notes" class="mt-4">
          <label class="text-sm opacity-60">Notes</label>
          <p class="whitespace-pre-wrap">{{ device.notes }}</p>
        </div>

        <div class="card-actions justify-end mt-4">
          <button class="btn btn-ghost btn-xs" @click="openEditModal">
            <Pencil :size="16" :stroke-width="2" />
          </button>
          <button class="btn btn-ghost btn-xs" @click="remove">
            <Trash2 :size="16" :stroke-width="2" />
          </button>
        </div>
      </div>
    </div>

    <div v-if="device.device_type === 'switch'" class="card bg-base-200 mt-6">
      <div class="card-body">
        <div class="flex items-center justify-between">
          <h2 class="card-title">Ports</h2>
          <button class="btn btn-primary btn-sm" @click="openPortModal">
            <Plus :size="16" :stroke-width="2" />
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
                    <Link2 :size="14" :stroke-width="2" />
                  </button>
                  <button class="btn btn-ghost btn-xs" @click="deletePort(port.id)">
                    <Trash2 :size="14" :stroke-width="2" />
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <dialog ref="editModal" class="modal">
      <div class="modal-box max-w-4xl">
        <h3 class="text-lg font-bold mb-4">Modifier {{ capitalize(device.name) }}</h3>
        <form @submit.prevent="updateDevice">
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-3">
            <div class="form-control">
              <label class="label"><span class="label-text">Nom</span></label>
              <input v-model="editForm.name" class="input input-bordered" required />
            </div>
            <div class="form-control">
              <label class="label"><span class="label-text">Hostname</span></label>
              <input v-model="editForm.hostname" class="input input-bordered" />
            </div>
            <div class="form-control">
              <label class="label"><span class="label-text">Type</span></label>
              <select v-model="editForm.device_type" class="select select-bordered">
                <option v-for="dt in deviceTypes" :key="dt.type" :value="dt.type">{{ dt.label }}</option>
              </select>
            </div>
          </div>

          <label class="label pb-1"><span class="label-text">Adresses IP</span></label>
          <div v-for="(ipEntry, idx) in editForm.ips" :key="idx" class="flex items-end gap-2 mb-2">
            <div class="flex-1">
              <select v-model="ipEntry.network_id" class="select select-bordered select-sm w-full">
                <option :value="null">- Réseau -</option>
                <option v-for="net in networks" :key="net.id" :value="net.id">{{ net.name }}</option>
              </select>
            </div>
            <div class="flex-[2]">
              <input v-model="ipEntry.ipv4" class="input input-bordered input-sm w-full" placeholder="192.168.1.x" />
            </div>
            <div class="flex-1">
              <select v-model="ipEntry.ip_type" class="select select-bordered select-sm w-full">
                <option value="">Type</option>
                <option value="static">Static</option>
                <option value="dhcp">DHCP</option>
              </select>
            </div>
            <div class="flex-[2]">
              <input v-model="ipEntry.mac" class="input input-bordered input-sm w-full font-mono" placeholder="XX:XX:XX:XX:XX:XX" />
            </div>
            <button type="button" class="btn btn-ghost btn-xs mb-0.5" @click="removeIp(idx)">
              <X :size="16" :stroke-width="2" />
            </button>
          </div>
          <button type="button" class="btn btn-outline btn-xs mb-3" @click="addIp">
            <Plus :size="14" :stroke-width="2" />
            Ajouter une IP
          </button>

          <div class="form-control mb-3">
            <label class="label"><span class="label-text">Interface d'administration</span></label>
            <input v-model="editForm.admin_url" class="input input-bordered font-mono" placeholder="http://{ip}:8080/admin" />
            <label class="label"><span class="label-text-alt text-xs opacity-60">Utilisez <code class="bg-base-300 px-1 rounded">{ip}</code> comme placeholder pour la première IP</span></label>
          </div>

          <div class="form-control mb-3">
            <label class="label"><span class="label-text">Emplacement</span></label>
            <select v-model="editForm.location_id" class="select select-bordered">
              <option :value="null">- Aucun -</option>
              <option v-for="loc in locations" :key="loc.id" :value="loc.id">{{ capitalize(loc.name) }} ({{ loc.floor_name || '?' }})</option>
            </select>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-3">
            <div class="form-control">
              <label class="label"><span class="label-text">Fabricant</span></label>
              <input v-model="editForm.manufacturer" class="input input-bordered" />
            </div>
            <div class="form-control">
              <label class="label"><span class="label-text">Modèle</span></label>
              <input v-model="editForm.model" class="input input-bordered" />
            </div>
          </div>

          <div class="form-control mb-3">
            <label class="label"><span class="label-text">Notes</span></label>
            <textarea v-model="editForm.notes" class="textarea textarea-bordered" rows="3"></textarea>
          </div>

          <div class="form-control mb-3">
            <label class="label"><span class="label-text">Icône</span></label>
            <IconPicker v-model="editForm.icon" />
          </div>

          <div class="modal-action">
            <button type="button" class="btn btn-outline" @click="enrichDevice" :disabled="enriching">
              <Info v-if="!enriching" :size="16" :stroke-width="2" />
              <span v-else class="loading loading-spinner loading-xs"></span>
              Enrichir
            </button>
            <button type="button" class="btn" @click="closeEditModal">Annuler</button>
            <button type="submit" class="btn btn-primary">Enregistrer</button>
          </div>
        </form>
      </div>
    </dialog>

    <dialog ref="portModal" class="modal">
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
            <button type="button" class="btn" @click="closePortModal">Annuler</button>
            <button type="submit" class="btn btn-primary">Ajouter</button>
          </div>
        </form>
      </div>
    </dialog>

    <dialog ref="connectPortModal" class="modal">
      <div class="modal-box">
        <h3 class="text-lg font-bold mb-4">Connecter {{ connectPort?.name }}</h3>
        <form @submit.prevent="connectPortSubmit">
          <div class="form-control mb-3">
            <label class="label"><span class="label-text">Périphérique</span></label>
            <select v-model="connectDeviceId" class="select select-bordered">
              <option :value="null">- Déconnecter -</option>
              <option v-for="d in availableDevices" :key="d.id" :value="d.id">{{ capitalize(d.name) }} ({{ d.ips?.[0]?.ipv4 || '?' }})</option>
            </select>
          </div>
          <div class="modal-action">
            <button type="button" class="btn" @click="closeConnectModal">Annuler</button>
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
import { ArrowLeft, Plus, Link2, Trash2, Pencil, Info, X } from '@lucide/vue'
import IconPicker from '../components/IconPicker.vue'

const route = useRoute()
const router = useRouter()
const device = ref(null)
const allDevices = ref([])
const connections = ref([])
const locations = ref([])
const networks = ref([])
const deviceTypes = ref([])

const editForm = ref({ name: '', device_type: 'other', ips: [], hostname: '', manufacturer: '', model: '', notes: '', admin_url: '', location_id: null })
const portForm = ref({ name: '', vlan: '', poe: false })
const connectPort = ref(null)

const connectDeviceId = ref(null)
const enriching = ref(false)

const editModal = ref(null)
const portModal = ref(null)
const connectPortModal = ref(null)

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
  allDevices.value
    .filter(d => d.id !== device.value?.id)
    .sort((a, b) => a.name.toLowerCase().localeCompare(b.name.toLowerCase()))
)

const firstIp = computed(() =>
  device.value?.ips?.[0]?.ipv4 || null
)

const resolvedAdminUrl = computed(() => {
  if (!device.value?.admin_url) return null
  const ip = firstIp.value
  if (!ip) return null
  return device.value.admin_url.replace(/\{ip\}/g, ip)
})

function capitalize(s) {
  return s ? s.charAt(0).toUpperCase() + s.slice(1) : ''
}

function typeColor(type) {
  const found = deviceTypes.value.find(dt => dt.type === type)
  return found ? found.color : '#6b7280'
}

function typeLabel(type) {
  const found = deviceTypes.value.find(dt => dt.type === type)
  return found ? found.label : type
}

function networkColor(networkId) {
  const found = networks.value.find(n => n.id === networkId)
  return found?.color || '#6b7280'
}

function navigateTo(id) {
  router.push(`/devices/${id}`)
}

function openEditModal() {
  editForm.value = {
    name: device.value.name,
    device_type: device.value.device_type,
    hostname: device.value.hostname || '',
    manufacturer: device.value.manufacturer || '',
    model: device.value.model || '',
    notes: device.value.notes || '',
    admin_url: device.value.admin_url || '',
    icon: device.value.icon || null,
    location_id: device.value.location_id,
    ips: (device.value.ips || []).map(ip => ({
      ipv4: ip.ipv4 || '',
      mac: ip.mac || '',
      network_id: ip.network_id,
      ip_type: ip.ip_type || '',
    })),
  }
  if (editForm.value.ips.length === 0) {
    editForm.value.ips.push({ ipv4: '', mac: '', network_id: null, ip_type: '' })
  }
  editModal.value?.showModal()
}

function closeEditModal() {
  editModal.value?.close()
}

function addIp() {
  editForm.value.ips.push({ ipv4: '', mac: '', network_id: null, ip_type: '' })
}

function removeIp(idx) {
  editForm.value.ips.splice(idx, 1)
}

function openPortModal() {
  portForm.value = { name: '', vlan: '', poe: false }
  portModal.value?.showModal()
}

function closePortModal() {
  portModal.value?.close()
}

async function fetchData() {
  const [devRes, devsRes, connRes, locRes, netRes, dtRes] = await Promise.all([
    axios.get(`/api/devices/${route.params.id}`),
    axios.get('/api/devices'),
    axios.get('/api/connections'),
    axios.get('/api/locations'),
    axios.get('/api/networks'),
    axios.get('/api/device-types'),
  ])
  device.value = devRes.data
  allDevices.value = devsRes.data
  connections.value = connRes.data
  locations.value = locRes.data
  networks.value = netRes.data
  deviceTypes.value = dtRes.data
}

async function updateDevice() {
  const payload = { ...editForm.value }
  await axios.put(`/api/devices/${device.value.id}`, payload)
  closeEditModal()
  fetchData()
}

async function enrichDevice() {
  enriching.value = true
  try {
    const { data } = await axios.post(`/api/enrich/${device.value.id}`)
    device.value = data.device
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
  closePortModal()
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
  connectPortModal.value?.showModal()
}

function closeConnectModal() {
  connectPortModal.value?.close()
}

async function connectPortSubmit() {
  await axios.put(`/api/ports/${connectPort.value.id}`, {
    connected_device_id: connectDeviceId.value,
  })
  closeConnectModal()
  fetchData()
}

async function updateConnColor(connId, color) {
  await axios.put(`/api/connections/${connId}`, { color })
  connections.value = connections.value.map(c =>
    c.id === connId ? { ...c, color } : c
  )
}

onMounted(fetchData)

watch(() => route.params.id, (newId, oldId) => {
  if (newId !== oldId) {
    device.value = null
    fetchData()
  }
})
</script>