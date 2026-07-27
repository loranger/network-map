<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">Cartographie</h1>
      <button class="btn btn-outline btn-sm" @click="refreshGraph">
        <RefreshCw :size="16" :stroke-width="2" />
        Actualiser
      </button>
    </div>

    <div class="flex gap-2 mb-4 flex-wrap items-center text-sm">
      <button v-for="dt in deviceTypes" :key="dt.type"
        class="btn btn-xs gap-1"
        :class="hiddenTypes.includes(dt.type) ? 'btn-outline opacity-40' : 'btn-ghost'"
        @click="toggleType(dt.type)">
        <span class="w-3 h-3 rounded-sm" :style="{ background: dt.color }"></span>
        {{ dt.label }}
      </button>
    </div>

    <div id="graph-container"></div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import cytoscape from 'cytoscape'
import fcose from 'cytoscape-fcose'
import axios from 'axios'
import { RefreshCw } from '@lucide/vue'

cytoscape.use(fcose)

const router = useRouter()
let cy = null

const deviceTypes = ref([])
const hiddenTypes = ref([])

const typeColors = computed(() => {
  const map = {}
  for (const dt of deviceTypes.value) {
    map[dt.type] = dt.color
  }
  return map
})

const locationColorPalette = [
  '#6366f1', '#a855f7', '#ec4899', '#f43f5e', '#f97316',
  '#eab308', '#84cc16', '#22c55e', '#14b8a6', '#06b6d4',
  '#0ea5e9', '#3b82f6',
]

const floorColorPalette = [
  '#334155', '#475569', '#64748b',
]

function buildGraph(data) {
  const container = document.getElementById('graph-container')

  const floorSet = new Set()
  const locIndex = {}
  let idx = 0
  for (const n of data.nodes) {
    if (n.floor) floorSet.add(n.floor)
    const locKey = n.location_id ? `loc-${n.location_id}` : null
    if (n.location && locKey && !(locKey in locIndex)) {
      locIndex[locKey] = { name: n.location, sample: n }
    }
  }

  const locColors = {}
  for (const [key, val] of Object.entries(locIndex)) {
    locColors[key] = locationColorPalette[
      (Object.keys(locIndex).indexOf(key)) % locationColorPalette.length
    ]
  }

  const floors = [...floorSet].sort()
  const floorColors = {}
  floors.forEach((f, i) => {
    floorColors[f] = floorColorPalette[i % floorColorPalette.length]
  })

  const elements = []

  for (const floor of floors) {
    elements.push({
      data: {
        id: `floor-${floor}`,
        label: `Étage ${floor}`,
        color: floorColors[floor],
      },
      classes: 'floor',
    })
  }

  for (const [locKey, val] of Object.entries(locIndex)) {
    const parentFloor = val.sample?.floor ? `floor-${val.sample.floor}` : undefined
    const color = locColors[locKey]
    elements.push({
      data: {
        id: locKey,
        label: val.name,
        color: color,
        parent: parentFloor,
      },
      classes: 'location',
    })
  }

  for (const n of data.nodes) {
    let parent = undefined
    if (n.location && n.location_id) {
      parent = `loc-${n.location_id}`
    } else if (n.floor) {
      parent = `floor-${n.floor}`
    }
    elements.push({
      data: {
        id: `dev-${n.id}`,
        label: n.label,
        type: n.group || 'other',
        parent: parent,
      },
    })
  }

  for (const e of data.edges) {
    const edgeColor = e.color?.color || '#94a3b8'
    elements.push({
      data: {
        id: `edge-${e.from}-${e.to}`,
        source: `dev-${e.from}`,
        target: `dev-${e.to}`,
        label: e.label,
        color: edgeColor,
      },
      classes: e.dashes ? 'wireless' : undefined,
    })
  }

  cy = cytoscape({
    container,
    style: [
      {
        selector: 'node.floor',
        style: {
          label: 'data(label)',
          'background-color': 'data(color)',
          'background-opacity': 0.08,
          'border-color': 'data(color)',
          'border-width': 1,
          'border-style': 'dashed',
          'text-valign': 'top',
          'text-halign': 'center',
          'font-weight': 'bold',
          'font-size': '14px',
          color: 'data(color)',
          'padding': '60px',
          'shape': 'round-rectangle',
          'compound-sizing-wrt-labels': 'include',
          'min-width': '120px',
          'min-height': '80px',
        },
      },
      {
        selector: 'node.location',
        style: {
          label: 'data(label)',
          'background-color': 'data(color)',
          'background-opacity': 0.12,
          'border-color': 'data(color)',
          'border-width': 2,
          'border-style': 'solid',
          'text-valign': 'top',
          'text-halign': 'center',
          'font-weight': 'bold',
          'font-size': '13px',
          color: 'data(color)',
          'padding': '24px',
          'shape': 'round-rectangle',
          'compound-sizing-wrt-labels': 'include',
          'min-width': '80px',
          'min-height': '60px',
        },
      },
      {
        selector: 'node:childless',
        style: {
          label: 'data(label)',
          'background-color': (el) => typeColors.value[el.data('type')] || '#6b7280',
          'border-color': (el) => {
            const parent = el.parent()
            return parent.length ? parent.data('color') : '#4b5563'
          },
          'border-width': 3,
          color: '#fff',
          'font-size': '12px',
          'text-valign': 'center',
          'text-halign': 'center',
          width: 'label',
          height: 'label',
          padding: '8px',
          shape: 'round-rectangle',
        },
      },
      {
        selector: 'edge',
        style: {
          width: 2.5,
          'line-color': (el) => el.data('color'),
          'target-arrow-color': (el) => el.data('color'),
          'target-arrow-shape': 'triangle',
          'arrow-scale': 1,
          'curve-style': 'unbundled-bezier',
          'control-point-distances': (el) => {
            const sum = el.data('source').split('').reduce((a, c) => a + c.charCodeAt(0), 0) +
                        el.data('target').split('').reduce((a, c) => a + c.charCodeAt(0), 0)
            return sum % 2 === 0 ? 25 : -25
          },
          'control-point-weights': 0.5,
          label: (el) => el.data('label'),
          'font-size': '10px',
          color: '#94a3b8',
          'text-background-color': '#1e293b',
          'text-background-opacity': 0.7,
          'text-background-padding': '3px',
          'text-margin-y': '-6px',
        },
      },
      {
        selector: 'edge.wireless',
        style: {
          'line-style': 'dashed',
        },
      },
    ],
    zoomingEnabled: true,
    userZoomingEnabled: true,
    panningEnabled: true,
    userPanningEnabled: true,
    boxSelectionEnabled: false,
    autoungrabify: false,
    autounselectify: true,
  })

  cy.add(elements)

  const layout = cy.layout({
    name: 'fcose',
    animate: false,
    nodeRepulsion: 8000,
    idealEdgeLength: 120,
    edgeElasticity: 0.45,
    nestingFactor: 0.8,
    gravity: 0.25,
    gravityCompound: 2.5,
    gravityRangeCompound: 3.0,
    numIter: 2500,
    tile: true,
    packComponents: true,
  })

  layout.one('layoutstop', () => {
    cy.fit(undefined, 50)
    cy.center()

    cy.on('mouseover', 'node:childless', () => {
      cy.container().style.cursor = 'pointer'
    })
    cy.on('mouseout', 'node:childless', () => {
      cy.container().style.cursor = 'default'
    })

    cy.on('dblclick', 'node:childless', (evt) => {
      const nodeId = evt.target.id()
      const deviceId = nodeId.replace('dev-', '')
      router.push(`/devices/${deviceId}`)
    })

    applyVisibility()
  })

  layout.run()
}

