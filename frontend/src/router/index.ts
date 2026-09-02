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
    {
      path: "/gis/models/add",
      name: "add-model",
      component: () => import("../views/AddModel.vue"),
      meta: { standalone: true },
    },
  ],
})

export default router
