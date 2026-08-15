<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">Cartographie</h1>
      <button class="btn btn-outline btn-sm" @click="refreshGraph">
        <RefreshCw :size="16" :stroke-width="2" />
        Actualiser
      </button>
    </div>

    <div class="flex gap-2 mb-2 flex-wrap items-center text-sm">
      <span class="text-xs opacity-50 mr-1">Types :</span>
      <button v-for="dt in deviceTypes" :key="dt.type"
        class="btn btn-xs gap-1"
        :class="hiddenTypes.includes(dt.type) ? 'btn-outline opacity-40' : 'btn-ghost'"
        @click="toggleType(dt.type)">
        <span class="w-3 h-3 rounded-sm" :style="{ background: dt.color }"></span>
        <img :src="iconDataUrl(dt.icon, '#94a3b8')" class="w-4 h-4" />
        {{ dt.label }}
      </button>
    </div>

    <div v-if="networks.length > 0" class="flex gap-2 mb-4 flex-wrap items-center text-sm">
      <span class="text-xs opacity-50 mr-1">Réseaux :</span>
      <button v-for="net in networks" :key="net.id"
        class="btn btn-xs gap-1"
        :class="hiddenNetworks.includes(net.id) ? 'btn-outline opacity-40' : 'btn-ghost'"
        @click="toggleNetwork(net.id)">
        <span class="w-3 h-3 rounded-sm" :style="{ background: net.color || '#94a3b8' }"></span>
        {{ net.name }}
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
import { iconDataUrl } from '../icons.js'

cytoscape.use(fcose)

const router = useRouter()
let cy = null

