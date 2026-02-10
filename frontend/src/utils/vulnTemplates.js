// 漏洞类型模板
export const VULN_TEMPLATES = {
  'SQL注入': {
    severity: 'critical',
    description: '未对用户输入进行过滤，直接拼接到SQL查询中，可能导致数据库被攻击者控制',
    suggestion: '使用参数化查询（Prepared Statements），永远不要将用户输入直接拼接到SQL语句中',
    codeSnippet: `// 危险代码
query = "SELECT * FROM users WHERE id = " + userId
db.execute(query)

// 安全代码
query = "SELECT * FROM users WHERE id = ?"
db.execute(query, [userId])`
  },
  
  'XSS跨站脚本': {
    severity: 'high',
    description: '未对输出进行HTML转义，攻击者可注入恶意脚本窃取用户Cookie或执行钓鱼攻击',
    suggestion: '使用模板引擎的自动转义功能，或对特殊字符进行HTML编码',
    codeSnippet: `// 危险代码
element.innerHTML = userInput

// 安全代码
element.textContent = userInput`
  },
  
  '命令注入': {
    severity: 'critical',
    description: '直接使用用户输入执行系统命令，可能导致服务器被完全控制',
    suggestion: '避免使用system/exec等函数，如必须使用需进行严格的输入验证和白名单过滤',
    codeSnippet: `// 危险代码
os.system("ping " + hostname)

// 安全代码
import subprocess
subprocess.run(["ping", "-c", "4", hostname], check=True)`
  },
  
  '路径遍历': {
    severity: 'high',
    description: '未对文件路径进行验证，攻击者可读取任意文件（如/etc/passwd）',
    suggestion: '使用白名单验证文件名，移除所有路径分隔符和特殊字符',
    codeSnippet: `// 危险代码
fs.readFileSync("/var/www/uploads/" + filename)

// 安全代码
const path = require('path')
const safeName = path.basename(filename)
fs.readFileSync("/var/www/uploads/" + safeName)`
  },
  
  '硬编码密钥': {
    severity: 'medium',
    description: '代码中硬编码了API密钥、密码或令牌，可能泄露敏感信息',
    suggestion: '使用环境变量或密钥管理服务（KMS）存储敏感配置，代码中只保留配置读取逻辑',
    codeSnippet: `// 危险代码
const API_KEY = "sk-1234567890abcdef"

// 安全代码
const API_KEY = process.env.API_KEY`
  },
  
  '不安全的反序列化': {
    severity: 'critical',
    description: '直接反序列化用户输入的数据，可能导致远程代码执行',
    suggestion: '使用JSON等安全格式替代pickle，或实施严格的类型检查和签名验证',
    codeSnippet: `// 危险代码
data = pickle.loads(userInput)

// 安全代码
data = json.loads(userInput)`
  },
  
  '敏感信息泄露': {
    severity: 'medium',
    description: '错误信息暴露了系统路径、数据库结构、堆栈跟踪等敏感信息',
    suggestion: '自定义错误页面，生产环境关闭调试模式，统一返回模糊的错误信息',
    codeSnippet: `// 危险代码
catch (Exception e) {
  return e.getStackTrace().toString()
}

// 安全代码
catch (Exception e) {
  logger.error(e)
  return "系统错误，请联系管理员"
}`
  },
  
  '弱加密算法': {
    severity: 'medium',
    description: '使用了MD5/SHA1等已破解的哈希算法，容易被彩虹表攻击',
    suggestion: '使用bcrypt/Argon2等现代密码哈希算法，或AES-256等强加密算法',
    codeSnippet: `// 危险代码
password_hash = md5(password)

// 安全代码
password_hash = bcrypt.hashpw(password, bcrypt.gensalt())`
  }
}

// 根据漏洞类型获取模板
export function getVulnTemplate(type) {
  return VULN_TEMPLATES[type] || {
    severity: 'low',
    description: '未知类型的安全问题',
    suggestion: '请人工审查代码',
    codeSnippet: '// 暂无示例代码'
  }
}

// 获取严重程度样式
export function getSeverityType(severity) {
  const map = {
    'critical': 'danger',
    'high': 'danger',
    'medium': 'warning',
    'low': 'info'
  }
  return map[severity] || 'info'
}