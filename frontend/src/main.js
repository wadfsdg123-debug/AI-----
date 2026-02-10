import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

// Element Plus
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

// 赛博朋克主题
import './styles/cyberpunk.css'
import './styles/terminal.css'

const app = createApp(App)

app.use(ElementPlus)
app.use(router)

app.mount('#app')