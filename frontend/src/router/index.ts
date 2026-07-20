import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/prompts',
    },
    {
      path: '/statements',
      name: 'statements',
      component: () => import('@/views/StatementBookPage.vue'),
    },
    {
      path: '/words',
      name: 'words',
      component: () => import('@/views/WordBookPage.vue'),
    },
    {
      path: '/prompts',
      name: 'display',
      component: () => import('@/views/DisplayPage.vue'),
    },
    {
      path: '/manage',
      name: 'manage',
      component: () => import('@/views/ManagePage.vue'),
    },
    {
      path: '/manage/prompts/new',
      name: 'manage-prompt-new',
      component: () => import('@/views/PromptForm.vue'),
    },
    {
      path: '/manage/prompts/:id/edit',
      name: 'manage-prompt-edit',
      component: () => import('@/views/PromptForm.vue'),
    },
  ],
})

export default router
