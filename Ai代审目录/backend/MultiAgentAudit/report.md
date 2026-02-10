# 安全审计报告

## 1. 概述
本次审计针对一个基于 Flask 框架的 Python Web 应用程序。该应用提供了一个代码执行沙箱功能，允许用户提交并运行 Python 代码。审计发现了多个严重的安全漏洞，可能导致远程代码执行、信息泄露和拒绝服务攻击。

## 2. 环境信息
- **编程语言**: Python
- **Web框架**: Flask 3.0.0
- **关键依赖**: flask, flask-socketio, python-socketio, eventlet
- **部署环境**: Docker (python:3.9-slim)
- **暴露端口**: 5000

## 3. 风险等级统计
| 风险等级 | 数量 | 说明 |
| :--- | :--- | :--- |
| **高危 (High)** | 1 | 可导致远程代码执行、系统完全失陷。 |
| **中危 (Medium)** | 3 | 可能导致信息泄露、权限提升或拒绝服务。 |
| **低危 (Low)** | 1 | 信息泄露风险，但需结合其他漏洞利用。 |

## 4. 详细漏洞分析

### 4.1 高危漏洞

#### 漏洞 1: Python代码注入/沙箱逃逸
- **严重性**: High
- **位置**: `app.py` 第127-148行 (`create_script`方法)
- **置信度**: Firm
- **文件**: `C:\Users\25825_o3pmri2\.trae-cn\uploads\app.py`

**漏洞描述**:
代码执行沙箱的过滤机制存在严重缺陷，攻击者可以构造恶意Payload绕过所有安全限制，实现任意Python代码执行，进而读取敏感文件（如`flag.txt`）或执行系统命令。

**代码证据**:
```
indented_code = '\n'.join(['        ' + line for line in self.code.split('\n')]).replace('flag.txt','').replace("GZCTF_FLAG","").replace("@","")
while True:
    save_code = indented_code
    indented_code = remove_non_ascii(indented_code).replace('flag.txt','').replace("GZCTF_FLAG","").replace("@","")
    for _ in banned:
        indented_code = indented_code.replace(_,"")
    if(save_code==indented_code):
        break
```

**漏洞成因**:
1.  **过滤可被绕过**: 使用简单的字符串替换（如`replace('flag.txt','')`）过滤关键词，攻击者可通过字符串拼接（`'fl'+'ag.txt'`）、编码、注释等方式轻松绕过。
2.  **过滤逻辑缺陷**: 过滤顺序为先移除非ASCII字符，再进行禁用词替换。攻击者可构造仅包含ASCII字符的恶意Payload来绕过过滤。
3.  **验证不一致**: `create_script`方法中的过滤逻辑与AST（抽象语法树）验证逻辑独立，存在逻辑不一致性，导致AST验证可能被绕过。

**验证Payload示例**:
- `import os; os.system('cat flag.txt')` - 直接执行系统命令。
- `print(open('fl'+'ag.txt').read())` - 通过字符串拼接绕过关键词过滤读取文件。
- `().__class__.__base__.__subclasses__()[132].__init__.__globals__['system']('cat flag.txt')` - 利用Python对象链进行沙箱逃逸。

**潜在危害**:
- 完全控制服务器，执行任意命令。
- 读取、修改或删除服务器上的任意文件。
- 窃取敏感数据和环境变量。

**修复建议**:
1.  **弃用不安全过滤**: 彻底移除基于字符串替换的过滤逻辑。
2.  **强化沙箱隔离**:
    - 使用操作系统级别的隔离，如Docker容器（配置严格的seccomp、capabilities和资源限制）。
    - 或使用成熟的Python沙箱库（如`PyPy`的沙箱功能、`RestrictedPython`），但需注意其自身的安全性。
3.  **白名单机制**: 如果必须允许执行代码，应严格限制允许导入的模块和函数（白名单），并禁止所有危险操作（如文件I/O、网络访问、子进程创建）。
4.  **代码静态分析**: 在运行前使用AST进行更严格和一致的检查，确保代码不包含任何危险节点。

