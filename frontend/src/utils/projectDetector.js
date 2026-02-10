// 根据文件列表检测项目类型
export function detectProjectType(files) {
  if (!files || files.length === 0) return 'Unknown'
  
  const fileNames = files.map(f => f.toLowerCase())
  
  // Python
  if (fileNames.some(f => f.includes('requirements.txt') || f.includes('pipfile'))) {
    return 'Python'
  }
  if (fileNames.some(f => f.endsWith('.py'))) {
    return 'Python'
  }
  
  // JavaScript/Node.js
  if (fileNames.some(f => f.includes('package.json') || f.includes('node_modules'))) {
    return 'JavaScript'
  }
  if (fileNames.some(f => f.endsWith('.js') || f.endsWith('.ts'))) {
    return 'JavaScript'
  }
  
  // Java
  if (fileNames.some(f => f.includes('pom.xml') || f.includes('build.gradle'))) {
    return 'Java'
  }
  if (fileNames.some(f => f.endsWith('.java'))) {
    return 'Java'
  }
  
  // PHP
  if (fileNames.some(f => f.includes('composer.json'))) {
    return 'PHP'
  }
  if (fileNames.some(f => f.endsWith('.php'))) {
    return 'PHP'
  }
  
  // Go
  if (fileNames.some(f => f.includes('go.mod'))) {
    return 'Go'
  }
  
  // Rust
  if (fileNames.some(f => f.includes('cargo.toml'))) {
    return 'Rust'
  }
  
  return 'Unknown'
}