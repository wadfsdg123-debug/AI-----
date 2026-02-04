开发报告（技术实现细节）
目录结构(确保开发效率和清晰度)
AI代审-system/
│
├── backend/                    # 后端（FastAPI + AI）
│   ├── main.py                 # FastAPI 入口 & 路由
│   ├── sandbox.py              # Docker 沙箱管理
│   ├── agents.py               # 多 Agent 编排逻辑（Recon/Audit/Review）
│   ├── report.py               # Markdown/PDF 报告生成
│   └── requirements.txt        # Python 依赖
│
├── frontend/                   # 前端（Vue 3）
│   ├── src/
│   │   ├── components/
│   │   │   ├── Upload.vue      # 拖拽上传
│   │   │   └── Terminal.vue    # xterm.js 终端
│   │   └── App.vue
│   └── package.json
│
├── docker_env/
│   ├── Dockerfile.base         # 审计基础镜像（含 bandit/semgrep）
│   └── docker-compose.yml      # 启动 backend + frontend + redis
│
├── docs/
│   └── api_design.md           # 接口定义（/upload + WebSocket）
│
├── .gitignore
├── README.md                   # 项目介绍 + 启动命令
└── LICENSE                     # MIT 协议
一、架构分层说明

层级	技术栈	功能说明
前端	Vue 3 + Element Plus + xterm.js	赛博朋克暗黑UI、拖拽上传、终端模拟、WebSocket 消息解析
后端	FastAPI (async) + Redis + docker-py	文件接收、任务调度、容器管理、WebSocket 广播
AI引擎	LangChain + OpenAI/DeepSeek	多Agent 编排、Prompt 工程、误报过滤、PoC 生成
沙箱	Docker 容器（隔离运行）	每任务独立容器，挂载代码目录，auto_remove=true
存储	SQLite（任务元数据） + JSON/Markdown（报告）	轻量持久化，便于部署

二、核心模块实现细节
1. 容器化沙箱模块（Sandbox）
基础镜像：cyber-audit-base，预装 semgrep, bandit, git, maven, php-cli
生命周期管理：
python
def create_sandbox(task_id: str, code_path: str):
    container = client.containers.run(
        "cyber-audit-base",
        volumes={code_path: {'bind': '/sandbox/code', 'mode': 'rw'}},
        detach=True,
        auto_remove=True,
        name=f"audit-{task_id}"
    )
    return container
命令执行：
python
def execute_in_sandbox(container, cmd: str) -> str:
    exit_code, output = container.exec_run(cmd)
    return output.decode('utf-8')
2. 多 Agent 协同逻辑（LangChain 编排）
Agent 1 - ReconAgent
解析 requirements.txt / pom.xml → 输出技术栈（如 Python/Django）
Agent 2 - AuditAgent
分块读取关键文件（如 views.py, routes.php），结合 SAST 工具输出 + LLM Prompt 进行深度分析
Prompt 示例：
“你是一名资深安全专家。请结合以下静态扫描结果 {tool_output}，分析代码片段 {code_snippet} 是否存在真实漏洞，排除误报。”
Agent 3 - ReviewAgent
对 AuditAgent 结果进行交叉验证，生成结构化 JSON 中间报告（含 CVSS 初评）
3. WebSocket 实时反馈管道
消息格式（JSON）：
json
{
  "type": "log|vuln_found|status_update",
  "data": { ... },
  "timestamp": "ISO8601"
}
后端推送逻辑（FastAPI + asyncio）：
python
async def audit_task(task_id: str, websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # 启动沙箱、调用Agent...
        for log in stream_logs_from_sandbox():
            await websocket.send_json({"type": "log", "data": log})
        for vuln in vulnerabilities:
            await websocket.send_json({"type": "vuln_found", "data": vuln})
    finally:
        manager.disconnect(websocket)
4. 报告生成引擎
输入：Agent 3 输出的 JSON 漏洞列表
处理：
o渲染为 Markdown（含代码高亮、修复建议、CVSS评分）
o使用 weasyprint 生成 PDF（后端）或 html2canvas（前端备选）
输出示例：
markdown
##  高危漏洞：SQL 注入
**文件**：`/app/views.py#L45`  
**描述**：用户输入未过滤直接拼接 SQL 查询  
**修复建议**：使用参数化查询（如 SQLAlchemy）  
**CVSS v3.1**：9.8 (Critical)
三、已验证功能清单
表格
功能	状态	测试方式
大文件上传（≤500MB）	✅	上传 Spring Boot 项目 ZIP
多语言识别（Python/Java/PHP）	✅	上传对应语言示例项目
SAST + LLM 联合分析	✅	Bandit + LLM 交叉验证
PoC 自动生成与沙箱执行	✅	成功复现 DVWA SQLi
WebSocket 实时日志流	✅	xterm.js 渲染绿色字符流
赛博朋克 UI 动效	✅	霓虹边框 + 故障字体
Markdown/PDF 报告导出	✅	一键下载完整报告
