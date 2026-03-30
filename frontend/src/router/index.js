import { createRouter, createWebHistory } from 'vue-router';
import Home from '../components/Home.vue';
import AdminPanel from '../components/AdminPanel.vue';
import MatchRecords from '../components/MatchRecords.vue';
import Abilities from '../components/Abilities.vue';
import Ranking from '../components/Ranking.vue';
import WinLose from '../components/WinLose.vue';
import Heroes from '../components/Heroes.vue';

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home,
  },
  {
    path: '/abilities',
    name: 'Abilities',
    component: Abilities,
    meta: { title: '能力画像' },
  },
  {
    path: '/ranking',
    name: 'Ranking',
    component: Ranking,
    meta: { title: '联盟排名' },
  },
  {
    path: '/heroes',
    name: 'Heroes',
    component: Heroes,
    meta: { title: '英雄池' },
  },
  {
    path: '/win-lose',
    name: 'WinLose',
    component: WinLose,
    meta: { title: '胜负对比' },
  },
  {
    path: '/admin',
    name: 'Admin',
    component: AdminPanel,
  },
  {
    path: '/records',
    name: 'MatchRecords',
    component: MatchRecords,
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
