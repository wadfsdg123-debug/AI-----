<template>
  <el-card class="chart-card" shadow="hover">
    <template #header>
      <div class="card-header">
        <span>审计趋势（近7天）</span>
        <el-tag type="info" size="small">实时更新</el-tag>
      </div>
    </template>
    
    <div ref="chartRef" class="chart-container"></div>
  </el-card>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import axios from 'axios'

const chartRef = ref(null)
let chartInstance = null

const getOption = (data) => ({
  tooltip: {
    trigger: 'axis',
    axisPointer: {
      type: 'cross',
      label: { backgroundColor: '#6a7985' }
    }
  },
  legend: {
    data: ['审计任务数', '发现漏洞数']
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    containLabel: true
  },
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: data.dates
  },
  yAxis: [
    {
      type: 'value',
      name: '任务数',
      position: 'left'
    },
    {
      type: 'value',
      name: '漏洞数',
      position: 'right'
    }
  ],
  series: [
    {
      name: '审计任务数',
      type: 'line',
      smooth: true,
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
          { offset: 1, color: 'rgba(64, 158, 255, 0.05)' }
        ])
      },
      itemStyle: { color: '#409eff' },
      data: data.tasks
    },
    {
      name: '发现漏洞数',
      type: 'line',
      smooth: true,
      yAxisIndex: 1,
      itemStyle: { color: '#f56c6c' },
      lineStyle: { width: 3 },
      data: data.vulns
    }
  ]
})

const fetchData = async () => {
  try {
    const res = await axios.get('/api/dashboard/trend')
    return res.data
  } catch (error) {
    // 模拟数据
    const dates = []
    const tasks = []
    const vulns = []
    for (let i = 6; i >= 0; i--) {
      const d = new Date()
      d.setDate(d.getDate() - i)
      dates.push(d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' }))
      tasks.push(Math.floor(Math.random() * 10) + 5)
      vulns.push(Math.floor(Math.random() * 20) + 2)
    }
    return { dates, tasks, vulns }
  }
}

const initChart = async () => {
  const data = await fetchData()
  if (chartRef.value) {
    chartInstance = echarts.init(chartRef.value)
    chartInstance.setOption(getOption(data))
  }
}

const handleResize = () => {
  chartInstance?.resize()
}

onMounted(() => {
  initChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-container {
  height: 300px;
  width: 100%;
}
</style>