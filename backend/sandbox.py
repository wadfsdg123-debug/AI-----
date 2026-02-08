"""
安全沙箱模块
用于隔离运行代码分析
"""

import os
import shutil
import tempfile
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class SecureSandbox:
    """安全沙箱环境"""
    
    def __init__(self, base_dir: str = None):
        """
        初始化沙箱
        
        Args:
            base_dir: 沙箱基础目录，默认为临时目录
        """
        self.base_dir = Path(base_dir) if base_dir else Path(tempfile.gettempdir()) / "cyber_audit_sandbox"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"沙箱基础目录: {self.base_dir}")
        
    def create_sandbox(self, task_id: str) -> Path:
        """
        为任务创建沙箱目录
        
        Args:
            task_id: 任务ID
            
        Returns:
            沙箱目录路径
        """
        sandbox_path = self.base_dir / task_id
        sandbox_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"创建沙箱目录: {sandbox_path}")
        return sandbox_path
    
    def copy_to_sandbox(self, task_id: str, source_file: str) -> Path:
        """
        将文件复制到沙箱中
        
        Args:
            task_id: 任务ID
            source_file: 源文件路径
            
        Returns:
            沙箱中的文件路径
        """
        sandbox_path = self.create_sandbox(task_id)
        dest_file = sandbox_path / Path(source_file).name
        
        # 复制文件
        shutil.copy2(source_file, dest_file)
        logger.info(f"已复制文件到沙箱: {source_file} -> {dest_file}")
        return dest_file
    
    def get_sandbox_path(self, task_id: str) -> Path:
        """
        获取任务沙箱路径
        
        Args:
            task_id: 任务ID
            
        Returns:
            沙箱目录路径
        """
        sandbox_path = self.base_dir / task_id
        return sandbox_path
    
    def cleanup(self, task_id: str):
        """
        清理任务沙箱
        
        Args:
            task_id: 任务ID
        """
        sandbox_path = self.get_sandbox_path(task_id)
        if sandbox_path.exists():
            try:
                shutil.rmtree(sandbox_path)
                logger.info(f"已清理沙箱: {sandbox_path}")
            except Exception as e:
                logger.warning(f"清理沙箱失败: {e}")
    
    def cleanup_all(self):
        """
        清理所有沙箱（用于应用关闭时）
        """
        if self.base_dir.exists():
            try:
                shutil.rmtree(self.base_dir)
                logger.info(f"已清理所有沙箱: {self.base_dir}")
            except Exception as e:
                logger.warning(f"清理所有沙箱失败: {e}")


# 单例模式
sandbox_instance = SecureSandbox()

# 导出常用函数
def copy_to_sandbox(task_id: str, source_file: str) -> Path:
    return sandbox_instance.copy_to_sandbox(task_id, source_file)

def get_sandbox_path(task_id: str) -> Path:
    return sandbox_instance.get_sandbox_path(task_id)

def cleanup(task_id: str):
    return sandbox_instance.cleanup(task_id)

def cleanup_all():
    return sandbox_instance.cleanup_all()


if __name__ == "__main__":
    # 测试沙箱功能
    import tempfile
    
    # 创建一个测试文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write('print("Hello, Sandbox!")')
        test_file = f.name
    
    try:
        sandbox = SecureSandbox()
        print(f"沙箱基础目录: {sandbox.base_dir}")
        
        # 测试创建和复制
        task_id = "test_task_123"
        dest = sandbox.copy_to_sandbox(task_id, test_file)
        print(f"文件复制到: {dest}")
        
        # 验证文件存在
        if dest.exists():
            print("✓ 文件复制成功")
            # 读取文件内容验证
            with open(dest, 'r') as f:
                content = f.read()
                print(f"文件内容: {content}")
        else:
            print("✗ 文件复制失败")
        
        # 清理
        sandbox.cleanup(task_id)
        print(f"✓ 沙箱清理完成")
        
    finally:
        # 删除测试文件
        os.unlink(test_file)
        print(f"✓ 清理测试文件")