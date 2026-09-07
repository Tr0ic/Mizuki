---
title: "[Python/数学模型]给大忙人看的速通三——图论优化"
published: 2026-04-29T16:00:50+08:00
updated: 2026-04-29T16:00:53+08:00
description: "用数学规划描述最大流、旅行商、最短路径和最小生成树问题，并给出相应的 Python 建模思路。"
tags: ["Python", "数学建模"]
category: "Python"
author: "Mem0rin"
sourceLink: "https://blog.csdn.net/2501_93882415/article/details/160629160"
draft: false
pinned: false
---

## 目录

- [最大流问题](#最大流问题)
- [旅行商问题](#旅行商问题)
- [最短路径问题](#最短路径问题)
- [最小生成树问题](#最小生成树问题)

## 最大流问题

输入数据：网络的容量矩阵

变量：每条边的流量

约束条件：流量不能超过边的容量，且满足流量守恒

目标函数：最大化从源点到汇点的流量

```
输入格式:
第1行包含2个整数：n表示农田数量，m表示水管数量。
接下来m行，每行包含3个整数：a, b, c，表示从农田a到农田b有一条有向水管，其流量限制为c。农田的编号从1到n。

输出格式:
输出一个整数，表示从1号农田到n号农田的最大流量。

输入示例：
4 5
1 2 10
1 3 5
2 3 5
2 4 20
3 4 5

输出示例：
15
```

代码如下：

```python
# 读入
n, m = map(int, input().split())
edges = []
for _ in range(m):
    a, b, c = map(int, input().split())
    edges.append((a, b, c))

# 决策变量：每条边上的流量
x = cp.Variable(m)

constraints = []

# 1. 容量约束
for i, (a, b, c) in enumerate(edges):
    constraints.append(x[i] >= 0)
    constraints.append(x[i] <= c)

# 2. 中间点流量守恒
for k in range(2, n):   # 2 ~ n-1
    inflow = 0
    outflow = 0
    for i, (a, b, c) in enumerate(edges):
        if b == k:
            inflow += x[i]
        if a == k:
            outflow += x[i]
    constraints.append(inflow == outflow)

# 3. 目标：最大化源点1的净流出
source_out = 0
source_in = 0
for i, (a, b, c) in enumerate(edges):
    if a == 1:
        source_out += x[i]
    if b == 1:
        source_in += x[i]

objective = cp.Maximize(source_out - source_in)

# 求解
prob = cp.Problem(objective, constraints)
prob.solve()

# 输出结果
print(round(prob.value))
```

## 旅行商问题

输入数据：城市之间的距离矩阵

变量：每条路径是否被选中

约束条件：每个城市只能访问一次，且形成一个闭环

目标函数：最小化总旅行距离

因为旅行商问题的结果是一个闭环，因此我们不需要考虑第一个城市是什么，指定第一个城市作为出发点就可以了。

```
输入格式：
第1行：一个整数 n，表示城市数量。
接下来的n行：每行包含n个整数，表示城市之间的距离矩阵。

输出格式：
输出一个整数，表示总行程的最短距离。

输入示例：
5
0 1050 1420 1270 460
1050 0 1200 240 1100
1420 1200 0 1950 1760
1270 240 1950 0 1270
460 1100 1760 1270 0

输出示例：
4590
```

代码如下：

```python
# ---------- 决策变量 ----------
# x[i, j] = 1 表示从 i 到 j
x = cp.Variable((n, n), boolean=True)

# MTZ 顺序变量
u = cp.Variable(n)

constraints = []

# ---------- 基本约束 ----------
# 不允许自己到自己
constraints.append(cp.diag(x) == 0)

# 每个城市恰好出发一次
for i in range(n):
    constraints.append(cp.sum(x[i, :]) == 1)

# 每个城市恰好到达一次
for j in range(n):
    constraints.append(cp.sum(x[:, j]) == 1)

# ---------- MTZ 子回路消除 ----------
# 固定第0个城市作为起点
constraints.append(u[0] == 0)

for i in range(1, n):
    constraints.append(u[i] >= 1)
    constraints.append(u[i] <= n - 1)

for i in range(1, n):
    for j in range(1, n):
        if i != j:
            constraints.append(u[i] - u[j] + n * x[i, j] <= n - 1)  # 如果选定了 i->j，此时x[i, j] = 1，则 u[i] < u[j]

# ---------- 目标函数 ----------
objective = cp.Minimize(cp.sum(cp.multiply(D, x)))
```

## 最短路径问题

输入数据：图的邻接矩阵和边权

变量：每条边是否被选中

约束条件：形成一条从源点到汇点的路径

目标函数：最小化路径总权重

```
输入格式:

第1行包含3个整数：n表示城市数量，m表示道路数量，k表示查询数量。

接下来m行，每行包含3个整数：a, b, t，表示城市a和城市b之间有一条双向道路，行驶这条道路需要t时间。城市的编号从1到n。

接下来k行，每行包含2个整数：s, d，表示一次查询，从城市s出发到达城市d。

输出格式：

输出k行，每行包含一个整数，表示对应查询的最短时间。

如果无法到达目标城市，输出-1。

输入示例：
4 5 2
1 2 3
1 3 1
2 4 2
3 4 4
2 3 5
1 4
2 4

输出示例：
5
2
```

代码如下：

```python
input = sys.stdin.readline

def solve_one_query(n, edges, s, t):
    # 无向边拆成有向边
    arcs = []
    cost = []
    for a, b, w in edges:
        arcs.append((a, b))
        cost.append(w)
        arcs.append((b, a))
        cost.append(w)

    m = len(arcs)

    # 决策变量：是否选第i条弧 0或者1
    x = cp.Variable(m, boolean=True)

    constraints = []

    # 流量平衡约束
    for i in range(1, n + 1):
        outflow = 0
        inflow = 0
        for e, (u, v) in enumerate(arcs):
            if u == i:
                outflow += x[e]   # 这条边被选作路径的起点
            if v == i:
                inflow += x[e]    # 这条边被选为路径的终点

        if i == s:
            constraints.append(outflow - inflow == 1) # 起点有后继没有前驱
        elif i == t:
            constraints.append(outflow - inflow == -1) # 终点有前驱没有后继
        else:
            constraints.append(outflow - inflow == 0) # 中间的点必定有前驱和后继

    # 目标函数
    objective = cp.Minimize(sum(cost[e] * x[e] for e in range(m)))

    # 建立问题
    prob = cp.Problem(objective, constraints)

    # 求解
    prob.solve()

    return int(round(prob.value))


# 主程序
n, m, k = map(int, input().split())
edges = []

for _ in range(m):
    a, b, w = map(int, input().split())
    edges.append((a, b, w))

queries = [tuple(map(int, input().split())) for _ in range(k)]

for s, t in queries:
    print(solve_one_query(n, edges, s, t))
```

## 最小生成树问题

输入数据：图的邻接矩阵和边权

变量：每条边是否被选中

约束条件：选中的边形成一个连接所有节点的树，并且这个树内部的所有子集的边数都不能超过子集节点数减一

目标函数：最小化选中边的总权重

```
输入格式:
第1行包含2个整数：n表示城市数量，m表示现有道路数量。
接下来m行，每行包含3个整数：a, b, c，表示城市a和城市b之间有一条现有道路，升级成本为c。城市的编号从1到n。

输出格式:
输出一个整数，表示连接所有城市的最低成本。

输入示例：
6 9
1 2 3
1 3 1
1 4 2
2 3 2
2 5 3
3 4 3
3 6 5
4 5 6
5 6 2

输出示例：
10
```

代码如下：

```python
import cvxpy as cp
import itertools

n, m = map(int, input().split())

edge = []
cost = []

for _ in range(m):
    a, b, c = map(int, input().split())
    edge.append((a, b))
    cost.append(c)

x = cp.Variable(m, boolean = True)

constraints = []

constraints.append(cp.sum(x) == n - 1)

nodes = list(range(1, n + 1))

for r in range(2, n):   # 子集大小 2 到 n-1
    for S in itertools.combinations(nodes, r):
        S = set(S)

        idx = []
        for e, (u, v) in enumerate(edge):
            if u in S and v in S:
                idx.append(e)

        if idx:
            constraints.append(cp.sum(x[idx]) <= len(S) - 1)

for i in range(m):
    constraints.append(x[i] <= 1)
    constraints.append(x[i] >= 0)

objective = cp.Minimize(cp.sum(cp.multiply(cost, x)))

prob = cp.Problem(objective, constraints)
prob.solve()

print(int(prob.value));
```
