import { createRouter, createWebHistory } from 'vue-router';
import Home from '../components/Home.vue';
import AdminPanel from '../components/AdminPanel.vue';

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home,
  },
  {
    path: '/admin',
    name: 'Admin',
    component: AdminPanel,
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
