<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">Périphériques</h1>
      <div class="flex gap-2">
        <button class="btn btn-outline" @click="scanNetwork" :disabled="scanning">
          <svg v-if="!scanning" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          <span v-else class="loading loading-spinner"></span>
          Scanner
        </button>
        <button class="btn btn-outline" onclick="import_arp_modal.showModal()">
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          Importer ARP
        </button>
        <button class="btn btn-outline" @click="enrichDevices" :disabled="enriching">
          <svg v-if="!enriching" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
          <span v-else class="loading loading-spinner"></span>
          Enrichir
        </button>
        <button class="btn btn-primary" onclick="add_modal.showModal()">
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          Ajouter
        </button>
      </div>
    </div>

    <div class="flex gap-2 mb-4 flex-wrap">
      <input v-model="filterName" type="search" placeholder="Rechercher…" class="input input-bordered input-sm flex-1 min-w-[160px]" />
      <select class="select select-bordered select-sm" v-model="filterType">
        <option value="">Tous les types</option>
        <option value="router">Routeur</option>
        <option value="modem">Modem</option>
        <option value="ap">Point d'accès</option>
        <option value="switch">Switch</option>
        <option value="computer">Ordinateur</option>
        <option value="server">Serveur</option>
        <option value="iot">IoT</option>
        <option value="other">Autre</option>
      </select>
      <select class="select select-bordered select-sm" v-model="filterLocation">
        <option value="">Tous les emplacements</option>
        <option v-for="loc in locations" :key="loc" :value="loc">{{ capitalize(loc) }}</option>
      </select>
    </div>

    <div class="overflow-x-auto">
      <table class="table table-zebra">
        <thead>
          <tr>
            <th>Nom</th>
            <th class="hidden md:table-cell">Type</th>
            <th class="hidden sm:table-cell">IP</th>
            <th class="hidden sm:table-cell">Type IP</th>
            <th class="hidden lg:table-cell">MAC</th>
            <th class="hidden xl:table-cell">Fabricant</th>
            <th>Emplacement</th>
            <th class="hidden xl:table-cell">Étage</th>
            <th class="hidden md:table-cell">Découvert</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="d in filteredDevices" :key="d.id">
            <td class="font-medium">
              <router-link :to="`/devices/${d.id}`" class="link link-hover">{{ capitalize(d.name) }}</router-link>
            </td>
            <td class="hidden md:table-cell">
              <span class="badge" :class="badgeClass(d.device_type)">{{ capitalize(d.device_type) }}</span>
            </td>
            <td class="hidden sm:table-cell font-mono text-sm">{{ d.ipv4 || '-' }}</td>
            <td class="hidden sm:table-cell text-sm">
              <span v-if="d.ip_type === 'static'" class="badge badge-outline badge-xs">Static</span>
              <span v-else-if="d.ip_type === 'dhcp'" class="badge badge-outline badge-xs">DHCP</span>
              <span v-else class="opacity-40">-</span>
            </td>
            <td class="hidden lg:table-cell font-mono text-sm">{{ d.mac || '-' }}</td>
            <td class="hidden xl:table-cell text-sm">{{ d.manufacturer || '-' }}</td>
            <td>{{ capitalize(d.location) || '-' }}</td>
            <td class="hidden xl:table-cell">{{ capitalize(d.floor) || '-' }}</td>
            <td class="hidden md:table-cell">
              <span v-if="d.discovered" class="text-success">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
              </span>
              <span v-else class="text-warning">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
              </span>
            </td>
            <td>
              <button class="btn btn-ghost btn-xs" @click="deleteDevice(d.id)">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
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
            <label class="label"><span class="label-text">Adresse IP</span></label>
            <input v-model="form.ipv4" class="input input-bordered" placeholder="192.168.1.x" />
          </div>
          <div class="form-control mb-3">
            <label class="label"><span class="label-text">Adresse MAC</span></label>
            <input v-model="form.mac" class="input input-bordered" placeholder="XX:XX:XX:XX:XX:XX" />
          </div>
          <div class="form-control mb-3">
            <label class="label"><span class="label-text">Étage</span></label>
            <input v-model="form.floor" class="input input-bordered" placeholder="ex: RDC, 1er..." />
          </div>
          <div class="form-control mb-3">
            <label class="label"><span class="label-text">Emplacement</span></label>
            <input v-model="form.location" class="input input-bordered" placeholder="ex: garage, bureau..." />
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

const devices = ref([])
const filterName = ref('')
const filterType = ref('')
const filterLocation = ref('')
const scanning = ref(false)
const enriching = ref(false)

const form = ref({
  name: '', device_type: 'computer', ipv4: '', mac: '', floor: '', location: '',
})

const locations = computed(() => {
  const locs = [...new Set(devices.value.map(d => d.location).filter(Boolean))]
  return locs.sort()
})

const filteredDevices = computed(() => {
  return devices.value.filter(d => {
    if (filterName.value && !d.name.toLowerCase().includes(filterName.value.toLowerCase())) return false
    if (filterType.value && d.device_type !== filterType.value) return false
    if (filterLocation.value && d.location !== filterLocation.value) return false
    return true
  })
})

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

async function fetchDevices() {
  const { data } = await axios.get('/api/devices')
  devices.value = data
}

async function addDevice() {
  await axios.post('/api/devices', form.value)
  form.value = { name: '', device_type: 'computer', ipv4: '', mac: '', floor: '', location: '' }
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

onMounted(fetchDevices)
</script>
