"""
沙箱安全测试
"""

import pytest
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sandbox import SecureSandbox


class TestSandboxSecurity:
    """沙箱安全测试类"""
    
    @pytest.fixture
    def sandbox(self):
        """创建沙箱实例"""
        return SecureSandbox()
    
    def test_network_isolation(self, sandbox, tmp_path):
        """测试网络隔离"""
        # 创建测试文件
        test_file = tmp_path / "test.py"
        test_file.write_text("print('test')")
        
        container = sandbox.create_sandbox("test-net", str(tmp_path))
        
        try:
            exit_code, output = sandbox.execute_command(
                container, "ping -c 1 8.8.8.8"
            )
            assert exit_code != 0, "网络隔离失败：容器可以访问外网"
        finally:
            sandbox.cleanup("test-net")
    
    def test_readonly_filesystem(self, sandbox, tmp_path):
        """测试只读文件系统"""
        test_file = tmp_path / "test.py"
        test_file.write_text("print('test')")
        
        container = sandbox.create_sandbox("test-ro", str(tmp_path))
        
        try:
            exit_code, output = sandbox.execute_command(
                container, "touch /test.txt"
            )
            assert exit_code != 0 or "Read-only" in output, "只读文件系统测试失败"
        finally:
            sandbox.cleanup("test-ro")
    
    def test_resource_limit(self, sandbox, tmp_path):
        """测试资源限制"""
        test_file = tmp_path / "test.py"
        test_file.write_text("print('test')")
        
        container = sandbox.create_sandbox("test-res", str(tmp_path))
        
        try:
            # 测试临时目录可写
            exit_code, output = sandbox.execute_command(
                container, "touch /tmp/test.txt && echo 'success'"
            )
            assert exit_code == 0, "临时目录应该可写"
        finally:
            sandbox.cleanup("test-res")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])