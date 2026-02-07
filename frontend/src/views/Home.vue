<template>
  <div class="home">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>代码审计系统</span>
          <el-button type="primary" @click="goToTerminal">
            进入终端
          </el-button>
        </div>
      </template>
      
      <!-- 文件上传组件 -->
      <FileUpload />
      
    </el-card>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import FileUpload from '@/components/FileUpload.vue'

const router = useRouter()

const goToTerminal = () => {
  router.push('/terminal')
}
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>