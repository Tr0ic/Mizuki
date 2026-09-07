---
title: "前缀和：一维与二维"
published: 2026-08-08T22:29:06+08:00
updated: 2026-08-08T22:29:08+08:00
description: "本质上有动态规划的思想。"
tags: ["算法", "数据结构"]
category: "算法"
author: "Mem0rin"
sourceLink: "https://blog.csdn.net/2501_93882415/article/details/163595533"
draft: false
pinned: false
---

## 目录

- [一、一维前缀和](#一一维前缀和)
- [二、二维前缀和](#二二维前缀和)
- [三、零边界](#三零边界)

本质上有动态规划的思想。

## 一、一维前缀和

[牛客 DP34.【模板】前缀和](https://www.nowcoder.com/practice/acead2f4c28c401889915da98ecdc6bf)

设 `dp[i]` 表示数组前 `i` 个元素之和，并额外定义 `dp[0] = 0`：

```text
dp[i] = dp[i - 1] + arr[i]
```

查询闭区间 `[l, r]` 时，`dp[r]` 包含第 `1` 个到第 `r` 个元素，再减去第 `1` 个到第 `l - 1` 个元素：

```text
sum(l, r) = dp[r] - dp[l - 1]
```

代码中的数组名虽然是 `dp`，但它保存的是预处理得到的前缀和，不是动态规划中的最优子结构结果。

```java
import java.util.Scanner;

public class Main {
    public static void main(String[] args) {
        Scanner in = new Scanner(System.in);
        int n = in.nextInt();
        int q = in.nextInt();
        int[] arr = new int[n + 1];
        long[] dp = new long[n + 1];
        for (int i = 1; i < n + 1; i++) {
            arr[i] = in.nextInt();
            dp[i] = dp[i - 1] + arr[i];
        }

        while (in.hasNextInt()) {
            int a = in.nextInt();
            int b = in.nextInt();
            System.out.println(dp[b] - dp[a - 1]);
        }
    }
}
```

题目中的元素绝对值可达 `10^9`，区间和可能超过 `int` 范围，因此前缀和数组使用 `long[]`。

## 二、二维前缀和

[牛客 DP35.【模板】二维前缀和](https://www.nowcoder.com/practice/99eb8040d116414ea3296467ce81cbbc)

设 `dp[i][j]` 表示左上角 `(1, 1)` 到右下角 `(i, j)` 这一整块矩形的元素和。构造时先相加上方矩形与左侧矩形，但它们重复计算了左上角重叠区域，因此需要减去一次，再加上当前元素：

```text
dp[i][j] = dp[i - 1][j] + dp[i][j - 1]
         - dp[i - 1][j - 1] + arr[i][j]
```

查询左上角 `(x1, y1)` 到右下角 `(x2, y2)` 的子矩形时，同样使用容斥：

```text
sum = dp[x2][y2] - dp[x1 - 1][y2]
    - dp[x2][y1 - 1] + dp[x1 - 1][y1 - 1]
```

前两次减法去掉目标矩形上方与左侧的区域，但左上角区域被减了两次，所以最后要补回一次。

```java
import java.util.Scanner;

public class Main {
    public static void main(String[] args) {
        Scanner in = new Scanner(System.in);
        int n = in.nextInt();
        int m = in.nextInt();
        int q = in.nextInt();

        int[][] arr = new int[n + 1][m + 1];
        long[][] dp = new long[n + 1][m + 1];

        for (int i = 1; i < n + 1; i++) {
            for (int j = 1; j < m + 1; j++) {
                arr[i][j] = in.nextInt();
                dp[i][j] = dp[i - 1][j] + dp[i][j - 1]
                        - dp[i - 1][j - 1] + arr[i][j];
            }
        }

        while (in.hasNextInt()) {
            int x1 = in.nextInt();
            int y1 = in.nextInt();
            int x2 = in.nextInt();
            int y2 = in.nextInt();
            System.out.println(dp[x2][y2] - dp[x1 - 1][y2]
                    - dp[x2][y1 - 1] + dp[x1 - 1][y1 - 1]);
        }
    }
}
```

## 三、零边界

为什么要把原数组向后平移一位？如果一维前缀和直接把 `dp[0]` 作为第一个值不是更符合直觉吗？

但是这样我们在实操的时候会遇到许多不便之处，往往需要繁杂的分类讨论，因此我们补出值为 `0` 的边界，用来统一公式。

例如查询从第 `1` 个元素开始第 `1` 个元素结束的区间时，公式会访问 `dp[1 - 1]`，也就是 `dp[0]`。二维前缀和同理：当查询区域贴着上边界或左边界时，公式会访问第 `0` 行或第 `0` 列。预留零边界后，不需要为这些情况额外分类，也不会出现负数下标，从而我们花费了少量的空间换来了简洁的代码，优雅的思路和性能的提升。
