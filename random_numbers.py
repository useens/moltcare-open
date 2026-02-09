import random

# 生成100个随机数（0-1000之间）
random_numbers = [random.randint(0, 1000) for _ in range(100)]

print("=" * 50)
print("生成的100个随机数（未排序）:")
print("=" * 50)
print(random_numbers)

# 排序
sorted_numbers = sorted(random_numbers)

print("\n" + "=" * 50)
print("排序后的100个随机数:")
print("=" * 50)
print(sorted_numbers)

# 统计信息
print("\n" + "=" * 50)
print("统计信息:")
print("=" * 50)
print(f"最小值: {min(sorted_numbers)}")
print(f"最大值: {max(sorted_numbers)}")
print(f"平均值: {sum(sorted_numbers) / len(sorted_numbers):.2f}")
print(f"中位数: {sorted_numbers[len(sorted_numbers)//2]}")
