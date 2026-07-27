<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">Cartographie</h1>
      <button class="btn btn-outline btn-sm" @click="refreshGraph">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
        Actualiser
      </button>
    </div>

    <div class="flex gap-2 mb-4 flex-wrap items-center text-sm">
      <span class="flex items-center gap-1"><span class="w-3 h-3 rounded-sm" style="background:#3b82f6"></span> Routeur</span>
      <span class="flex items-center gap-1"><span class="w-3 h-3 rounded-sm" style="background:#8b5cf6"></span> Modem</span>
      <span class="flex items-center gap-1"><span class="w-3 h-3 rounded-sm" style="background:#06b6d4"></span> AP</span>
      <span class="flex items-center gap-1"><span class="w-3 h-3 rounded-sm" style="background:#f59e0b"></span> Switch</span>
      <span class="flex items-center gap-1"><span class="w-3 h-3 rounded-sm" style="background:#10b981"></span> Ordinateur</span>
      <span class="flex items-center gap-1"><span class="w-3 h-3 rounded-sm" style="background:#ef4444"></span> Serveur</span>
      <span class="flex items-center gap-1"><span class="w-3 h-3 rounded-sm" style="background:#ec4899"></span> IoT</span>
    </div>

    <div id="graph-container"></div>
  </div>
</template>

<script setup>
import { onMounted, onBeforeUnmount } from 'vue'
import cytoscape from 'cytoscape'
import fcose from 'cytoscape-fcose'
import axios from 'axios'

cytoscape.use(fcose)

let cy = null

const typeColors = {
  router: '#3b82f6', modem: '#8b5cf6', ap: '#06b6d4',
  switch: '#f59e0b', computer: '#10b981', server: '#ef4444',
  iot: '#ec4899', other: '#6b7280',
}

const locationColorPalette = [
  '#6366f1', '#a855f7', '#ec4899', '#f43f5e', '#f97316',
  '#eab308', '#84cc16', '#22c55e', '#14b8a6', '#06b6d4',
  '#0ea5e9', '#3b82f6',
]

function buildGraph(data) {
  const container = document.getElementById('graph-container')

  const locIndex = {}
  let idx = 0
  for (const n of data.nodes) {
    if (n.location && !(n.location in locIndex)) {
      locIndex[n.location] = idx++
    }
  }

  const locColors = {}
  for (const loc of Object.keys(locIndex)) {
    locColors[loc] = locationColorPalette[locIndex[loc] % locationColorPalette.length]
  }

  const elements = []

  for (const loc of Object.keys(locIndex)) {
    const color = locColors[loc]
    elements.push({
      data: {
        id: `loc-${loc}`,
        label: loc,
        color: color,
      },
      classes: 'location',
    })
  }

  for (const n of data.nodes) {
    elements.push({
      data: {
        id: `dev-${n.id}`,
        label: n.label,
        type: n.group || 'other',
        parent: n.location ? `loc-${n.location}` : undefined,
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
    elements,
    style: [
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
          'min-width': '80px',
          'min-height': '60px',
        },
      },
      {
        selector: 'node:childless',
        style: {
          label: 'data(label)',
          'background-color': (el) => typeColors[el.data('type')] || typeColors.other,
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
          'curve-style': 'bezier',
          'control-point-step-size': 40,
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
    layout: {
      name: 'fcose',
      animate: false,
      nodeRepulsion: 4500,
      idealEdgeLength: 100,
      edgeElasticity: 0.45,
      nestingFactor: 1.8,
      gravity: 0.25,
      gravityCompound: 1.5,
      gravityRangeCompound: 1.5,
      numIter: 2500,
      tile: true,
      packComponents: true,
    },
    zoomingEnabled: true,
    userZoomingEnabled: true,
    panningEnabled: true,
    userPanningEnabled: true,
    boxSelectionEnabled: false,
    autoungrabify: false,
    autounselectify: true,
  })
}

async function refreshGraph() {
  const { data } = await axios.get('/api/graph')
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
