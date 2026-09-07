---
title: "二分查找：左右边界"
published: 2026-08-11T16:56:15+08:00
updated: 2026-08-11T16:56:18+08:00
description: "这两次搜索都会返回数组中的一个候选下标，但候选值不一定等于。，因此不能只用“左候选是否大于右候选”判断目标是否存在。分支，区间不会变化，从而产生死循环。搜索时，需要先确定区间外已经知道什么，再决定。表格描述的是候选区间外侧，不包含仍待判断的。除返回数组外，额外空间复杂度为。的位置，右边界是最后一个等于。如果这里仍使用下中点，那么在。两次二分搜索的时间复杂度均为。，两个分支都能让区间收缩。，区间都会继续缩小。"
tags: ["算法", "数据结构"]
category: "算法"
author: "Mem0rin"
sourceLink: "https://blog.csdn.net/2501_93882415/article/details/163671761"
draft: false
pinned: false
---

## 目录

- [一、把问题拆成两次边界搜索](#一把问题拆成两次边界搜索)
- [二、寻找左边界](#二寻找左边界)
- [三、寻找右边界](#三寻找右边界)
- [四、目标不存在时的校验](#四目标不存在时的校验)

## 一、把问题拆成两次边界搜索

[LeetCode 34. 在排序数组中查找元素的第一个和最后一个位置](https://leetcode.cn/problems/find-first-and-last-position-of-element-in-sorted-array/)

左边界是第一个等于 `target` 的位置，右边界是最后一个等于 `target` 的位置。使用闭区间 `[left, right]` 搜索时，需要先确定区间外已经知道什么，再决定 `mid` 是否仍可能是答案。

| 搜索目标 | `left` 左侧 | `right` 右侧 |
| --- | --- | --- |
| 左边界 | `< target` | `>= target` |
| 右边界 | `<= target` | `> target` |

表格描述的是候选区间外侧，不包含仍待判断的 `[left, right]`。

## 二、寻找左边界

左边界搜索使用下中点：

```text
mid = left + (right - left) / 2
```

- 当 `nums[mid] < target` 时，`mid` 及其左侧不可能是答案，令 `left = mid + 1`。
- 当 `nums[mid] >= target` 时，`mid` 仍可能是第一个目标值，令 `right = mid` 保留它。

当区间只剩 `[i, i + 1]` 时，下中点为 `i`。无论更新 `left = mid + 1` 还是 `right = mid`，区间都会继续缩小。

## 三、寻找右边界

右边界搜索使用上中点：

```text
mid = left + (right - left) / 2 + 1
```

- 当 `nums[mid] <= target` 时，`mid` 仍可能是最后一个目标值，令 `left = mid` 保留它。
- 当 `nums[mid] > target` 时，`mid` 及其右侧不可能是答案，令 `right = mid - 1`。

如果这里仍使用下中点，那么在 `[i, i + 1]` 中会得到 `mid == left == i`。一旦进入 `left = mid` 分支，区间不会变化，从而产生死循环。改用上中点后，`mid == i + 1`，两个分支都能让区间收缩。

## 四、目标不存在时的校验

这两次搜索都会返回数组中的一个候选下标，但候选值不一定等于 `target`。例如数组只有 `[5]` 时，查找 `4` 或 `6` 都会得到候选位置 `0`，因此不能只用“左候选是否大于右候选”判断目标是否存在。

完整代码需要额外处理空数组，并检查两个候选位置的值：

```java
class Solution {
    public int[] searchRange(int[] nums, int target) {
        int[] ret = new int[2];
        int left = 0;
        int right = nums.length - 1;

        while (left < right) {
            int mid = left + (right - left) / 2;
            if (nums[mid] < target) {
                left = mid + 1;
            } else {
                right = mid;
            }
        }
        ret[0] = left;

        left = 0;
        right = nums.length - 1;
        while (left < right) {
            int mid = left + (right - left) / 2 + 1;
            if (nums[mid] <= target) {
                left = mid;
            } else {
                right = mid - 1;
            }
        }
        ret[1] = right;

        if (nums.length == 0
                || nums[ret[0]] != target
                || nums[ret[1]] != target) {
            ret[0] = -1;
            ret[1] = -1;
        }
        return ret;
    }
}
```

两次二分搜索的时间复杂度均为 `O(log n)`，总时间复杂度仍为 `O(log n)`；除返回数组外，额外空间复杂度为 `O(1)`。
