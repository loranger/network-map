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
      <span class="flex items-center gap-1"><span class="badge badge-info w-3 h-3 p-0"></span> Routeur</span>
      <span class="flex items-center gap-1"><span class="badge badge-secondary w-3 h-3 p-0"></span> Modem</span>
      <span class="flex items-center gap-1"><span class="badge badge-accent w-3 h-3 p-0"></span> AP</span>
      <span class="flex items-center gap-1"><span class="badge badge-warning w-3 h-3 p-0"></span> Switch</span>
      <span class="flex items-center gap-1"><span class="badge badge-success w-3 h-3 p-0"></span> Ordinateur</span>
      <span class="flex items-center gap-1"><span class="badge badge-error w-3 h-3 p-0"></span> Serveur</span>
      <span class="flex items-center gap-1"><span class="badge badge-ghost w-3 h-3 p-0"></span> IoT</span>
      <span class="flex-1"></span>
      <span v-for="(color, loc) in locationColors" :key="loc" class="flex items-center gap-1">
        <span class="w-3 h-3 rounded-sm" :style="{ background: color }"></span> {{ capitalize(loc) }}
      </span>
    </div>

    <div id="graph-container"></div>
  </div>
</template>

<script setup>
import { onMounted, onBeforeUnmount, ref } from 'vue'

function capitalize(s) {
  return s ? s.charAt(0).toUpperCase() + s.slice(1) : ''
}
import { Network } from 'vis-network'
import { DataSet } from 'vis-data'
import axios from 'axios'

let network = null
let nodeLocations = []

const typeColors = {
  router: { background: '#3b82f6', border: '#2563eb' },
  modem: { background: '#8b5cf6', border: '#7c3aed' },
  ap: { background: '#06b6d4', border: '#0891b2' },
  switch: { background: '#f59e0b', border: '#d97706' },
  computer: { background: '#10b981', border: '#059669' },
  server: { background: '#ef4444', border: '#dc2626' },
  iot: { background: '#ec4899', border: '#db2777' },
  other: { background: '#6b7280', border: '#4b5563' },
}

const locationColorPalette = [
  '#6366f1', '#a855f7', '#ec4899', '#f43f5e', '#f97316',
  '#eab308', '#84cc16', '#22c55e', '#14b8a6', '#06b6d4',
  '#0ea5e9', '#3b82f6',
]

const locationColors = ref({})

function drawLocationZones(ctx) {
  if (!network || nodeLocations.length === 0) return

  const positions = network.getPositions()
  const groups = {}
  for (const n of nodeLocations) {
    const pos = positions[n.id]
    if (!pos) continue
    if (!groups[n.location]) groups[n.location] = { nodes: [], color: n.color }
    groups[n.location].nodes.push(pos)
  }

  for (const [loc, group] of Object.entries(groups)) {
    if (group.nodes.length < 2) continue
    const padX = 30
    const padY = 20
    const xs = group.nodes.map(p => p.x)
    const ys = group.nodes.map(p => p.y)
    const minX = Math.min(...xs) - padX
    const maxX = Math.max(...xs) + padX
    const minY = Math.min(...ys) - padY
    const maxY = Math.max(...ys) + padY

    ctx.beginPath()
    ctx.moveTo(minX + 12, minY)
    ctx.lineTo(maxX - 12, minY)
    ctx.quadraticCurveTo(maxX, minY, maxX, minY + 12)
    ctx.lineTo(maxX, maxY - 12)
    ctx.quadraticCurveTo(maxX, maxY, maxX - 12, maxY)
    ctx.lineTo(minX + 12, maxY)
    ctx.quadraticCurveTo(minX, maxY, minX, maxY - 12)
    ctx.lineTo(minX, minY + 12)
    ctx.quadraticCurveTo(minX, minY, minX + 12, minY)
    ctx.closePath()

    const r = parseInt(group.color.slice(1, 3), 16)
    const g = parseInt(group.color.slice(3, 5), 16)
    const b = parseInt(group.color.slice(5, 7), 16)
    ctx.fillStyle = `rgba(${r},${g},${b},0.08)`
    ctx.fill()
    ctx.strokeStyle = group.color
    ctx.lineWidth = 1.5
    ctx.setLineDash([])
    ctx.stroke()

    ctx.fillStyle = group.color
    ctx.font = 'bold 11px sans-serif'
    ctx.textAlign = 'left'
    ctx.textBaseline = 'top'
    ctx.fillText(capitalize(loc), minX + 8, minY + 4)
  }
}

