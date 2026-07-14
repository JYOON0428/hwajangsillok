<template>
  <header class="app-header">
    <div class="header-inner">
      <RouterLink class="brand" to="/" aria-label="화장실록 홈">
        <span class="brand-mark" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none">
            <circle cx="7" cy="5.5" r="2" fill="currentColor" />
            <circle cx="17" cy="5.5" r="2" fill="currentColor" />
            <path d="M4.5 9h5v10h-2v-5h-1v5h-2V9Zm10 0h5l1.4 5h-2.2v5h-2v-5h-1v5h-2v-5h-1.2L14.5 9Z" fill="currentColor" />
            <path d="M12 3v18" stroke="currentColor" stroke-width="1.3" opacity=".58" />
          </svg>
        </span>
        <strong>화장실록</strong>
      </RouterLink>
    </div>
  </header>
</template>
