---
title: "[Python/数学模型]给大忙人用的速通一：cvxpy和numpy"
published: 2026-04-27T19:29:23+08:00
updated: 2026-04-27T19:31:05+08:00
description: "梳理用 CVXPY 建立并求解优化问题的通用流程，同时记录 NumPy 的基础数据处理方法。"
tags: ["Python", "数学建模"]
category: "Python"
author: "Mem0rin"
sourceLink: "https://blog.csdn.net/2501_93882415/article/details/160565144"
draft: false
pinned: false
---

## 目录

- [一、cvxpy解决问题的框架](#一cvxpy解决问题的框架)
  - [读取数据](#读取数据)
  - [创建变量](#创建变量)
  - [设置约束条件](#设置约束条件)
  - [目标函数](#目标函数)
  - [求解问题](#求解问题)
  - [输出结果](#输出结果)
- [二、numpy的简单使用](#二numpy的简单使用)

本文依照我校期中考试进行简单梳理，主要内容包括：cvxpy从设置变量到解决问题输出结果的框架，numpy的简单使用，多种优化问题的限制条件的使用。

## 一、cvxpy解决问题的框架

主要框架是：读取数据->创建变量->设置约束条件->目标函数->求解问题->输出结果。

### 读取数据

可以采用的读取数据的方法有很多种，这边采用最通用的：

```python
# 读取输入
import sys
data = sys.stdin.read().strip().split()
# 处理可能的逗号分隔（如果输入有逗号，先替换为空格）
data = [item.replace(',', ' ') for item in data]
data = ' '.join(data).split()
# 现在 data 是一个字符串列表，包含所有数字

# 读取m，n
idx = 0;
```

这样我们把读取的数据转换成了字符串列表，读取数据的时候只需要不断移动 `idx`，并且用强制类型转换把数据转换成需要的类型即可。

### 创建变量

我们只考虑一阶和二阶的情况。

创建变量的时候我们使用的方法是 `cvxpy` 内置的函数 `cp.Variable`，一维的只需要传入整数即可，二位的需要用元组分别指定行数和列数，例如以下代码：

```python
import cvxpy as cp
# 创建一维变量
x = cp.Variable(n)

# 创建二维变量
X = cp.Variable((m, n))
```

与此同时我们还可以指定变量的类型，如 `boolean`， `nonneg` 等等，例如以下代码：

```python
# 创建一个非负变量
y = cp.Variable(nonneg=True)

# 创建一个布尔变量
z = cp.Variable(boolean=True)
```

如果没有指定类型则默认是连续变量。

### 设置约束条件

我们通过创建一个名为 `constraints` 的列表来存储约束条件，约束条件的设置主要是通过比较运算符来实现的，例如以下代码：

```python
x = cp.Variable(m)  # 创建一个变量
constraints = []
# 添加约束条件 x >= 0
constraints.append(x >= 0)
# 添加约束条件 x <= 10
constraints.append(x <= 10)

y = cp.Variable((n, n))  # 创建另一个变量
# 添加约束条件 y 的每行之和等于 1
constraints.append(cp.sum(y, axis=1) == 1)

# 添加约束条件 y 的每列之和等于 1
constraints.append(cp.sum(y, axis=0) == 1)

# 添加约束条件 y 的所有元素之和等于n
constraints.append(cp.sum(y) == n)
```

需要注意的是，cp.sum函数如果对二维变量使用时需要指定 `axis` 参数来确定求和的维度，`axis=0` 表示对列求和，`axis=1` 表示对行求和，返回的是各行或者各列之和组成的向量。

### 目标函数

目标函数的设置主要是通过 `cp.Minimize` 和 `cp.Maximize` 来实现的，例如 ∣∣Ax−b∣∣22||Ax - b||_2^2∣∣Ax−b∣∣22 就可以用以下代码来实现：

```python
# 第二行：b 的 m 个元素
b = np.array([float(data[idx + i]) for i in range(m)]); idx += m

# 接下来 m 行，每行 n 个元素，构造 A
A = np.zeros((m, n))
for i in range(m):
    for j in range(n):
        A[i, j] = float(data[idx + j])
    idx += n

# 构建 cvxpy 变量和问题
x = cp.Variable(n)
objective = cp.Minimize(cp.sum_squares(A @ x - b))
constraints = [0 <= x, x <= 1]
```

构造目标函数常用的函数有 `cp.sum_squares`， `cp.multiply`， `cp.sum` 等等。具体的使用可以看后面的具体题目。

### 求解问题

用 `cp.Problem` 来构建问题，传入目标函数和约束条件，然后调用 `solve` 方法来求解问题，例如以下代码：

```python
objective = cp.Minimize(cp.sum_squares(A @ x - b))
constraints = [0 <= x, x <= 1]

prob = cp.Problem(objective, constraints)
result = prob.solve()
```

得到的 `result` 就是目标函数的最优值，变量 `x.value` 就是最优解。

### 输出结果

通常需要保留小数点后两位，如果只需要输出最优值可以直接输出 `result`，如果需要输出最优解则需要输出 `x.value`，例如以下代码：

```python
print(f"{result:.2f}")  # 输出最优值，保留两位小数
print(f"{x.value}")  # 输出最优解
```

## 二、numpy的简单使用

在使用 `cvxpy` 之前我们需要先把输入的数据转换成 `numpy` 数组，这样才能方便地进行矩阵运算，例如以下代码：

```python
Performance = np.zeros((n, n))

for i in range(n):
    for j in range(n):
        Performance[i, j] = float(data[idx])
        idx += 1
```

这样我们就把输入的数据转换成了一个 n×nn \times nn×n 的矩阵。

或者用 `np.array` 把列表转换成 `numpy` 的数组，例如以下代码：

```python
# 读取一个长度为 n 的列表
lst = [float(data[idx + i]) for i in range(n)]
idx += n
# 转换成 numpy 数组
arr = np.array(lst)
```

还可以进行多项式拟合并从高到低返回多项式的系数：

```python
# 多项式拟合，返回从高次到低次的系数
coef = np.polyfit(x, y, n)

# 输出，保留两位小数
for c in coef:
    print(f"{c:.2f}")
```