### 4.2 中危漏洞

#### 漏洞 2: 命令注入
- **严重性**: Medium
- **位置**: `app.py` 第150-151行 (`run`方法)
- **置信度**: Tentative
- **文件**: `C:\Users\25825_o3pmri2\.trae-cn\uploads\app.py`

**漏洞描述**:
`run`方法中用于构建Python命令的参数`self.args`部分来源于用户可控的输入。虽然使用了`split()`进行分割，降低了风险，但仍存在潜在的注入可能性。

**代码证据**:
```
cmd = ['python', script_path]
if self.args:
    cmd.extend(self.args.split())
```

**漏洞成因**:
`self.args`来自`/api/run`接口的JSON参数，由用户输入控制。如果攻击者能够精心构造`args`参数，可能影响最终命令的执行参数，尽管风险因使用`split()`而降低。

**潜在危害**:
- 通过注入命令行参数影响Python解释器的行为。
- 结合其他漏洞可能导致更严重的利用。

**修复建议**:
1.  **严格验证输入**: 对`self.args`进行严格的白名单验证，只允许特定的、安全的参数（如`-O`, `-B`等）。
2.  **避免用户控制参数**: 重新设计功能，避免将用户输入直接作为命令行参数传递。
3.  **使用安全API**: 如果必须传递参数，确保使用列表形式（已实现）并避免通过shell执行。

#### 漏洞 3: 路径遍历/文件操作
- **严重性**: Medium
- **位置**: `app.py` 第127行 (`create_script`方法)
- **置信度**: Tentative
- **文件**: `C:\Users\25825_o3pmri2\.trae-cn\uploads\app.py`

**漏洞描述**:
在`/tmp`目录下创建可执行的临时Python文件。虽然文件名是随机的，但存在时间竞争攻击（TOCTOU）的风险，攻击者可能预测或暴力破解文件名。

**代码证据**:
```
self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir='/tmp', delete=False)
```

**漏洞成因**:
临时文件创建在全局可写的`/tmp`目录，权限设置为`0o755`（可执行）。结合代码注入漏洞，攻击者可能写入恶意内容并执行。

**验证Payload示例**:
- 尝试读取系统文件：`../../../etc/passwd`
- 尝试读取环境变量：`../../../proc/self/environ`

**潜在危害**:
- 结合代码注入漏洞，实现更稳定的文件读写或代码执行。
- 在共享主机环境下，可能被其他用户恶意利用。

**修复建议**:
1.  **使用安全临时目录**: 使用`tempfile.mkdtemp()`在更安全的私有目录创建临时文件。
2.  **降低文件权限**: 将临时文件的权限设置为仅当前用户可读可写（如`0o600`），移除执行权限。
3.  **及时清理**: 确保进程结束后立即删除临时文件。

#### 漏洞 4: 拒绝服务（DoS）
- **严重性**: Medium
- **位置**: `app.py` 第150-160行 (`run`方法)
- **置信度**: Firm
- **文件**: `C:\Users\25825_o3pmri2\.trae-cn\uploads\app.py`

**漏洞描述**:
应用程序未对并发执行的代码进程数量进行任何限制。攻击者可以同时发起大量执行请求，快速消耗系统资源。

**代码证据**:
```
self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, text=True, bufsize=1, universal_newlines=True)
...
threading.Thread(target=read_output, daemon=True).start()
```

**漏洞成因**:
- 每个请求都会创建一个新的子进程和线程。
- 未对全局的`active_processes`字典大小进行限制。
- 子进程可能执行消耗资源的恶意代码（如无限循环、`fork`炸弹）。

**验证Payload示例**:
- `import os; while True: os.fork()` - 快速耗尽系统PID资源。
- `while True: print('x' * 1000000)` - 持续输出，占用CPU和I/O，耗尽缓冲区。

