import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import './assets/base.css'

const app = createApp(App)

app.config.errorHandler = (error) => {
  console.error('[화장실록 Vue 오류]', error)
  const root = document.querySelector('#app')
  if (root && !root.children.length) {
    root.innerHTML = `
      <main style="min-height:100vh;padding:40px;background:#f7fcff;color:#18303f;font-family:Arial,sans-serif">
        <h1>화면을 불러오지 못했습니다.</h1>
        <p>브라우저 개발자 도구의 Console 오류를 확인해 주세요.</p>
      </main>
    `
  }
}

app.use(router).mount('#app')
