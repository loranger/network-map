<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">Périphériques</h1>
      <div class="flex gap-2">
        <input v-model="scanSubnet" type="text" placeholder="192.168.1.0/24" class="input input-bordered w-44 hidden md:inline-flex" title="Sous-réseau à scanner" />
        <button class="btn btn-outline" @click="scanNetwork" :disabled="scanning">
          <Search v-if="!scanning" :size="18" :stroke-width="2" />
          <span v-else class="loading loading-spinner"></span>
          Scanner
        </button>
        <button class="btn btn-outline" onclick="import_arp_modal.showModal()">
          <Download :size="18" :stroke-width="2" />
          Importer ARP
        </button>
        <button class="btn btn-outline" @click="enrichDevices" :disabled="enriching">
          <Info v-if="!enriching" :size="18" :stroke-width="2" />
          <span v-else class="loading loading-spinner"></span>
          Enrichir
        </button>
        <button class="btn btn-primary" onclick="add_modal.showModal()">
          <Plus :size="18" :stroke-width="2" />
          Ajouter
        </button>
      </div>
    </div>

    <div class="flex gap-2 mb-4 flex-wrap">
      <input v-model="filterName" type="search" placeholder="Rechercher…" class="input input-bordered input-sm flex-1 min-w-[160px]" />
      <select class="select select-bordered select-sm" v-model="filterType">
        <option value="">Tous les types</option>
        <option v-for="dt in deviceTypes" :key="dt.type" :value="dt.type">{{ dt.label }}</option>
      </select>
      <select class="select select-bordered select-sm" v-model="filterLocation">
        <option value="">Tous les emplacements</option>
        <option v-for="loc in locations" :key="loc.id" :value="loc.id">{{ capitalize(loc.name) }}</option>
      </select>
      <select class="select select-bordered select-sm" v-model="filterNetwork">
        <option value="">Tous les réseaux</option>
        <option v-for="net in networks" :key="net.id" :value="net.id">{{ net.name }}</option>
      </select>
      <select class="select select-bordered select-sm" v-model="filterStatus">
        <option value="">En ligne et hors ligne</option>
        <option value="online">En ligne</option>
        <option value="offline">Hors ligne</option>
      </select>
    </div>

    <div class="overflow-x-auto">
      <table class="table table-zebra">
        <thead>
          <tr>
            <th class="cursor-pointer select-none" @click="toggleSort('name')">
              Nom <span v-if="sortCol === 'name'" class="text-xs">{{ sortDir === 'asc' ? '▲' : '▼' }}</span>
            </th>
            <th class="hidden md:table-cell cursor-pointer select-none" @click="toggleSort('device_type')">
              Type <span v-if="sortCol === 'device_type'" class="text-xs">{{ sortDir === 'asc' ? '▲' : '▼' }}</span>
            </th>
            <th class="hidden sm:table-cell">IP / MAC / Réseau</th>
            <th class="hidden xl:table-cell cursor-pointer select-none" @click="toggleSort('manufacturer')">
              Fabricant <span v-if="sortCol === 'manufacturer'" class="text-xs">{{ sortDir === 'asc' ? '▲' : '▼' }}</span>
            </th>
            <th class="cursor-pointer select-none" @click="toggleSort('location_name')">
              Emplacement <span v-if="sortCol === 'location_name'" class="text-xs">{{ sortDir === 'asc' ? '▲' : '▼' }}</span>
            </th>
            <th class="hidden xl:table-cell cursor-pointer select-none" @click="toggleSort('location_floor')">
              Étage <span v-if="sortCol === 'location_floor'" class="text-xs">{{ sortDir === 'asc' ? '▲' : '▼' }}</span>
            </th>
            <th class="hidden md:table-cell cursor-pointer select-none" @click="toggleSort('last_seen')">
              Dernière apparition <span v-if="sortCol === 'last_seen'" class="text-xs">{{ sortDir === 'asc' ? '▲' : '▼' }}</span>
            </th>
            <th class="hidden md:table-cell">Admin</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="d in filteredDevices" :key="d.id" :class="{ 'opacity-50': !d.online }">
            <td class="font-medium">
              <div class="flex items-center gap-2">
                <img :src="iconDataUrl(deviceIconName(d), '#334155')" class="w-5 h-5 opacity-70 shrink-0" />
                <router-link :to="`/devices/${d.id}`" class="link link-hover">{{ capitalize(d.name) }}</router-link>
              </div>
            </td>
            <td class="hidden md:table-cell">
              <span class="badge text-white border-0" :style="{ backgroundColor: typeColor(d.device_type) }">{{ typeLabel(d.device_type) }}</span>
            </td>
            <td class="hidden sm:table-cell text-sm">
              <div v-if="d.ips && d.ips.length > 0" class="space-y-1.5">
                <div v-for="ip in d.ips" :key="ip.id" class="flex items-center gap-1.5 flex-wrap">
                  <span class="font-mono">{{ ip.ipv4 || '-' }}</span>
                  <span v-if="ip.mac" class="font-mono text-[0.7rem] opacity-50">{{ ip.mac }}</span>
                  <span v-if="ip.network_name" class="badge badge-sm border-0 text-white" :style="{ backgroundColor: networkColor(ip.network_id) }">{{ ip.network_name }}</span>
                </div>
              </div>
              <span v-else class="opacity-40">-</span>
            </td>
            <td class="hidden xl:table-cell text-sm">{{ d.manufacturer || '-' }}</td>
            <td>{{ capitalize(d.location_name) || '-' }}</td>
            <td class="hidden xl:table-cell">{{ capitalize(d.location_floor) || '-' }}</td>
            <td class="hidden md:table-cell text-sm" :title="d.last_seen ? new Date(d.last_seen + 'Z').toLocaleString() : ''">
              {{ formatLastSeen(d.last_seen) }}
            </td>
            <td class="hidden md:table-cell">
              <a v-if="d.admin_url" :href="resolveAdminUrl(d)" target="_blank" rel="noopener noreferrer" class="link link-primary" @click.stop>
                <ExternalLink :size="16" :stroke-width="2" />
              </a>
              <span v-else class="opacity-30">-</span>
            </td>
            <td>
              <button class="btn btn-ghost btn-xs" @click="deleteDevice(d.id)">
                <Trash2 :size="16" :stroke-width="2" />
              </button>
            </td>
          </tr>
          <tr v-if="filteredDevices.length === 0">
            <td colspan="10" class="text-center text-base-content/50 py-8">
              Aucun périphérique trouvé
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <dialog id="import_arp_modal" class="modal">
      <div class="modal-box max-w-2xl">
        <h3 class="text-lg font-bold mb-2">Importer ARP</h3>
        <p class="text-sm text-base-content/60 mb-4">
          Colle le résultat de <code class="bg-base-200 px-1 rounded">arp -a</code> exécuté depuis ton Mac/Linux.
          Les périphériques avec adresse MAC seront créés automatiquement.
        </p>
        <form @submit.prevent="importArp">
          <div class="form-control mb-3">
            <textarea v-model="arpRaw" class="textarea textarea-bordered font-mono text-sm h-48" placeholder="$ arp -a&#10;? (192.168.1.10) at 50:eb:f6:77:e6:40 on en0 ifscope [ethernet]&#10;? (192.168.1.11) at 6c:a0:42:dd:18:50 on en0 ifscope [ethernet]" required></textarea>
          </div>
          <div v-if="importResult" class="alert mb-3" :class="importResultClass">
            <span>{{ importResult }}</span>
          </div>
          <div class="modal-action">
            <button type="button" class="btn" onclick="import_arp_modal.close()">Fermer</button>
            <button type="submit" class="btn btn-primary" :disabled="importing">
              <span v-if="importing" class="loading loading-spinner"></span>
              Importer
            </button>
          </div>
        </form>
      </div>
    </dialog>

    <dialog id="add_modal" class="modal">
      <div class="modal-box">
        <h3 class="text-lg font-bold mb-4">Ajouter un périphérique</h3>
        <form @submit.prevent="addDevice">
          <div class="form-control mb-3">
            <label class="label"><span class="label-text">Nom</span></label>
            <input v-model="form.name" class="input input-bordered" required />
          </div>
          <div class="form-control mb-3">
            <label class="label"><span class="label-text">Type</span></label>
            <select v-model="form.device_type" class="select select-bordered" required>
              <option v-for="dt in deviceTypes" :key="dt.type" :value="dt.type">{{ dt.label }}</option>
            </select>
          </div>
          <div class="form-control mb-3">
            <label class="label"><span class="label-text">Adresse IP</span></label>
            <input v-model="form.ip" class="input input-bordered" placeholder="192.168.1.x" />
          </div>
          <div class="form-control mb-3">
            <label class="label"><span class="label-text">Emplacement</span></label>
            <select v-model="form.location_id" class="select select-bordered">
              <option :value="null">- Aucun -</option>
              <option v-for="loc in locations" :key="loc.id" :value="loc.id">{{ capitalize(loc.name) }} ({{ loc.floor_name || '?' }})</option>
            </select>
          </div>
          <div class="form-control mb-3">
            <label class="label"><span class="label-text">Interface d'administration</span></label>
            <input v-model="form.admin_url" class="input input-bordered font-mono" placeholder="http://{ip}:8080/admin" />
          </div>
          <div class="modal-action">
            <button type="button" class="btn" onclick="add_modal.close()">Annuler</button>
            <button type="submit" class="btn btn-primary">Ajouter</button>
          </div>
        </form>
      </div>
    </dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { Search, Download, Info, Plus, Trash2, ExternalLink } from '@lucide/vue'
