# 多智能体安全审计系统 (Multi-Agent Security Audit System)

这是一个实验性的自动化代码审计系统，由大语言模型 (LLM) 和多智能体架构驱动。它旨在辅助安全研究人员和开发人员进行初步的安全扫描，识别潜在漏洞并生成验证 Payload。

> **免责声明**：本工具仅供教育和授权测试使用。可能会产生误报或漏报。请务必人工验证扫描结果。

## 功能特性

*   **多智能体架构**：
    *   **OpsAgent (运维智能体)**：自动识别项目环境、编程语言、框架和依赖。
    *   **AnalyzeAgent (审计智能体)**：基于语义理解执行静态代码分析，识别潜在的安全漏洞。
    *   **HackerAgent (攻防智能体)**：针对识别出的漏洞生成具体的验证 Payload（模拟攻击验证）。
    *   **ReporterAgent (报告智能体)**：将所有发现汇总成一份详细的 Markdown 格式安全报告。
*   **广泛的语言支持**：支持 Python, Java, Node.js, PHP, Go, C, C++, C#, Ruby, Rust。
*   **灵活的扫描模式**：支持审计单个文件或整个项目目录。

## 支持的语言

系统目前支持审计以下扩展名的文件：
*   Python (`.py`)
*   PHP (`.php`)
*   Java (`.java`)
*   JavaScript/TypeScript (`.js`, `.ts`)
*   Go (`.go`)
*   C/C++ (`.c`, `.cpp`)
*   Ruby (`.rb`)
*   Rust (`.rs`)
*   C# (`.cs`)

## 安装指南

1.  克隆本仓库。
2.  使用 pip 安装依赖：

    ```bash
    pip install -r requirements.txt
    ```

## 配置说明

1.  将 `.env.example` 复制为 `.env`：

    ```bash
    cp .env.example .env
    ```

2.  编辑 `.env` 文件并配置您的 LLM 提供商设置：

    ```ini
    # 选项: openai, deepseek, gemini
    LLM_PROVIDER=deepseek
    
    # API 密钥 (必填)
    LLM_API_KEY=your_api_key_here
    
    # Base URL (可选，默认为提供商的标准 URL)
    # DeepSeek: https://api.deepseek.com
    # OpenAI: https://api.openai.com/v1
    LLM_BASE_URL=https://api.deepseek.com
    
    # 模型名称 (可选)
    # 示例: deepseek-chat, gpt-3.5-turbo, gemini-1.5-flash
    LLM_MODEL=deepseek-chat
    ```

## 使用方法

运行主脚本开始审计。您可以指定要扫描的文件或目录路径。

**扫描默认的 `uploads` 目录：**

```bash
python main.py
```
*(如果 `uploads` 目录不存在，系统会自动创建。请将文件放入该目录后再次运行。)*

**扫描指定目录：**

```bash
python main.py /path/to/your/project
```

**扫描指定文件：**

```bash
python main.py /path/to/vulnerable.py
```

## 输出结果

审计完成后，将在根目录下生成以下文件：
*   `report.md`: 详细的安全审计报告。
*   `system.log`: 用于调试的系统执行日志。

## 许可证

[MIT License](LICENSE)
