<script setup lang="ts">
import SideNav from './SideNav.vue'
</script>

<template>
  <div class="app-layout">
    <SideNav />
    <main class="main-content">
      <slot />
    </main>
  </div>
</template>

<style scoped>
.app-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.main-content {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-lg);
}
</style>
