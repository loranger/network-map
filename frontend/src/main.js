import { createApp } from 'vue'
import { createRouter, createWebHashHistory } from 'vue-router'
import App from './App.vue'
import Devices from './views/Devices.vue'
import DeviceDetail from './views/DeviceDetail.vue'
import Graph from './views/Graph.vue'
import Networks from './views/Networks.vue'
import Locations from './views/Locations.vue'
import Floors from './views/Floors.vue'
import DeviceTypes from './views/DeviceTypes.vue'
import Access from './views/Access.vue'
import './style.css'

const routes = [
  { path: '/', redirect: '/devices' },
  { path: '/devices', component: Devices },
  { path: '/devices/:id', component: DeviceDetail },
  { path: '/graph', component: Graph },
  { path: '/networks', component: Networks },
  { path: '/locations', component: Locations },
  { path: '/floors', component: Floors },
  { path: '/device-types', component: DeviceTypes },
  { path: '/access', component: Access },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

createApp(App).use(router).mount('#app')
