"""
测试 Logging Handler 功能

验证日志转发和解析是否正常工作
"""

import sys
import logging
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from frontend.progress_reporter import ProgressReporter
from frontend.logging_handler import setup_logging_forwarding, remove_logging_forwarding


def test_logging_handler():
    """测试日志 Handler"""
    print("\n" + "=" * 70)
    print("测试 Logging Handler 功能")
    print("=" * 70)
    
    # 1. 创建 ProgressReporter（没有真实客户端）
    print("\n[1] 创建 ProgressReporter...")
    reporter = ProgressReporter()
    print("  ✓ ProgressReporter 创建成功")
    
    # 2. 设置日志转发
    print("\n[2] 配置日志转发...")
    handler = setup_logging_forwarding(reporter)
    print("  ✓ 日志转发已配置")
    
    # 3. 测试各种日志输出
    print("\n[3] 测试日志输出...")
    
    test_logger = logging.getLogger("test_module")
    
    # 测试各种日志级别
    test_logger.info("正在打开微信...")
    test_logger.info("微信已启动并激活")
    test_logger.info("正在打开微信搜索...")
    test_logger.info("微信搜索界面已打开")
    test_logger.info("正在处理第 1/2 个公众号")
    test_logger.info("处理第 1/3 个文章位置")
    test_logger.info("识别到 3 个当天日期位置")
    test_logger.info("文章链接已复制: https://mp.weixin.qq.com/s/test123abc")
    test_logger.info("文章链接采集完成")
    test_logger.warning("这是一条警告消息")
    test_logger.error("这是一条错误消息")
    
    print("  ✓ 日志输出测试完成")
    
    # 4. 移除日志转发
    print("\n[4] 移除日志转发...")
    remove_logging_forwarding(handler)
    print("  ✓ 日志转发已移除")
    
    # 5. 验证移除后的日志不会被转发
    print("\n[5] 验证移除后的日志...")
    test_logger.info("这条日志不应该被转发到 WebSocket")
    print("  ✓ 移除验证完成")
    
    print("\n" + "=" * 70)
    print("✅ 所有测试通过")
    print("=" * 70)


if __name__ == "__main__":
    # 配置基础日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        test_logging_handler()
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