const deviceTypes = ref([])
const hiddenTypes = ref([])
const networks = ref([])
const hiddenNetworks = ref([])

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

  const ORPHAN_GROUP_ID = 'virt-orphans'
  const hasOrphans = data.nodes.some(n => !(n.location && n.location_id) && !n.floor)
  if (hasOrphans) {
    elements.push({
      data: {
        id: ORPHAN_GROUP_ID,
        label: 'Sans emplacement',
        color: '#64748b',
      },
      classes: 'virtual',
    })
  }

  for (const n of data.nodes) {
    let parent = undefined
    if (n.location && n.location_id) {
      parent = `loc-${n.location_id}`
    } else if (n.floor) {
      parent = `floor-${n.floor}`
    } else if (hasOrphans) {
      parent = ORPHAN_GROUP_ID
    }
    elements.push({
      data: {
        id: `dev-${n.id}`,
        label: n.label,
        type: n.group || 'other',
        parent: parent,
        network_ids: n.network_ids || [],
      },
    })
  }

  for (const e of data.edges) {
    const edgeColor = e.color?.color || '#94a3b8'
    elements.push({
      data: {
        id: `edge-${e.from}-${e.to}-${e.network_id || ''}`,
        source: `dev-${e.from}`,
        target: `dev-${e.to}`,
        label: e.label,
        color: edgeColor,
        network_id: e.network_id,
      },
      classes: e.edge_type,
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
          'padding': '40px',
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
          'padding': '16px',
          'shape': 'round-rectangle',
          'compound-sizing-wrt-labels': 'include',
          'min-width': '120px',
          'min-height': '100px',
        },
      },
      {
        selector: 'node.virtual',
        style: {
          label: 'data(label)',
          'background-color': 'data(color)',
          'background-opacity': 0.008,
          'border-color': 'data(color)',
          'border-width': 1,
          'border-style': 'dashed',
          'border-opacity': 0.18,
          'text-valign': 'top',
          'text-halign': 'center',
          'font-size': '11px',
          'font-style': 'italic',
          'text-opacity': 0.3,
          color: 'data(color)',
          'padding': '14px',
          'shape': 'round-rectangle',
          'compound-sizing-wrt-labels': 'include',
          'min-width': '100px',
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
          'target-arrow-shape': 'none',
          'curve-style': 'unbundled-bezier',
          'control-point-distances': (el) => {
            const id = el.data('id') || ''
            const sum = id.split('').reduce((a, c) => a + c.charCodeAt(0), 0)
            return (sum % 2 === 0 ? 1 : -1) * (20 + (Math.abs(sum) % 4) * 15)
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
        selector: 'edge.backbone',
        style: {
          'line-style': 'dashed',
          'line-dash-pattern': [10, 8],
        },
      },
      {
        selector: 'edge.wifi',
        style: {
          'line-style': 'dashed',
          'line-dash-pattern': [3, 18],
        },
      },
      {
        selector: 'edge.wireless',
        style: {
          'line-style': 'dashed',
          'line-dash-pattern': [3, 18],
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
    nestingFactor: 1.5,
    gravity: 0.25,
    gravityCompound: 2.0,
    gravityRangeCompound: 2.0,
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

    removeOverlaps()
    arrangeFloorsVertically()
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

function toggleNetwork(netId) {
  const idx = hiddenNetworks.value.indexOf(netId)
  if (idx >= 0) {
    hiddenNetworks.value.splice(idx, 1)
  } else {
    hiddenNetworks.value.push(netId)
  }
  applyVisibility()
}

function applyVisibility() {
  if (!cy) return

  const hiddenNet = hiddenNetworks.value

  cy.nodes('node:childless').forEach(node => {
    let visible = true
    const type = node.data('type')
    if (hiddenTypes.value.includes(type)) {
      visible = false
    }
    if (visible && hiddenNet.length > 0) {
      const netIds = node.data('network_ids') || []
      if (netIds.length > 0) {
        const anyVisible = netIds.some(nid => !hiddenNet.includes(nid))
        if (!anyVisible) visible = false
      }
    }
    node.style('display', visible ? 'element' : 'none')
  })

  cy.edges().forEach(edge => {
    const src = edge.source().id()
    const tgt = edge.target().id()
    const srcHidden = cy.getElementById(src).style('display') === 'none'
    const tgtHidden = cy.getElementById(tgt).style('display') === 'none'
    let visible = !srcHidden && !tgtHidden
    if (visible && hiddenNet.length > 0) {
      const netId = edge.data('network_id')
      if (netId && hiddenNet.includes(netId)) {
        visible = false
      }
    }
    edge.style('display', visible ? 'element' : 'none')
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
  cy.nodes('node.virtual').forEach(vg => {
    vg.style('display', hasVisibleChild(vg) ? 'element' : 'none')
  })
}

function removeOverlaps() {
  for (let pass = 0; pass < 5; pass++) {
    let moved = false
    const locs = cy.nodes('node.location')
    for (let i = 0; i < locs.length; i++) {
      for (let j = i + 1; j < locs.length; j++) {
        const a = locs[i], b = locs[j]
        if (a.parent().id() !== b.parent().id()) continue
        if (a.style('display') === 'none' || b.style('display') === 'none') continue

        const bbA = a.boundingBox(), bbB = b.boundingBox()
        const overlapX = Math.max(0, Math.min(bbA.x2, bbB.x2) - Math.max(bbA.x1, bbB.x1))
        const overlapY = Math.max(0, Math.min(bbA.y2, bbB.y2) - Math.max(bbA.y1, bbB.y1))

        if (overlapX > 0 && overlapY > 0) {
          const cxA = (bbA.x1 + bbA.x2) / 2
          const cyA = (bbA.y1 + bbA.y2) / 2
          const cxB = (bbB.x1 + bbB.x2) / 2
          const cyB = (bbB.y1 + bbB.y2) / 2
          const dx = cxB - cxA, dy = cyB - cyA
          const dist = Math.sqrt(dx * dx + dy * dy)
          const gap = 20
          if (dist < 1) {
            b.position({ x: cxA + 100, y: cyA })
          } else {
            b.position({ x: cxB + (overlapX + gap) * (dx / dist), y: cyB + (overlapY + gap) * (dy / dist) })
          }
          moved = true
        }
      }
    }
    if (!moved) break
  }
}

function arrangeFloorsVertically() {
  const floorNodes = cy.nodes('node.floor')
  if (floorNodes.length < 2) return

  const floorRank = (id) => {
    const f = id.replace('floor-', '')
    const m = f.match(/^R?\+?(\d+)$/i)
    if (m) return parseInt(m[1])
    if (f.toUpperCase() === 'RDC') return 0
    return 999
  }

  const sorted = floorNodes.sort((a, b) => floorRank(a.id()) - floorRank(b.id()))

  const clusterBB = cy.nodes('node.floor').boundingBox()
  const clusterCenterY = (clusterBB.y1 + clusterBB.y2) / 2
  const spacing = 100

  const heights = sorted.map(f => f.boundingBox().y2 - f.boundingBox().y1)
  const totalTargetHeight = heights.reduce((s, h) => s + h, 0) + spacing * (sorted.length - 1)
  let y = clusterCenterY - totalTargetHeight / 2

  for (let i = sorted.length - 1; i >= 0; i--) {
    const f = sorted[i]
    const bb = f.boundingBox()
    const h = bb.y2 - bb.y1
    const targetCenterY = y + h / 2
    const currentCenterY = (bb.y1 + bb.y2) / 2
    const deltaY = targetCenterY - currentCenterY

    f.descendants().filter(n => n.isChildless()).forEach(n => {
      const pos = n.position()
      n.position({ x: pos.x, y: pos.y + deltaY })
    })
    y += h + spacing
  }
}

async function refreshGraph() {
  const [{ data }, dtRes, netRes] = await Promise.all([
    axios.get('/api/graph'),
    axios.get('/api/device-types'),
    axios.get('/api/networks'),
  ])
  deviceTypes.value = dtRes.data
  networks.value = netRes.data
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
