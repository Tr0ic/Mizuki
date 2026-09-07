---
title: "前缀和：中心下标与数组乘积"
published: 2026-08-10T18:39:46+08:00
updated: 2026-08-10T18:39:49+08:00
description: "从左右两侧信息的复用出发，分别用前缀和寻找中心下标、用前后缀积计算除自身外的数组乘积。"
tags: ["算法", "数据结构"]
category: "算法"
author: "Mem0rin"
sourceLink: "https://blog.csdn.net/2501_93882415/article/details/163643612"
draft: false
pinned: false
---

## 目录

- [一、左右信息的统一视角](#一左右信息的统一视角)
- [二、寻找数组的中心下标](#二寻找数组的中心下标)
- [三、除了自身以外数组的乘积](#三除了自身以外数组的乘积)

## 一、左右信息的统一视角

对于下标 `i`，可以把数组拆成三部分：

```text
[0, i) + nums[i] + (i, n)
```

中心下标比较左右两侧的和；除自身以外数组的乘积则把左右两侧的乘积相乘。两题的共同点是都不需要在处理每个 `i` 时重新扫描左右区间。

## 二、寻找数组的中心下标

[LeetCode 724. 寻找数组的中心下标](https://leetcode.cn/problems/find-pivot-index/)

设 `dp[i]` 表示下标 `i` 左侧所有元素的和，那么 `dp[nums.length]` 就是整个数组的总和。

如果 `i` 是中心下标，则有：

```text
左侧和 = 右侧和
dp[i] = dp[nums.length] - dp[i] - nums[i]
```

移项后可以直接判断：

```text
dp[i] * 2 + nums[i] == dp[nums.length]
```

这样只需要一个前缀和数组，不必再建立后缀和数组。代码从左向右检查，因此找到的第一个结果自然是最靠左的中心下标。

```java
class Solution {
    public int pivotIndex(int[] nums) {
        long[] dp = new long[nums.length + 1];
        for (int i = 1; i < nums.length + 1; i++) {
            dp[i] = dp[i - 1] + nums[i - 1];
        }

        for (int i = 0; i < nums.length; i++) {
            if (dp[i] * 2 + nums[i] == dp[nums.length]) {
                return i;
            }
        }
        return -1;
    }
}
```

时间复杂度为 `O(n)`，空间复杂度为 `O(n)`。按照本题约束，`int` 足以保存总和；这里使用 `long` 可以降低代码对数值范围的依赖。

## 三、除了自身以外数组的乘积

[LeetCode 238. 除了自身以外数组的乘积](https://leetcode.cn/problems/product-of-array-except-self/)

如果先求全部元素的乘积，再除以 `nums[i]`，遇到 `0` 时就无法处理，而且题目本身也要求不使用除法。可以分别保存左侧前缀积和右侧后缀积：

- `dpleft[i]`：下标 `0` 到 `i - 1` 的元素乘积；
- `dpright[i]`：下标 `i` 到 `len - 1` 的元素乘积。

因此，下标 `i` 的答案为：

```text
ret[i] = dpleft[i] * dpright[i + 1]
```

数组两端没有元素的一侧按乘法单位元 `1` 处理，所以初始化 `dpleft[0] = 1`、`dpright[len] = 1`。

```java
class Solution {
    public int[] productExceptSelf(int[] nums) {
        int len = nums.length;
        int[] dpleft = new int[len + 1];
        int[] dpright = new int[len + 1];

        dpleft[0] = 1;
        dpright[len] = 1;
        for (int i = 0; i < len; i++) {
            dpleft[i + 1] = dpleft[i] * nums[i];
        }
        for (int i = len - 1; i >= 0; i--) {
            dpright[i] = dpright[i + 1] * nums[i];
        }

        int[] ret = new int[len];
        for (int i = 0; i < len; i++) {
            ret[i] = dpleft[i] * dpright[i + 1];
        }
        return ret;
    }
}
```

题目保证相关前缀积、后缀积与答案都在 32 位整数范围内，因此可以使用 `int[]`。时间复杂度为 `O(n)`，额外空间复杂度为 `O(n)`。
