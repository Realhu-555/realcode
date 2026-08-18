import { createRouter, createWebHistory } from "vue-router"

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      redirect: "/gis",
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