**潜在危害**:
- 系统内存、CPU、进程数被耗尽，导致服务完全不可用。
- 可能影响同一服务器上的其他应用。

**修复建议**:
1.  **资源限制**:
    - 使用`resource`模块或在Docker中设置CPU、内存、进程数限制。
    - 对`subprocess.Popen`使用`preexec_fn`参数设置子进程资源限制。
2.  **并发控制**:
    - 实现请求队列和最大并发数限制。
    - 使用信号量或线程池控制同时运行的`run`方法实例数量。
3.  **超时机制**: 为每个代码执行任务设置严格的超时时间，超时后强制终止进程。
4.  **输入检查**: 拒绝执行明显恶意的DoS代码（如包含`while True:`且无`sleep`的循环）。

### 4.3 低危漏洞

#### 漏洞 5: 信息泄露
- **严重性**: Low
- **位置**: `app.py` 第113-119行 (`create_script`方法的wrapper)
- **置信度**: Firm
- **文件**: `C:\Users\25825_o3pmri2\.trae-cn\uploads\app.py`

**漏洞描述**:
应用程序的wrapper代码明确将环境变量`GZCTF_FLAG`写入`/flag.txt`文件。虽然尝试过滤相关字符串，但由于过滤机制不完善（见漏洞1），攻击者仍可能读取到该敏感信息。

**代码证据**:
```
if(os.environ.get('GZCTF_FLAG', '')!=''):
    flag_content = os.environ.get('GZCTF_FLAG', '')
    try:
        with open('/flag.txt', 'w') as f:
            f.write(flag_content)
    except:
        pass
```

**漏洞成因**:
核心问题是漏洞1（代码注入）导致过滤失效。此段代码本身揭示了敏感信息（flag）的存在和存储位置，降低了攻击难度。

**验证Payload示例**:
- `import os; print(os.environ.get('GZCTF_FLAG', 'NOT_FOUND'))` - 直接读取环境变量。
- `import os; print(dict(os.environ))` - 打印所有环境变量。

**潜在危害**:
- 直接泄露比赛或系统的核心敏感数据（flag）。
- 泄露的环境变量可能包含其他敏感配置，如数据库密码、API密钥等。

**修复建议**:
1.  **修复根本问题**: 首要任务是彻底修复漏洞1，确保沙箱无法逃逸。
2.  **避免写入文件**: 重新设计应用逻辑，避免将敏感信息从环境变量写入文件系统。如果必须使用文件，应考虑使用内存文件系统（如`tmpfs`）或更严格的权限控制。
3.  **最小权限原则**: 运行应用的Docker容器或进程不应具有读取`/flag.txt`的权限（如果该文件仅为其他服务准备）。

## 5. 总结与建议
本次审计发现的目标应用存在严重的安全缺陷，**高危的代码注入漏洞**使得攻击者能够完全绕过沙箱限制，执行任意代码。结合中危的DoS和路径遍历漏洞，可造成服务瘫痪和进一步渗透。

**总体修复优先级**:
1.  **立即修复**: 漏洞1（代码注入/沙箱逃逸）。这是最紧急的威胁，必须首先解决。
2.  **尽快修复**: 漏洞4（拒绝服务）。该漏洞可能被轻易利用导致服务中断。
3.  **计划内修复**: 漏洞2（命令注入）、漏洞3（路径遍历）和漏洞5（信息泄露）。在修复漏洞1后，这些漏洞的风险会显著降低，但仍需处理以提升整体安全性。

**加固建议**:
- **深度防御**: 不要依赖单一的过滤或验证机制。应采用多层防护，包括输入校验、沙箱隔离、资源限制和输出编码。
- **安全开发生命周期**: 在代码编写阶段即考虑安全性，对涉及代码执行、命令执行、文件操作的功能进行严格设计和评审。
- **定期安全审计**: 对代码进行定期的静态和动态安全扫描，尤其是在功能更新后。