function buildGraph(data) {
  const container = document.getElementById('graph-container')

  const locIndex = {}
  let idx = 0
  const colors = {}
  for (const n of data.nodes) {
    if (n.location && !(n.location in locIndex)) {
      locIndex[n.location] = idx++
      colors[n.location] = locationColorPalette[locIndex[n.location] % locationColorPalette.length]
    }
  }
  locationColors.value = colors

  nodeLocations = data.nodes.filter(n => n.location).map(n => ({
    id: n.id,
    location: n.location,
    color: colors[n.location],
  }))

  const hubNodes = []
  const hubEdges = []
  for (const [loc, color] of Object.entries(colors)) {
    const hubId = `_hub:${loc}`
    hubNodes.push({
      id: hubId,
      hidden: true,
      shape: 'dot',
      size: 1,
    })
    for (const n of data.nodes) {
      if (n.location === loc) {
        hubEdges.push({
          from: hubId,
          to: n.id,
          color: { color: 'rgba(0,0,0,0)' },
          width: 3,
          smooth: { type: 'straightCross' },
        })
      }
    }
  }

  const allNodesData = [...data.nodes.map(n => ({
    id: n.id,
    label: capitalize(n.label),
    title: n.title,
    color: {
      background: typeColors[n.group]?.background || '#6b7280',
      border: n.location ? colors[n.location] : typeColors[n.group]?.border || '#4b5563',
    },
    shape: 'box',
    font: { color: '#fff', size: 14 },
    borderWidth: n.location ? 3 : 2,
    borderWidthSelected: 4,
    shadow: { enabled: true, size: 4 },
  }))]

  const nodes = new DataSet([...allNodesData, ...hubNodes])
  const allEdgesData = [...data.edges.map(e => ({
    from: e.from,
    to: e.to,
    label: e.label,
    dashes: e.dashes,
    color: { color: e.color?.color || '#64748b', highlight: '#94a3b8' },
    font: { size: 11, color: '#94a3b8', strokeWidth: 0 },
    width: 2,
    smooth: { type: 'curvedCW', roundness: 0.15 },
  })), ...hubEdges]

  const edges = new DataSet(allEdgesData)

  const options = {
    physics: {
      solver: 'forceAtlas2Based',
      forceAtlas2Based: {
        gravitationalConstant: -40,
        centralGravity: 0.003,
        springLength: 140,
        springConstant: 0.04,
        damping: 0.4,
      },
      stabilization: { iterations: 300 },
    },
    layout: { improvedLayout: true },
    interaction: {
      hover: true,
      tooltipDelay: 100,
      zoomView: true,
      dragView: true,
    },
    edges: {
      arrows: { to: { enabled: true, scaleFactor: 0.8 } },
    },
  }

  network = new Network(container, { nodes, edges }, options)
  network.on('beforeDrawing', drawLocationZones)
}

async function refreshGraph() {
  const { data } = await axios.get('/api/graph')
  if (network) {
    network.destroy()
    network = null
  }
  buildGraph(data)
}

function handleResize() {
  if (network) network.redraw()
}

onMounted(() => {
  refreshGraph()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  if (network) {
    network.destroy()
    network = null
  }
  window.removeEventListener('resize', handleResize)
})
</script>
