---
title: "算法每日一题：字母异位词-滑动窗口的计数与逆操作"
published: 2026-08-23T20:19:59+08:00
updated: 2026-08-23T20:19:59+08:00
description: "字母异位词要求字符种类和每种字符的数量完全相同，字符顺序可以不同。只要把字符频次放进固定长度的滑动窗口，字符串问题就能化归成更熟悉的整数数组问题。"
tags: ["算法", "数据结构"]
category: "算法"
author: "Mem0rin"
sourceLink: "https://zhuanlan.zhihu.com/p/2074953574984037959"
draft: false
pinned: false
---

## 目录

- [一、计数数组](#一计数数组)
- [二、固定窗口](#二固定窗口)
- [三、增量匹配](#三增量匹配)
- [四、进出窗口](#四进出窗口)

字母异位词要求字符种类和每种字符的数量完全相同，字符顺序可以不同。只要把字符频次放进固定长度的滑动窗口，字符串问题就能化归成更熟悉的整数数组问题。

## 一、计数数组

[LeetCode 438. 找到字符串中所有字母异位词](https://leetcode.cn/problems/find-all-anagrams-in-a-string/)

如果你觉得字符串形式陌生，可以先把小写字母映射成数字：`a` 对应 0，`b` 对应 1，一直到 `z` 对应 25。这样，字符串就变成了取值范围为 `[0, 25]` 的整数序列。

接下来建立两个长度为 26 的数组：

- `targetCounts` 记录字符串 `p` 中每个字符的数量。
- `windowCounts` 记录当前窗口中相关字符的数量。

整个过程可以写成一条清晰的路径：

```text
字符串 → 计数数组 → 固定长度窗口 → 增量更新匹配量 → 保存起点
```

## 二、固定窗口

异位词与 `p` 的长度相同，因此窗口长度始终固定为 `p.length()`。使用左闭右开区间 `[left, right)`，初始化时先把 `s` 的前 `p.length()` 个字符放入窗口。

如果 `p.length() > s.length()`，连一个完整窗口都无法形成，可以直接返回空结果。

初始化完成后，每次滑动包含两个动作：右侧加入一个字符，左侧移出一个字符。窗口长度不变，新的起点就是更新后的 `left`。

## 三、增量匹配

直接比较两个长度为 26 的数组也可以判断窗口是否匹配，但每移动一次都要重新扫描计数数组。这里使用一个 `matched` 记录已经满足需求的字符副本数量。

例如 `p` 中有两个 `a`，窗口中第一个和第二个 `a` 都会让 `matched` 加一；第三个 `a` 已经超过需求，不再增加。换句话说，`matched` 等于各字符 `min(windowCounts[i], targetCounts[i])` 的总和。

窗口长度固定为 `p.length()`。当 `matched == p.length()` 时，窗口中的每个位置都已经匹配到需求，当前窗口就是一个字母异位词。

使用增量状态可以省去每次滑动时对 26 个下标的重新比较。由于字母表大小固定，两种写法的渐进时间复杂度都是 `O(n)`；`matched` 优化的是每次移动的常数开销。

## 四、进出窗口

进窗口和出窗口互为逆操作，更新顺序也正好相反。

字符进入窗口时，先增加频次，再判断增加后的数量是否仍在需求范围内：

```text
windowCounts[index]++;
if (windowCounts[index] <= targetCounts[index]) {
    matched++;
}
```

字符离开窗口时，先根据离开前的频次判断它是否占用了一个有效匹配，再减少频次：

```text
if (windowCounts[index] <= targetCounts[index]) {
    matched--;
}
windowCounts[index]--;
```

如果选择先减少频次，判断条件需要相应改成 `< targetCounts[index]`。把两侧写成逆操作，可以直接从进入窗口的逻辑推出离开窗口的逻辑，不用重新模拟一遍。

完整代码如下：

```text
import java.util.LinkedList;
import java.util.List;

class Solution {
    public List<Integer> findAnagrams(String s, String p) {
        List<Integer> result = new LinkedList<>();
        int patternLength = p.length();
        int stringLength = s.length();
        if (patternLength > stringLength) {
            return result;
        }

        int[] targetCounts = new int[26];
        int[] windowCounts = new int[26];
        for (int i = 0; i < patternLength; i++) {
            targetCounts[p.charAt(i) - 'a']++;
        }

        int left = 0;
        int right = 0;
        int matched = 0;
        while (right < patternLength) {
            int index = s.charAt(right++) - 'a';
            if (targetCounts[index] > 0) {
                windowCounts[index]++;
                if (windowCounts[index] <= targetCounts[index]) {
                    matched++;
                }
            }
        }
        if (matched == patternLength) {
            result.add(left);
        }

        while (right < stringLength) {
            int index = s.charAt(right++) - 'a';
            if (targetCounts[index] > 0) {
                windowCounts[index]++;
                if (windowCounts[index] <= targetCounts[index]) {
                    matched++;
                }
            }

            index = s.charAt(left++) - 'a';
            if (targetCounts[index] > 0) {
                if (windowCounts[index] <= targetCounts[index]) {
                    matched--;
                }
                windowCounts[index]--;
            }

            if (matched == patternLength) {
                result.add(left);
            }
        }
        return result;
    }
}
```

构造目标计数需要 `O(|p|)`，滑动窗口需要 `O(|s|)`，总时间复杂度为 `O(|s| + |p|)`。两个计数数组长度固定为 26，除返回结果外的额外空间复杂度为 `O(1)`。
