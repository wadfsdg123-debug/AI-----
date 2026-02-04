# AIAgents (AIxVuln Python Agents)

一个用于自动化代码安全审计的自主多智能体系统，具备环境搭建、漏洞分析、验证和报告生成功能。

## 前置条件

- Python 3.9+
- Docker (正在运行且可通过命令行访问)

## 配置指南

在运行智能体之前，您必须配置 LLM 设置。

1.  **找到配置示例：**
    在项目根目录下找到 `config.example.json`。

2.  **创建您的配置文件：**
    将 `config.example.json` 复制或重命名为 `config.json`。

    ```bash
    # Windows PowerShell
    Copy-Item config.example.json config.json
    
    # Linux/Mac
    cp config.example.json config.json
    ```

3.  **编辑 `config.json`：**
    打开 `config.json` 并填入您的 LLM API 详细信息。

    ```json
    {
        "llm": {
            "api_key": "YOUR_ACTUAL_API_KEY",
            "base_url": "https://api.openai.com/v1",  // 或者您的兼容提供商 URL
            "model": "gpt-4o"                           // 或者您偏好的模型
        },
        "default_target_path": "./uploads/upload"       // 您想要审计的代码路径
    }
    ```

    > **安全提示：** `config.json` 已包含在 `.gitignore` 中，以防止意外泄露您的 API 密钥。切勿将真实的 `config.json` 提交到版本控制系统。

## 使用方法

运行主程序以启动审计流程：

```bash
python main.py [target_path]
```

- 如果提供了 `target_path`，智能体将审计该目录。
- 如果未提供，默认为 `config.json` 中指定的路径（通常是 `./uploads/upload`）。

## 智能体工作流程

1.  **OpsAgent（运维智能体）**：检测项目语言，搭建 Docker 沙箱，并解决环境问题（例如端口冲突）。
2.  **AnalyzeAgent（分析智能体）**：执行静态代码分析以识别潜在的漏洞候选。
3.  **VerifierAgent（验证智能体）**：通过对实时沙箱环境执行 payload 来验证发现的漏洞。
4.  **ReportAgent（报告智能体）**：将发现和验证证据汇总成一份易读的报告（`final_report.md`）。
