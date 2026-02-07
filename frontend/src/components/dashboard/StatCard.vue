<template>
  <el-card class="stat-card" :body-style="{ padding: '20px' }" shadow="hover">
    <div class="stat-content">
      <div class="stat-icon" :style="{ backgroundColor: iconBg }">
        <el-icon :size="24" :color="iconColor">
          <component :is="icon" />
        </el-icon>
      </div>
      <div class="stat-info">
        <div class="stat-title">{{ title }}</div>
        <div class="stat-value">
          <el-statistic :value="value" :precision="precision">
            <template v-if="suffix" #suffix>{{ suffix }}</template>
          </el-statistic>
        </div>
        <div class="stat-trend" v-if="trend !== undefined">
          <el-icon :color="trend >= 0 ? '#67c23a' : '#f56c6c'">
            <caret-top v-if="trend >= 0" />
            <caret-bottom v-else />
          </el-icon>
          <span :style="{ color: trend >= 0 ? '#67c23a' : '#f56c6c' }">
            {{ Math.abs(trend) }}%
          </span>
          <span class="trend-text">较上周</span>
        </div>
      </div>
    </div>
  </el-card>
</template>

<script setup>
defineProps({
  title: String,
  value: Number,
  suffix: String,
  precision: { type: Number, default: 0 },
  icon: { type: String, default: 'TrendCharts' },
  iconBg: { type: String, default: '#ecf5ff' },
  iconColor: { type: String, default: '#409eff' },
  trend: Number
})
</script>

<style scoped>
.stat-card {
  transition: all 0.3s;
}

.stat-card:hover {
  transform: translateY(-2px);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-info {
  flex: 1;
  min-width: 0;
}

.stat-title {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
  line-height: 1.2;
}

.stat-trend {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 8px;
  font-size: 13px;
}

.trend-text {
  color: #909399;
  margin-left: 4px;
}

:deep(.el-statistic__content) {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
}
</style>