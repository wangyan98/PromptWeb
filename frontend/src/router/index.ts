import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/prompts',
    },
    {
      path: '/prompts',
      name: 'prompt-list',
      component: () => import('@/views/PromptList.vue'),
    },
    {
      path: '/prompts/new',
      name: 'prompt-new',
      component: () => import('@/views/PromptForm.vue'),
    },
    {
      path: '/prompts/:id',
      name: 'prompt-detail',
      component: () => import('@/views/PromptDetail.vue'),
    },
    {
      path: '/prompts/:id/edit',
      name: 'prompt-edit',
      component: () => import('@/views/PromptForm.vue'),
    },
    {
      path: '/statement-types',
      name: 'statement-types',
      component: () => import('@/views/StatementTypeManager.vue'),
    },
    {
      path: '/import',
      name: 'import',
      component: () => import('@/views/ImportPage.vue'),
    },
  ],
})

export default router
