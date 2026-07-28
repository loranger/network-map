<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">Périphériques</h1>
      <div class="flex gap-2">
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
            <th class="hidden sm:table-cell cursor-pointer select-none" @click="toggleSort('ipv4')">
              IP <span v-if="sortCol === 'ipv4'" class="text-xs">{{ sortDir === 'asc' ? '▲' : '▼' }}</span>
            </th>
            <th class="hidden sm:table-cell">Type IP</th>
            <th class="hidden lg:table-cell cursor-pointer select-none" @click="toggleSort('mac')">
              MAC <span v-if="sortCol === 'mac'" class="text-xs">{{ sortDir === 'asc' ? '▲' : '▼' }}</span>
            </th>
            <th class="hidden xl:table-cell cursor-pointer select-none" @click="toggleSort('manufacturer')">
              Fabricant <span v-if="sortCol === 'manufacturer'" class="text-xs">{{ sortDir === 'asc' ? '▲' : '▼' }}</span>
            </th>
            <th class="cursor-pointer select-none" @click="toggleSort('location_name')">
              Emplacement <span v-if="sortCol === 'location_name'" class="text-xs">{{ sortDir === 'asc' ? '▲' : '▼' }}</span>
            </th>
            <th class="hidden xl:table-cell cursor-pointer select-none" @click="toggleSort('location_floor')">
              Étage <span v-if="sortCol === 'location_floor'" class="text-xs">{{ sortDir === 'asc' ? '▲' : '▼' }}</span>
            </th>
            <th class="hidden md:table-cell">Admin</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="d in filteredDevices" :key="d.id">
            <td class="font-medium">
              <router-link :to="`/devices/${d.id}`" class="link link-hover">{{ capitalize(d.name) }}</router-link>
            </td>
            <td class="hidden md:table-cell">
              <span class="badge text-white border-0" :style="{ backgroundColor: typeColor(d.device_type) }">{{ typeLabel(d.device_type) }}</span>
            </td>
            <td class="hidden sm:table-cell font-mono text-sm">{{ d.ipv4 || '-' }}</td>
            <td class="hidden sm:table-cell text-sm">
              <span v-if="d.ip_type === 'static'" class="badge badge-outline badge-xs">Static</span>
              <span v-else-if="d.ip_type === 'dhcp'" class="badge badge-outline badge-xs">DHCP</span>
              <span v-else class="opacity-40">-</span>
            </td>
            <td class="hidden lg:table-cell font-mono text-sm">{{ d.mac || '-' }}</td>
            <td class="hidden xl:table-cell text-sm">{{ d.manufacturer || '-' }}</td>
            <td>{{ capitalize(d.location_name) || '-' }}</td>
            <td class="hidden xl:table-cell">{{ capitalize(d.location_floor) || '-' }}</td>
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
            <input v-model="form.ipv4" class="input input-bordered" placeholder="192.168.1.x" />
          </div>
          <div class="form-control mb-3">
            <label class="label"><span class="label-text">Adresse MAC</span></label>
            <input v-model="form.mac" class="input input-bordered" placeholder="XX:XX:XX:XX:XX:XX" />
          </div>
          <div class="form-control mb-3">
            <label class="label"><span class="label-text">Emplacement</span></label>
            <select v-model="form.location_id" class="select select-bordered">
              <option :value="null">- Aucun -</option>
              <option v-for="loc in locations" :key="loc.id" :value="loc.id">{{ capitalize(loc.name) }} ({{ loc.floor || '?' }})</option>
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

const devices = ref([])
const locations = ref([])
const deviceTypes = ref([])
const filterName = ref('')
const filterType = ref('')
const filterLocation = ref('')
const sortCol = ref('')
const sortDir = ref('asc')
const scanning = ref(false)
const enriching = ref(false)

const form = ref({
  name: '', device_type: 'computer', ipv4: '', mac: '', location_id: null, admin_url: '',
})

const filteredDevices = computed(() => {
  let list = devices.value.filter(d => {
    if (filterName.value && !d.name.toLowerCase().includes(filterName.value.toLowerCase())) return false
    if (filterType.value && d.device_type !== filterType.value) return false
    if (filterLocation.value && d.location_id !== Number(filterLocation.value)) return false
    return true
  })
  if (sortCol.value) {
    list = [...list].sort((a, b) => {
      const va = (a[sortCol.value] || '').toString().toLowerCase()
      const vb = (b[sortCol.value] || '').toString().toLowerCase()
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
    sortDir.value = 'asc'
  }
}

function capitalize(s) {
  return s ? s.charAt(0).toUpperCase() + s.slice(1) : ''
}

function typeColor(type) {
  const found = deviceTypes.value.find(dt => dt.type === type)
  return found ? found.color : '#6b7280'
}

function resolveAdminUrl(d) {
  if (!d.admin_url) return null
  if (!d.ipv4) return d.admin_url
  return d.admin_url.replace(/\{ip\}/g, d.ipv4)
}

function typeLabel(type) {
  const found = deviceTypes.value.find(dt => dt.type === type)
  return found ? found.label : type
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

async function addDevice() {
  await axios.post('/api/devices', form.value)
  form.value = { name: '', device_type: 'computer', ipv4: '', mac: '', location_id: null, admin_url: '' }
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
    const { data } = await axios.post('/api/scan')
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
})
</script>