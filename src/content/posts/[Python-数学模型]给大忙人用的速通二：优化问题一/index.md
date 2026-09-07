---
title: "[Python/数学模型]给大忙人用的速通二：优化问题一"
published: 2026-04-27T20:45:58+08:00
updated: 2026-04-27T20:46:00+08:00
description: "用数学规划拆解运输、指派和销售点代理问题，分别说明变量、约束条件与目标函数的设置。"
tags: ["Python", "数学建模"]
category: "Python"
author: "Mem0rin"
sourceLink: "https://blog.csdn.net/2501_93882415/article/details/160566637"
draft: false
pinned: false
---

## 目录

- [运输问题](#运输问题)
- [指派问题](#指派问题)
- [销售点代理问题](#销售点代理问题)

## 运输问题

输入数据：每个仓库到各个路线的成本

变量：每条路径的运输量

约束条件：供应量和需求量

目标函数：总运输成本

关键点是供应量大于运输量大于需求量。

```
输入格式：
第一行两个数m,n
第2行到第m+1行 对应商品运价
第m+2行对应需求量
第m+3行对应存货量
输出格式：
精确到小数点后两位

eg.
6 8
6    2    6    7    4    2    5    9  
4    9    5    3    8    5    8    2  
5    2    1    9    7    4    3    3  
7    6    7    3    9    2    7    1  
2    3    9    5    7    2    6    5  
5    5    2    2    8    1    4    3  
35    37    22    32    41    32    43    38  
60  55  51  43  41  52 

664.00
```

```python
# 运输单价
cost = np.zeros((m, n))
for i in range(m):
    for j in range(n):
        cost[i, j] = float(data[idx + j])
    idx += n

# 客户需求量
demand = np.array([float(data[idx + i]) for i in range(n)]); idx += n

# 存量
supply = np.array([float(data[idx + i]) for i in range(m)]); idx += m

# 定义变量
x = cp.Variable((m, n),nonneg = True)

# 定义目标函数
objective = cp.Minimize(cp.sum(cp.multiply(cost, x)))

# 定义约束条件
constraints = [
    cp.sum(x, axis = 1) <= supply,
    cp.sum(x, axis = 0) >= demand
]

# 求解问题
prob = cp.Problem(objective, constraints)
result = prob.solve()
```

## 指派问题

输入数据：工人的绩效

变量：工人的工作分配

约束条件：每个工人只能分配一个工作，每个工作只能分配给一个工人

目标函数：总绩效最大化

```
输入格式:
第1行输入一个数，n,  表示方阵的大小

第2行到n+1行，表示n*n的矩阵

输出格式:
输出最优绩效，精度控制在小数点后两位。

输入示例：
5
100,0,100,267,100
400,200,100,153,33
200,800,100,99,33
200,0,100,451,34
100,0,600,30,800

输出：
2551.00
```

```python
Performance = np.zeros((n, n))

for i in range(n):
    for j in range(n):
        Performance[i, j] = float(data[idx])
        idx += 1

# 指派变量，x[i, j] 表示第 i 个人是否做第 j 项工作
x = cp.Variable((n, n))

constraints = [
    x >= 0,
    x <= 1,
    cp.sum(x, axis=1) == 1,  # 每个人完成一个工作
    cp.sum(x, axis=0) == 1   # 每个工作只能安排一个人
]

objective = cp.Maximize(cp.sum(cp.multiply(Performance, x)))
```

## 销售点代理问题

输入数据：相邻矩阵和每个销售点的利润

变量：每个销售点是否被代理

约束条件：每个社区只能设立一个代理点，且只能供应到相邻社区

目标函数：总利润最大化

```
输入格式:

第1行输入一个树，n,  表示方阵的大小

第2行到n+1行，表示n*n的相邻矩阵

最后一行表示人数

输出格式:
输出最佳人数，最终结果为整数。

输入示例：
7
0,1,1,0,0,0,0
0,0,1,1,1,0,0
0,0,0,1,0,0,0
0,0,0,0,1,1,1
0,0,0,0,0,1,0
0,0,0,0,0,0,1
0,0,0,0,0,0,0
34, 29, 42, 21, 56, 18, 71

输出示例：
177
```

```python
A = np.zeros((n, n), dtype=int)
for i in range(n):
    for j in range(n):
        A[i, j] = int(data[idx])
        idx += 1

num = np.array([int(data[idx + i]) for i in range(n)])

# 原矩阵只给了上三角形式，所以转成无向相邻矩阵
Adj = ((A + A.T) > 0).astype(int)

# 主对角线设为 0，因为 t[i, j] 只表示“供应相邻社区”，不表示供应本区
np.fill_diagonal(Adj, 0)

# t[i, j] = 1 表示在 i 区建点，并且供应相邻的 j 区
t = cp.Variable((n, n), boolean=True)

# z[j] = 1 表示第 j 个社区被覆盖
# 这里 z 不需要设置 boolean，连续变量即可
z = cp.Variable(n)

# 第 i 行有 1，表示第 i 个社区建了代理点
selected = cp.sum(t, axis=1)

# 第 j 列有 1，表示第 j 个社区被其他代理点供应
served_by_neighbor = cp.sum(t, axis=0)

# 社区 j 被覆盖的次数：
# 自己建点覆盖一次 + 被邻居供应覆盖一次
covered = selected + served_by_neighbor

constraints = [
    # 一共建立两个代理点
    cp.sum(t) == 2,

    # 每个社区最多建立一个代理点
    cp.sum(t, axis=1) <= 1,

    # 只能供应相邻社区
    t <= Adj,

    # 覆盖变量约束
    z >= 0,
    z <= 1,
    z <= covered
]
```
