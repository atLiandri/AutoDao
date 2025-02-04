/**
 * main.js
 *
 * Bootstraps Vuetify and other plugins then mounts the App`
 */

// Plugins
import { registerPlugins } from '@/plugins'
import * as VueRouter from 'vue-router';
import Home from "@/components/Home.vue";
//import Chat from "@/components/Chat.vue";
// Components
import App from './App.vue'

// Composables
import { createApp } from 'vue'

const app = createApp(App)

registerPlugins(app)

const routes = [
    { path: '/', component: Home },
//    { path: '/chat', component: Chat },
  //   { path: '/profile', component: Profile },
];

const router = VueRouter.createRouter({
    history: VueRouter.createWebHistory(),
    routes,
});

app.use(router).mount('#app')
  
