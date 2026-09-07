---
title: "前缀和：哈希计数、目标和与同余分组"
published: 2026-08-14T13:59:55+08:00
updated: 2026-08-14T13:59:57+08:00
description: "讲解如何用前缀和配合哈希计数处理目标和与整除问题，重点梳理初始状态、更新顺序和同余分组。"
tags: ["算法", "数据结构"]
category: "算法"
author: "Mem0rin"
sourceLink: "https://blog.csdn.net/2501_93882415/article/details/163753346"
draft: false
pinned: false
---

## 目录

- [一、子数组与前缀和](#一子数组与前缀和)
- [二、出现次数](#二出现次数)
- [三、初始化与更新顺序](#三初始化与更新顺序)
- [四、同余分组](#四同余分组)

前缀和不只可以保存下来回答区间查询，还可以配合哈希表统计子数组。关键在于把一段连续区间改写成两个前缀和之差，再统计符合条件的左端点有  
 多少个。

## 一、子数组与前缀和

[LeetCode 560. 和为 K 的子数组](https://leetcode.cn/problems/subarray-sum-equals-k/)

设 `P[i]` 表示前 `i` 个元素的和，那么区间 `( j, i ]` 的元素和为：

```text
P[i] - P[j]
```

如果这段子数组的和等于 `k`，就有：

```text
P[j] = P[i] - k
```

遍历到 `i` 时，只要知道前面出现过多少个值为 `P[i] - k` 的前缀和，就知道有多少个以当前位置结尾、和为 `k` 的子数组。这样就通过前缀和建立了递推关系。

## 二、出现次数

这里仍然会计算每个位置对应的前缀和，只是没有把所有前缀和依次存进数组。题目只关心符合条件的子数组数量，不需要知道每个前缀和出现在哪些位置，因此可以用哈希表记录“前缀和 → 出现次数”。

遍历数组时维护当前前缀和 `sum`：

```java
sum += x;
count += hash.getOrDefault(sum - k, 0);
hash.put(sum, hash.getOrDefault(sum, 0) + 1);
```

哈希表里每一次匹配，都对应一个可以与当前前缀组成目标子数组的左端点。

## 三、初始化与更新顺序

查找和更新谁先执行？正确顺序是先查找，再更新当前前缀和。查找范围只包含当前位置之前的前缀；如果 `k == 0` 时先更新，当前前缀和会立刻匹配自己，相当于把长度为零的区间也算了进去。

还有一个容易漏掉的前缀：`P[0] = 0`。它表示还没有取任何元素时的前缀和，需要预先写入：

```java
hash.put(0, 1);
```

例如数组为 `[1, 1]`、`k = 2`。遍历到第二个元素时 `sum = 2`，查询 `sum - k = 0`，初始前缀正好贡献一个答案。没有这次初始化会得到 `0`，正确结果是 `1`。

完整代码如下：

```java
import java.util.HashMap;
import java.util.Map;

class Solution {
    public int subarraySum(int[] nums, int k) {
        Map<Integer, Integer> hash = new HashMap<>();
        int sum = 0;
        int count = 0;
        hash.put(0, 1);

        for (int x : nums) {
            sum += x;
            count += hash.getOrDefault(sum - k, 0);
            hash.put(sum, hash.getOrDefault(sum, 0) + 1);
        }
        return count;
    }
}
```

## 四、同余分组

[LeetCode 974. 和可被 K 整除的子数组](https://leetcode.cn/problems/subarray-sums-divisible-by-k/)

如果两个前缀和除以 `k` 后属于同一个余数类，那么它们的差就可以被 `k` 整除。于是可以按照余数分组，从统计某个前缀和的出现次数，迁移到统计某个余数类的出现次数。

机械地把减法改成取模还不够。Java 的 `%` 保留被除数的符号，例如 `-1 % 2 == -1`；数学上 `-1` 和 `1` 属于模 `2` 的同一个余数类，却会在哈希表中落入两个键。可以把余数统一到 `[0, k - 1]`：

```java
int remainder = (sum % k + k) % k;
```

其余统计过程与上一题相同：

```java
import java.util.HashMap;
import java.util.Map;

class Solution {
    public int subarraysDivByK(int[] nums, int k) {
        Map<Integer, Integer> hash = new HashMap<>();
        int sum = 0;
        int count = 0;
        hash.put(0, 1);

        for (int x : nums) {
            sum += x;
            int remainder = (sum % k + k) % k;
            count += hash.getOrDefault(remainder, 0);
            hash.put(remainder, hash.getOrDefault(remainder, 0) + 1);
        }
        return count;
    }
}
```

两道题都只遍历数组一次，时间复杂度为 `O(n)`，哈希表最多记录 `O(n)` 个键，空间复杂度为 `O(n)`。
