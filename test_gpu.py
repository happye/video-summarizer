import torch

# 检查CUDA是否可用
print(f"CUDA available: {torch.cuda.is_available()}")

if torch.cuda.is_available():
    # 打印GPU设备信息
    print(f"GPU device count: {torch.cuda.device_count()}")
    print(f"GPU device name: {torch.cuda.get_device_name(0)}")
    print(f"GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
    
    # 测试GPU计算
    x = torch.randn(1000, 1000).to('cuda')
    y = torch.randn(1000, 1000).to('cuda')
    z = torch.matmul(x, y)
    print(f"GPU computation successful: {z.shape}")
else:
    print("No GPU available")
