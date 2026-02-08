"""
直接测试后台任务
"""
import sys
import os
sys.path.append('.')

# 导入模块
import main_fixed
import threading

print("直接测试 run_audit 函数...")

# 创建测试文件
test_code = """import os
print("Test code")
"""
test_file = "direct_test_file.py"
with open(test_file, "w", encoding="utf-8") as f:
    f.write(test_code)

# 任务ID
task_id = "direct_test_123"
file_path = os.path.abspath(test_file)

print(f"任务ID: {task_id}")
print(f"文件路径: {file_path}")
print(f"文件存在: {os.path.exists(file_path)}")

# 将任务添加到字典
with main_fixed.tasks_lock:
    main_fixed.audit_tasks[task_id] = {
        "task_id": task_id,
        "filename": test_file,
        "language": "python",
        "status": "pending",
        "upload_time": "2026-02-07T12:30:00",
        "file_path": file_path,
        "issues": [],
        "summary": "等待分析"
    }

print(f"任务已添加到字典: {task_id in main_fixed.audit_tasks}")

# 直接运行后台任务
print("\n开始运行后台任务...")
main_fixed.run_audit(task_id, file_path, "python")

# 检查结果
with main_fixed.tasks_lock:
    task = main_fixed.audit_tasks.get(task_id)
    if task:
        print(f"\n任务状态: {task.get('status')}")
        print(f"错误: {task.get('error', '无')}")
        print(f"问题数量: {len(task.get('issues', []))}")
        print(f"摘要: {task.get('summary', '无')}")
    else:
        print(f"\n任务不存在于字典中!")

# 清理
if os.path.exists(test_file):
    os.remove(test_file)
    print(f"\n已清理测试文件: {test_file}")