function toggleType(type) {
  const idx = hiddenTypes.value.indexOf(type)
  if (idx >= 0) {
    hiddenTypes.value.splice(idx, 1)
  } else {
    hiddenTypes.value.push(type)
  }
  applyVisibility()
}

function applyVisibility() {
  if (!cy) return
  const allTypes = deviceTypes.value.map(dt => dt.type)
  for (const t of allTypes) {
    const visible = !hiddenTypes.value.includes(t)
    cy.nodes(`node:childless[type = "${t}"]`).style('display', visible ? 'element' : 'none')
  }
  const visibleNodes = cy.nodes('node:childless').filter(n => n.style('display') !== 'none')
  const visibleIds = new Set(visibleNodes.map(n => n.id()))
  cy.edges().forEach(edge => {
    const src = edge.source().id()
    const tgt = edge.target().id()
    edge.style('display', visibleIds.has(src) && visibleIds.has(tgt) ? 'element' : 'none')
  })

  const hasVisibleChild = node => {
    if (!node.isParent()) return node.style('display') !== 'none'
    return node.children().some(c => hasVisibleChild(c))
  }

  cy.nodes('node.location').forEach(loc => {
    loc.style('display', hasVisibleChild(loc) ? 'element' : 'none')
  })
  cy.nodes('node.floor').forEach(floor => {
    floor.style('display', hasVisibleChild(floor) ? 'element' : 'none')
  })
}

async function refreshGraph() {
  const [{ data }, dtRes] = await Promise.all([
    axios.get('/api/graph'),
    axios.get('/api/device-types'),
  ])
  deviceTypes.value = dtRes.data
  if (cy) {
    cy.destroy()
    cy = null
  }
  buildGraph(data)
}

function handleResize() {
  if (cy) cy.resize()
}

onMounted(() => {
  refreshGraph()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  if (cy) {
    cy.destroy()
    cy = null
  }
  window.removeEventListener('resize', handleResize)
})
</script>
