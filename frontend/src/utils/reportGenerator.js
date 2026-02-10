// 生成Markdown格式报告
export function generateMarkdownReport(task, vulns) {
  const now = new Date().toLocaleString('zh-CN')
  
  const lines = [
    `# 代码审计报告`,
    ``,
    `> 生成时间：${now}`,
    ``,
    `## 任务信息`,
    ``,
    `| 项目 | 内容 |`,
    `|------|------|`,
    `| 任务ID | ${task.taskId} |`,
    `| 文件名 | ${task.filename} |`,
    `| 项目类型 | ${task.projectType} |`,
    `| 审计状态 | ${task.status} |`,
    `| 发现漏洞 | ${vulns.length} 个 |`,
    ``,
    `## 漏洞详情`,
    ``
  ]
  
  if (vulns.length === 0) {
    lines.push(`✅ 未发现安全漏洞，代码质量良好！`)
  } else {
    vulns.forEach((vuln, index) => {
      lines.push(`### ${index + 1}. ${vuln.type} [${vuln.severity.toUpperCase()}]`)
      lines.push(``)
      lines.push(`- **位置**：\`${vuln.file}:${vuln.line}\``)
      lines.push(`- **描述**：${vuln.description}`)
      lines.push(`- **修复建议**：${vuln.suggestion}`)
      if (vuln.codeSnippet) {
        lines.push(``)
        lines.push(`\`\`\``)
        lines.push(vuln.codeSnippet)
        lines.push(`\`\`\``)
      }
      lines.push(``)
      lines.push(`---`)
      lines.push(``)
    })
  }
  
  lines.push(``)
  lines.push(`*本报告由自动化代码审计系统生成*`)
  
  return lines.join('\n')
}

// 下载报告文件
export function downloadReport(markdownContent, filename) {
  const blob = new Blob([markdownContent], { type: 'text/markdown' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}