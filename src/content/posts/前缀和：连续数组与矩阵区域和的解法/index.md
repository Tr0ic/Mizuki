---
title: "前缀和：连续数组与矩阵区域和的解法"
published: 2026-08-16T13:27:13+08:00
updated: 2026-08-16T17:52:46+08:00
description: "文章目录"
tags: ["算法", "数据结构"]
category: "算法"
author: "Mem0rin"
sourceLink: "https://zhuanlan.zhihu.com/p/2072312355367788723"
draft: false
pinned: false
---

## 目录

- [一、连续数组 -> 个数差](#一连续数组-个数差)
- [二、最早位置](#二最早位置)
- [三、二维前缀和](#三二维前缀和)
- [四、矩形边界](#四矩形边界)

## 一、连续数组 -> 个数差

[LeetCode 525. 连续数组](https://leetcode.cn/problems/contiguous-array/)

常见方法是把 `0` 看成 `-1`，于是 0 和 1 数量相同的子数组就变成了“和为 0 的子数组”。它的底色仍然是[和为 K 的子数组](https://leetcode.cn/problems/subarray-sum-equals-k/)中的前缀差。

不过，把 `0` 看成 `-1` 的转换在第一次遇到时有些突然。那么，有没有更平凡的理解方法？可以直接维护“1 的数量减去 0 的数量”，把这个差值当作前缀状态。

如果下标 `i` 和更早位置的差值相同，说明两者之间新增的 0 和 1 数量相等。这样就不必改动数组，只需要不断更新差值：

```java
difference += nums[i] == 1 ? 1 : -1;
```

这两种写法计算的是同一个状态，只是观察角度不同。

## 二、最早位置

哈希表记录“差值 → 最早出现位置”。当相同差值再次出现时，当前下标减去最早位置，就是一个 0 和 1 数量相同的连续子数组长度。

这里为什么只保存最早位置？题目要求最长长度，同一个差值对应的位置越靠前，与当前下标形成的区间就越长。因此差值第一次出现后不再更新位置。

初始值 `firstIndex.put(0, -1)` 表示遍历开始前差值为 0。这样一来，如果从下标 0 开始的前缀中 0 和 1 数量相同，也可以直接算出正确长度。

```text
import java.util.HashMap;
import java.util.Map;

class Solution {
    public int findMaxLength(int[] nums) {
        Map<Integer, Integer> firstIndex = new HashMap<>();
        firstIndex.put(0, -1);

        int difference = 0;
        int maxLength = 0;
        for (int i = 0; i < nums.length; i++) {
            difference += nums[i] == 1 ? 1 : -1;
            if (firstIndex.containsKey(difference)) {
                maxLength = Math.max(maxLength, i - firstIndex.get(difference));
            } else {
                firstIndex.put(difference, i);
            }
        }
        return maxLength;
    }
}
```

数组只遍历一次，时间复杂度为 `O(n)`，哈希表的空间复杂度为 `O(n)`。

## 三、二维前缀和

[LeetCode 1314. 矩阵区域和](https://leetcode.cn/problems/matrix-block-sum/)

这道题是二维前缀和的直接应用。令 `prefix[i][j]` 表示原矩阵中左上角到 `(i - 1, j - 1)` 的区域和，并在上方和左侧各补一行 0、一列 0，构造公式为：

```text
prefix[i + 1][j + 1]
= prefix[i][j + 1] + prefix[i + 1][j]
 - prefix[i][j] + mat[i][j]
```

补出的 0 边界可以统一矩形求和公式，查询贴着矩阵上边或左边时也不需要额外分支。

## 四、矩形边界

以 `(i, j)` 为中心、距离不超过 `k` 的区域可能越过矩阵边缘，因此需要同时裁剪四个边界：

```text
int x1 = Math.max(0, i - k);
int y1 = Math.max(0, j - k);
int x2 = Math.min(m - 1, i + k);
int y2 = Math.min(n - 1, j + k);
```

得到左上角 `(x1, y1)` 和右下角 `(x2, y2)` 后，用二维前缀和完成一次容斥：

```text
prefix[x2 + 1][y2 + 1]
- prefix[x1][y2 + 1]
- prefix[x2 + 1][y1]
+ prefix[x1][y1]
```

完整代码如下：

```text
class Solution {
    public int[][] matrixBlockSum(int[][] mat, int k) {
        int m = mat.length;
        int n = mat[0].length;
        int[][] answer = new int[m][n];
        int[][] prefix = new int[m + 1][n + 1];

        for (int i = 0; i < m; i++) {
            for (int j = 0; j < n; j++) {
                prefix[i + 1][j + 1] = prefix[i][j + 1]
                        + prefix[i + 1][j] - prefix[i][j] + mat[i][j];
            }
        }

        for (int i = 0; i < m; i++) {
            for (int j = 0; j < n; j++) {
                int x1 = Math.max(0, i - k);
                int y1 = Math.max(0, j - k);
                int x2 = Math.min(m - 1, i + k);
                int y2 = Math.min(n - 1, j + k);
                answer[i][j] = prefix[x2 + 1][y2 + 1]
                        - prefix[x1][y2 + 1] - prefix[x2 + 1][y1]
                        + prefix[x1][y1];
            }
        }
        return answer;
    }
}
```

构造前缀和与生成答案都需要遍历整个矩阵，时间复杂度为 `O(mn)`；前缀和数组的额外空间复杂度为 `O(mn)`。
