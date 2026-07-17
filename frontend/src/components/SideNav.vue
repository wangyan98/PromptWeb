<script setup lang="ts">
import { useRoute } from 'vue-router'

const route = useRoute()

const navItems = [
  { label: 'Prompt 列表', to: '/prompts', icon: '📋' },
  { label: '语句类型', to: '/statement-types', icon: '🏷️' },
  { label: '导入数据', to: '/import', icon: '📥' },
]
</script>

<template>
  <aside class="side-nav">
    <div class="logo">
      <span class="logo-icon">🎨</span>
      <span class="logo-text">PromptWeb</span>
    </div>
    <nav class="nav-links">
      <RouterLink
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        class="nav-item"
        :class="{ active: route.path.startsWith(item.to) }"
      >
        <span class="nav-icon">{{ item.icon }}</span>
        <span class="nav-label">{{ item.label }}</span>
      </RouterLink>
    </nav>
  </aside>
</template>

<style scoped>
.side-nav {
  width: var(--sidebar-width);
  background: var(--color-bg-secondary);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.logo {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-md) var(--space-lg);
  height: var(--header-height);
  border-bottom: 1px solid var(--color-border);
}

.logo-icon {
  font-size: 1.5rem;
}

.logo-text {
  font-size: var(--font-size-lg);
  font-weight: 700;
  color: var(--color-accent);
}

.nav-links {
  padding: var(--space-md);
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--border-radius);
  color: var(--color-text-secondary);
  transition: all var(--transition-fast);
  text-decoration: none;
  font-size: var(--font-size-sm);
}

.nav-item:hover {
  background: var(--color-bg-hover);
  color: var(--color-text-primary);
  text-decoration: none;
}

.nav-item.active {
  background: var(--color-bg-tertiary);
  color: var(--color-accent);
}

.nav-icon {
  font-size: 1.1rem;
}
</style>