import { iconDataUrl } from '../icons.js'

const devices = ref([])
const locations = ref([])
const networks = ref([])
const deviceTypes = ref([])
const filterName = ref('')
const filterType = ref('')
const filterLocation = ref('')
const filterNetwork = ref('')
const filterStatus = ref('')
const sortCol = ref('name')
const sortDir = ref('asc')
const scanning = ref(false)
const enriching = ref(false)
const scanSubnet = ref('')

const form = ref({
  name: '', device_type: 'computer', ip: '', location_id: null, admin_url: '',
})

const filteredDevices = computed(() => {
  let list = devices.value.filter(d => {
    if (filterName.value) {
      const q = filterName.value.toLowerCase()
      const nameMatch = d.name.toLowerCase().includes(q)
      const ipMatch = (d.ips || []).some(ip => (ip.ipv4 || '').toLowerCase().includes(q))
      if (!nameMatch && !ipMatch) return false
    }
    if (filterType.value && d.device_type !== filterType.value) return false
    if (filterLocation.value && d.location_id !== Number(filterLocation.value)) return false
    if (filterNetwork.value) {
      const netId = Number(filterNetwork.value)
      const ipNetIds = (d.ips || []).map(ip => ip.network_id).filter(id => id != null)
      const apNetIds = d.ap_network_ids || []
      const allNetIds = [...ipNetIds, ...apNetIds]
      if (!allNetIds.includes(netId)) return false
    }
    if (filterStatus.value === 'online' && d.online === false) return false
    if (filterStatus.value === 'offline' && d.online !== false) return false
    return true
  })
  if (sortCol.value) {
    list = [...list].sort((a, b) => {
      const va = (a[sortCol.value] || '').toString().toLowerCase()
      const vb = (b[sortCol.value] || '').toString().toLowerCase()
      if (va === '' && vb !== '') return 1
      if (vb === '' && va !== '') return -1
      return sortDir.value === 'asc' ? va.localeCompare(vb) : vb.localeCompare(va)
    })
  }
  return list
})

