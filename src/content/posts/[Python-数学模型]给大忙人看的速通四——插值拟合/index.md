---
title: "[Python/数学模型]给大忙人看的速通四——插值拟合"
published: 2026-04-29T16:37:09+08:00
updated: 2026-04-29T16:37:12+08:00
description: "整理 SciPy 中一维、二维插值和多项式拟合的基本用法，说明输入数据、方法选择与结果获取方式。"
tags: ["Python", "数学建模"]
category: "Python"
author: "Mem0rin"
sourceLink: "https://blog.csdn.net/2501_93882415/article/details/160630501"
draft: false
pinned: false
---

## 目录

- [插值问题](#插值问题)
  - [一维插值问题](#一维插值问题)
  - [二维插值问题](#二维插值问题)
  - [多项式拟合](#多项式拟合)

## 插值问题

### 一维插值问题

给定一些数据点 
(
x
i
,
y
i
)
(x_i, y_i)
(xi,yi)，我们需要预测一个新的 
x
x
x 值对应的 
y
y
y 值。我们可以使用 `scipy.interpolate` 模块中的 `interp1d` 函数来进行一维插值，例如以下代码：

```python
import numpy as np
from scipy.interpolate import interp1d

n = int(input().strip())

x = []
y = []

for i in range(n):
    humidity, yield_value = map(float, input().split())
    x.append(humidity)
    y.append(yield_value)

m = int(input().strip())

x = np.array(x, dtype = float)
y = np.array(y, dtype = float)

f = interp1d(x, y)

for _ in range(m):
    query = float(input().strip())// 需要预测的数据进行插值查询
    result = f(query)
    print(f"{float(result):.2f}")
```

### 二维插值问题

可以使用 `scipy.interpolate` 模块中的 `griddata` 函数来进行二维插值。  
 `griddata` 函数的参数包括：已知数据点的坐标 `p`，已知数据点的值 `t`，需要预测的数据点的坐标 `xi`，以及插值方法 `method`（如 ‘linear’、‘nearest’、‘cubic’ 等）。其中坐标是用二维列表储存的，例如以下代码：

```python
from scipy.interpolate import griddata
import numpy as np

n, m = map(int, input().split())

p = []
t = []
for _ in range(n):
    longitude, latitude, temperature = map(float, input().split())
    p.append([longitude, latitude])
    t.append(temperature)

p = np.array(p)
t = np.array(t)

xi = []
for _ in range(m):
    l1, l2 = map(float, input().split())
    xi.append([l1, l2])
xi = np.array(xi)
    
# 进行二维线性插值
result = griddata(p, t, xi, method='linear')

# 输出结果，保留两位小数
for temp in result:
    print(f"{temp:.2f}")
```

### 多项式拟合

如果要返回多项式拟合之后的系数，可以使用 `numpy.polyfit` 函数，例如以下代码：

```python
import numpy as np

m, n = map(int, input().split())

x = []
y = []

for _ in range(m):
    time, temp = map(float, input().split())
    x.append(time)
    y.append(temp)
# 多项式拟合，返回从高次到低次的系数
coef = np.polyfit(x, y, n)

# 输出，保留两位小数
for c in coef:
    print(f"{c:.2f}")
```
