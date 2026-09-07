---
title: "算法每日一题：数组分区与指针推进"
published: 2026-08-18T13:06:52+08:00
updated: 2026-08-18T13:06:52+08:00
description: "颜色分类只有 0、1、2 三种值，直接排序当然能得到结果，但题目要求不使用库内置排序，并尽量只扫描一遍。要满足这个限制，可以把数组划成几个已经确定的区域，再不断缩短待处理区域。"
tags: ["算法", "数据结构"]
category: "算法"
author: "Mem0rin"
sourceLink: "https://zhuanlan.zhihu.com/p/2073032285104911762"
draft: false
pinned: false
---

## 目录

- [一、四个区域](#一四个区域)
- [二、快排的分区思路](#二快排的分区思路)
- [三、错误的统一推进](#三错误的统一推进)
- [四、交换后的判断](#四交换后的判断)

颜色分类只有 `0、1、2` 三种值，直接排序当然能得到结果，但题目要求不使用库内置排序，并尽量只扫描一遍。要满足这个限制，可以把数组划成几个已经确定的区域，再不断缩短待处理区域。

## 一、四个区域

[LeetCode 75. 颜色分类](https://leetcode.cn/problems/sort-colors/)

使用 `left、current、right` 三个指针，把数组分成四个部分：

| 区间 | 含义 |
| --- | --- |
| [0, left] | 已确定的 0 |
| [left + 1, current - 1] | 已确定的 1 |
| [current, right - 1] | 待处理区域 |
| [right, nums.length - 1] | 已确定的 2 |

初始时 `left = -1`、`current = 0`、`right = nums.length`，前三个已确定区域都是空的，整个数组都在待处理区域中。每一步只需要检查 `nums[current]`，再把它丢给对应的区域即可。

## 二、快排的分区思路

这个过程可以联想到快速排序的数组分区。快排选择一个基准值，不断把较小的元素放到左侧、较大的元素放到右侧，最后让基准值落在分界位置。

颜色分类已经知道三种元素的归属，不需要额外选择基准值：

- 遇到 `0`，与左侧边界交换，然后扩大 0 区域。
- 遇到 `2`，与右侧边界交换，然后扩大 2 区域。
- 遇到 `1`，它本来就属于中间区域，只需推进 `current`。

分区的核心是区间含义始终不变。每次交换和移动指针后，四个区间仍然满足表中的定义。

## 三、错误的统一推进

初步写法可以把 `current` 放进 `for` 循环，每轮统一加一：

```text
for (int current = 0; current < right; current++) {
    if (nums[current] == 0) {
        swap(nums, current, ++left);
    } else if (nums[current] == 2) {
        swap(nums, current, --right);
    }
}
```

问题会在 `[1, 2, 0]` 中出现。`current = 1` 时，`2` 与右侧的 `0` 交换，数组变成 `[1, 0, 2]`。下一轮直接执行 `current++`，刚刚换到当前位置的 `0` 没有再次处理。

这说明了一个问题：交换来的数据也可能需要重新判断。

## 四、交换后的判断

什么时候可以继续推进，什么时候必须留在原地？要看交换位置属于哪个区域。

遇到 `0` 时，交换目标是新的 `left`。这个位置原本位于已确定的 1 区域，或者恰好就是 `current`，因此交换后当前位置已经处理完，可以执行 `current++`。

遇到 `2` 时，交换目标是 `--right`。这个位置原本属于待处理区域，换来的值可能是 `0、1、2` 中的任何一个，所以 `current` 不能前进。代码中使用 `continue`，让下一轮继续判断同一位置。

```text
class Solution {
    public void swap(int[] nums, int i, int j) {
        int temp = nums[i];
        nums[i] = nums[j];
        nums[j] = temp;
    }

    public void sortColors(int[] nums) {
        int left = -1;
        int right = nums.length;
        int current = 0;

        while (current < right) {
            if (nums[current] == 0) {
                swap(nums, current, ++left);
            } else if (nums[current] == 2) {
                swap(nums, current, --right);
                continue;
            }
            current++;
        }
    }
}
```

`current` 只向右移动，`right` 只向左移动，每一步都会缩短待处理区域，因此时间复杂度为 `O(n)`。交换在原数组中完成，额外空间复杂度为 `O(1)`。