function toggleSort(col) {
  if (sortCol.value === col) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortCol.value = col
    sortDir.value = col === 'last_seen' ? 'desc' : 'asc'
  }
}

function capitalize(s) {
  return s ? s.charAt(0).toUpperCase() + s.slice(1) : ''
}

function formatLastSeen(ts) {
  if (!ts) return '-'
  const d = new Date(ts + 'Z')
  if (isNaN(d.getTime())) return '-'
  const diffMin = Math.floor((Date.now() - d.getTime()) / 60000)
  if (diffMin < 1) return "à l'instant"
  if (diffMin < 60) return `il y a ${diffMin} min`
  const diffHours = Math.floor(diffMin / 60)
  if (diffHours < 24) return `il y a ${diffHours} h`
  return d.toLocaleDateString()
}

function typeColor(type) {
  const found = deviceTypes.value.find(dt => dt.type === type)
  return found ? found.color : '#6b7280'
}

function resolveAdminUrl(d) {
  if (!d.admin_url) return null
  const ip = d.ips?.[0]?.ipv4
  if (!ip) return d.admin_url
  return d.admin_url.replace(/\{ip\}/g, ip)
}

function typeLabel(type) {
  const found = deviceTypes.value.find(dt => dt.type === type)
  return found ? found.label : type
}

