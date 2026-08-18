import { createRouter, createWebHistory } from "vue-router"

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      redirect: "/create",
    },
    {
      path: "/create",
      name: "create",
      component: () => import("../views/Create.vue"),
    },
    {
      path: "/strategy/:projectId",
      name: "strategy",
      component: () => import("../views/Strategy.vue"),
    },
    {
      path: "/preview/:projectId",
      name: "preview",
      component: () => import("../views/Preview.vue"),
    },
    {
      path: "/gis",
      name: "gis",
      component: () => import("../views/GisAssistant.vue"),
      meta: { standalone: true },
    },
  ],
})

export default router
