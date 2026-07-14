import { createRouter, createWebHashHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import SearchResultView from '../views/SearchResultView.vue'
import CommunityListView from '../views/CommunityListView.vue'
import PostDetailView from '../views/PostDetailView.vue'
import PostFormView from '../views/PostFormView.vue'
import NotFoundView from '../views/NotFoundView.vue'

const router = createRouter({
  history: createWebHashHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'home', component: HomeView },
    { path: '/search', name: 'search', component: SearchResultView },
    { path: '/community', name: 'community', component: CommunityListView },
    { path: '/community/new', name: 'post-create', component: PostFormView },
    { path: '/community/:id', name: 'post-detail', component: PostDetailView, props: true },
    { path: '/community/:id/edit', name: 'post-edit', component: PostFormView, props: true },
    { path: '/:pathMatch(.*)*', name: 'not-found', component: NotFoundView },
  ],
  scrollBehavior() {
    return { top: 0 }
  },
})

export default router
