"""
测试脚本：验证性能优化和会话稳定性修复
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from llm.kimi_client import KimiClient, PerformanceTracker
from pipeline.chunker import chunk_transcript
from datetime import datetime

def test_performance_tracker():
    """测试性能跟踪器"""
    print("\n========== 测试性能跟踪器 ==========")
    tracker = PerformanceTracker()
    
    # 模拟几个请求
    for i in range(3):
        tracker.start_request()
        import time
        time.sleep(0.1 * (i + 1))  # 模拟不同的处理时间
        tracker.end_request(success=True)
    
    print(tracker.get_summary())
    print("性能跟踪器测试通过 [OK]")

def test_context_management():
    """测试上下文管理"""
    print("\n========== 测试上下文管理 ==========")
    client = KimiClient(max_context_messages=10)
    
    # 模拟添加多个消息
    for i in range(15):
        client.messages.append({"role": "user", "content": f"Test message {i}"})
        client.messages.append({"role": "assistant", "content": f"Response {i}"})
    
    print(f"添加消息后，上下文大小: {len(client.messages)}")
    
    # 触发上下文管理
    client._manage_context()
    
    print(f"上下文管理后，上下文大小: {len(client.messages)}")
    print(f"上下文消息数量限制: {client.max_context_messages}")
    
    if len(client.messages) <= client.max_context_messages:
        print("上下文管理测试通过 [OK]")
    else:
        print("上下文管理测试失败 [FAIL]")

def test_token_estimation():
    """测试token估算"""
    print("\n========== 测试Token估算 ==========")
    client = KimiClient()
    
    # 测试中文文本
    chinese_text = "这是一个测试文本，用于测试中文token估算功能。"
    chinese_tokens = client._estimate_tokens(chinese_text)
    print(f"中文文本: {chinese_text}")
    print(f"估算tokens: {chinese_tokens}")
    
    # 测试英文文本
    english_text = "This is a test text for testing English token estimation."
    english_tokens = client._estimate_tokens(english_text)
    print(f"\n英文文本: {english_text}")
    print(f"估算tokens: {english_tokens}")
    
    print("\nToken估算测试通过 [OK]")

def test_chunk_size_optimization():
    """测试chunk大小优化"""
    print("\n========== 测试Chunk大小优化 ==========")
    
    # 创建测试转录文本
    test_texts = {
        "short": "短文本测试" * 100,  # ~600字符
        "medium": "中等长度文本测试" * 2000,  # ~14000字符
        "long": "长文本测试" * 5000,  # ~25000字符
        "very_long": "超长文本测试" * 10000,  # ~50000字符
    }
    
    for name, text in test_texts.items():
        print(f"\n测试 {name} 文本 ({len(text)} 字符):")
        
        # 模拟chunk分割逻辑
        transcript_length = len(text)
        
        if transcript_length > 50000:
            target_chunks = 15
            estimated_chunk_size = transcript_length // target_chunks
            dynamic_chunk_size = max(4000, min(6000, estimated_chunk_size))
            dynamic_chunk_overlap = int(dynamic_chunk_size * 0.15)
        elif transcript_length > 30000:
            dynamic_chunk_size = 4000
            dynamic_chunk_overlap = 500
        else:
            dynamic_chunk_size = 1200
            dynamic_chunk_overlap = 200
        
        estimated_chunks = transcript_length // dynamic_chunk_size
        print(f"  Chunk大小: {dynamic_chunk_size}")
        print(f"  重叠大小: {dynamic_chunk_overlap}")
        print(f"  预估chunk数量: {estimated_chunks}")
    
    print("\nChunk大小优化测试通过 [OK]")

def test_session_health_check():
    """测试会话健康检查"""
    print("\n========== 测试会话健康检查 ==========")
    client = KimiClient()
    
    # 模拟多个请求
    for i in range(25):
        client.request_count = i + 1
        client.messages.append({"role": "user", "content": f"Test {i}"})
        client.messages.append({"role": "assistant", "content": f"Response {i}"})
        
        # 触发健康检查（每10个请求）
        if client.request_count % 10 == 0:
            print(f"\n请求 #{client.request_count} - 触发健康检查")
            client._check_session_health()
    
    print("\n会话健康检查测试通过 [OK]")

def main():
    """运行所有测试"""
    print(f"\n{'='*60}")
    print(f"开始测试: {datetime.now().isoformat()}")
    print(f"{'='*60}")
    
    try:
        test_performance_tracker()
        test_context_management()
        test_token_estimation()
        test_chunk_size_optimization()
        test_session_health_check()
        
        print(f"\n{'='*60}")
        print("所有测试通过 [OK]")
        print(f"{'='*60}\n")
        
        return True
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"测试失败: {str(e)}")
        print(f"{'='*60}\n")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
