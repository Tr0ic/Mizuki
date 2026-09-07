---
title: "二分查找：寻找最小值与点名"
published: 2026-08-08T21:58:22+08:00
updated: 2026-08-08T21:58:24+08:00
description: "通过旋转数组最小值和点名两题梳理二分查找的边界设计，重点判断 mid 是否仍可能成为答案。"
tags: ["算法", "数据结构"]
category: "算法"
author: "Mem0rin"
sourceLink: "https://blog.csdn.net/2501_93882415/article/details/163573118"
draft: false
pinned: false
---

## 目录

- [一、二分查找的边界判断](#一二分查找的边界判断)
- [二、寻找旋转排序数组中的最小值](#二寻找旋转排序数组中的最小值)
- [三、点名](#三点名)

这两道题都使用二分查找。真正需要判断的不是“套哪一个模板”，而是：`mid` 对应的位置是否仍可能成为答案。如果可能，就必须保留；如果不可能，才可以越过它。

## 一、二分查找的边界判断

二分查找每次都要排除一段不可能包含答案的区间。更新边界前，可以先问两个问题：

1. 答案可能等于 `mid` 吗？
2. 循环结束时，答案由区间中的元素表示，还是由边界位置表示？

这两个问题决定了应该使用 `right = mid`、`right = mid - 1`，还是 `left = mid + 1`。

## 二、寻找旋转排序数组中的最小值

[LeetCode 153. 寻找旋转排序数组中的最小值](https://leetcode.cn/problems/find-minimum-in-rotated-sorted-array/)

旋转后的数组可以看成两段递增区间。与其判断 `mid` 属于图中的哪一段，不如直接比较 `nums[mid]` 与右边界 `nums[right]`。

- 当 `nums[mid] < nums[right]` 时，`mid` 到 `right` 是递增的，最小值位于 `[left, mid]`。`mid` 本身仍可能是最小值，因此令 `right = mid`。
- 当 `nums[mid] > nums[right]` 时，`mid` 位于旋转点左侧，最小值只能位于 `[mid + 1, right]`。此时 `mid` 不可能是答案，因此令 `left = mid + 1`。

题目保证元素互不相同，而且循环中 `mid < right`，所以不需要处理 `nums[mid] == nums[right]`。

```java
class Solution {
    public int findMin(int[] nums) {
        int left = 0;
        int right = nums.length - 1;
        while (left < right) {
            int mid = left + (right - left) / 2;
            if (nums[mid] < nums[right]) {
                right = mid;
            } else {
                left = mid + 1;
            }
        }
        return nums[left];
    }
}
```

循环始终保证最小值位于闭区间 `[left, right]`。当 `left == right` 时，区间中只剩一个元素，它就是最小值。

时间复杂度为 `O(log n)`，空间复杂度为 `O(1)`。

## 三、点名

[LCR 173. 点名](https://leetcode.cn/problems/que-shi-de-shu-zi-lcof/)

如果没有同学缺席，学号与数组下标相同。缺失位置出现后，后面的学号都会比下标大 `1`：

- 缺失位置之前：`records[i] == i`；
- 缺失位置及其之后：`records[i] == i + 1`。

因此，这道题可以转化为寻找第一个发生偏移的位置。

设缺失学号为 `p`。这份代码维护的不变量是 `p` 始终位于 `[left, right + 1]`，其中 `right + 1` 也可能是答案。

```java
class Solution {
    public int takeAttendance(int[] records) {
        int left = 0;
        int right = records.length - 1;
        while (left <= right) {
            int mid = left + (right - left) / 2;
            if (records[mid] == mid + 1) {
                right = mid - 1;
            } else {
                left = mid + 1;
            }
        }
        return left;
    }
}
```

当 `records[mid] == mid + 1` 时，有 `p <= mid`，因此令 `right = mid - 1`。虽然新的待检查下标区间不再包含 `mid`，但新的 `right + 1` 正好等于 `mid`，所以 `p == mid` 的情况并没有丢失。否则有 `records[mid] == mid`，说明 `p > mid`，令 `left = mid + 1`。

循环结束时 `left == right + 1`，不变量收缩为唯一位置 `p == left`。若缺少的是最后一个学号，数组中不会出现偏移，此时 `left` 会自然移动到 `records.length`，仍然得到正确答案。

时间复杂度为 `O(log n)`，空间复杂度为 `O(1)`。
