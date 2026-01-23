import { createRouter, createWebHistory } from 'vue-router'
import PatientsListPage from '@/pages/PatientsListPage.vue'
import PatientDetailPage from '@/pages/PatientDetailPage.vue'

const routes = [
  {
    path: '/',
    name: 'patients',
    component: PatientsListPage,
  },
  {
    path: '/patient/:id',
    name: 'patient',
    component: PatientDetailPage,
    props: true,
  },

  // опционально: если путь не найден — уходим на главную
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
