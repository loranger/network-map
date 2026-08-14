<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">Accès</h1>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 max-w-4xl">
      <div class="card bg-base-200">
        <div class="card-body">
          <div class="flex items-center gap-3">
            <span class="w-8 h-8 rounded flex items-center justify-center bg-indigo-500/20 text-indigo-500">
              <ShieldKeyhole :size="20" :stroke-width="2" />
            </span>
            <div>
              <h2 class="card-title">Freebox</h2>
              <div class="text-sm opacity-60">Table DHCP du LAN (hostnames)</div>
            </div>
            <span v-if="access?.configured" class="badge badge-success badge-sm ml-auto">Connecté</span>
            <span v-else class="badge badge-warning badge-sm ml-auto">Non configurée</span>
          </div>

          <div class="divider my-2"></div>

          <div v-if="pairing" class="form-control mb-3">
            <label class="label"><span class="label-text">URL de la Freebox</span></label>
            <input v-model="pairBaseUrl" class="input input-bordered" placeholder="http://192.168.1.254" />
          </div>

          <div v-if="pairingStatus === 'pending'" class="alert alert-info mb-3">
            <span class="loading loading-spinner loading-sm"></span>
            En attente de validation sur l'écran de la Freebox (confirmez avec le bouton central)…
          </div>
          <div v-else-if="pairingStatus === 'granted'" class="alert alert-success mb-3">
            Appairage réussi, jeton enregistré.
          </div>
          <div v-else-if="pairingStatus === 'denied'" class="alert alert-error mb-3">
            Autorisation refusée sur la Freebox.
          </div>
          <div v-else-if="pairingStatus === 'timeout'" class="alert alert-warning mb-3">
            Temps de validation écoulé.
          </div>

          <div v-if="!access?.configured" class="flex flex-wrap gap-2">
            <button class="btn btn-primary" @click="startPair" :disabled="pairing">
              <span v-if="pairing" class="loading loading-spinner loading-xs"></span>
              <span v-else>{{ pairing ? '' : 'Appairer' }}</span>
            </button>
            <button class="btn btn-outline" @click="showManual = !showManual">
              {{ showManual ? 'Masquer' : 'Jeton manuel' }}
            </button>
          </div>

          <div v-if="showManual && !access?.configured" class="mt-3">
            <div class="flex gap-2">
              <input v-model="manualToken" class="input input-bordered flex-1 font-mono" placeholder="Collez le jeton" />
              <button class="btn btn-outline" @click="saveManualToken">Enregistrer</button>
            </div>
          </div>

          <div v-if="access?.configured" class="flex gap-2">
            <button class="btn btn-error btn-outline" @click="revoke">Révoquer</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import axios from 'axios'
import { ShieldKeyhole } from '@lucide/vue'

const accesses = ref([])
const pairing = ref(false)
const pairBaseUrl = ref('http://192.168.1.254')
const pairingStatus = ref('')
const showManual = ref(false)
const manualToken = ref('')
let pollTimer = null

const access = computed(() => accesses.value.find(a => a.service === 'freebox'))

async function fetchAccesses() {
  const { data } = await axios.get('/api/access')
  accesses.value = data.accesses
  if (access.value?.base_url) pairBaseUrl.value = access.value.base_url
}

async function startPair() {
  pairing.value = true
  pairingStatus.value = ''
  await axios.post('/api/access/freebox/pair', { base_url: pairBaseUrl.value })
  pairingStatus.value = 'pending'
  pollTimer = setInterval(pollPairStatus, 2000)
}

async function pollPairStatus() {
  try {
    const { data } = await axios.get('/api/access/freebox/pair')
    pairingStatus.value = data.status
    if (data.status !== 'pending') {
      clearInterval(pollTimer)
      pairing.value = false
      await fetchAccesses()
    }
  } catch (e) {
    clearInterval(pollTimer)
    pairing.value = false
  }
}

async function saveManualToken() {
  if (!manualToken.value.trim()) return
  await axios.post('/api/access/freebox/token', { token: manualToken.value.trim() })
  manualToken.value = ''
  showManual.value = false
  await fetchAccesses()
}

async function revoke() {
  if (!confirm("Révoquer l'accès Freebox ?")) return
  await axios.delete('/api/access/freebox')
  await fetchAccesses()
}

onMounted(fetchAccesses)
onBeforeUnmount(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>