function deviceIconName(d) {
  if (d.icon) return d.icon
  const dt = deviceTypes.value.find(t => t.type === d.device_type)
  return dt?.icon || 'box'
}

function networkColor(networkId) {
  const found = networks.value.find(n => n.id === networkId)
  return found?.color || '#6b7280'
}

async function fetchDevices() {
  const { data } = await axios.get('/api/devices')
  devices.value = data
}

async function fetchLocations() {
  const { data } = await axios.get('/api/locations')
  locations.value = data
}

async function fetchDeviceTypes() {
  const { data } = await axios.get('/api/device-types')
  deviceTypes.value = data
}

async function fetchNetworks() {
  const { data } = await axios.get('/api/networks')
  networks.value = data
}

async function addDevice() {
  const payload = {
    name: form.value.name,
    device_type: form.value.device_type,
    location_id: form.value.location_id,
    admin_url: form.value.admin_url,
    ips: form.value.ip ? [{ ipv4: form.value.ip }] : [],
  }
  await axios.post('/api/devices', payload)
  form.value = { name: '', device_type: 'computer', ip: '', location_id: null, admin_url: '' }
  document.getElementById('add_modal').close()
  fetchDevices()
}

async function deleteDevice(id) {
  if (!confirm('Supprimer ce périphérique ?')) return
  await axios.delete(`/api/devices/${id}`)
  fetchDevices()
}

async function scanNetwork() {
  scanning.value = true
  try {
    const payload = scanSubnet.value ? { subnet: scanSubnet.value } : {}
    const { data } = await axios.post('/api/scan', payload)
    if (data.hint) {
      alert(data.hint)
    } else {
      alert(`Scan terminé : ${data.found} périphérique(s) trouvé(s)`)
    }
    fetchDevices()
  } catch (e) {
    console.error('Scan failed:', e)
  }
  scanning.value = false
}

async function enrichDevices() {
  enriching.value = true
  try {
    const { data } = await axios.post('/api/enrich')
    alert(`Enrichis : ${data.enriched} / ${data.total} périphériques`)
    fetchDevices()
  } catch (e) {
    console.error('Enrich failed:', e)
  }
  enriching.value = false
}

const arpRaw = ref('')
const importing = ref(false)
const importResult = ref('')
const importResultClass = ref('')

async function importArp() {
  importing.value = true
  importResult.value = ''
  try {
    const { data } = await axios.post('/api/scan/import', { raw: arpRaw.value })
    importResult.value = `Créés : ${data.created} · Mis à jour : ${data.updated} · Ignorés : ${data.ignored}`
    importResultClass.value = 'alert-success'
    arpRaw.value = ''
    fetchDevices()
  } catch (e) {
    importResult.value = 'Erreur lors de l\'import'
    importResultClass.value = 'alert-error'
  }
  importing.value = false
}

onMounted(() => {
  fetchDevices()
  fetchLocations()
  fetchDeviceTypes()
  fetchNetworks()
})
</script>