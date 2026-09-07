---
title: "【C语言】scanf函数的跳过问题处理"
published: 2025-12-16T16:35:07+08:00
updated: 2025-12-16T16:35:08+08:00
description: "解释 scanf 连续读取时 %c 意外读到空白字符的原因，并给出在格式串中跳过空白的处理方法。"
tags: ["C"]
category: "C"
author: "Mem0rin"
sourceLink: "https://blog.csdn.net/2501_93882415/article/details/155951803"
draft: false
pinned: false
---

```cpp
#define _CRT_SECURE_NO_WARNINGS 1
#include <stdio.h>

int main() {
	int a;
	char c;
	printf("请输入a：");
	scanf("%d", &a);
	printf("请输入c：");
	scanf("%c", &c);
	printf("c= %c", c);
	return 0;
}

>>>请输入a：1
请输入c：
（此处有回车）
>>>请输入a：1c
请输入c：c = c
```

**省流：scanf("%d%c", &a, &c)和拆开来写是等价的，%d读走了1，但是空格还在缓存区，占位符有且仅有%c会识别空白符，所以把\n读走了。**

**解决方法是%c前面加一个空格。**

代码如上所示，如果输入1并回车，就会跳过scanf("%c", &c)直接执行return 0。

原因是%c会识别空白字符，其中包括空格，制表符和回车，在scanf("%d", &a)输入1并回车之后，\n会残留在内存中，并被%c读取。

给更深层的来讲，是因为输入的信息会先存储在缓存区，因此如果我输入1然后回车，就会把1和\n都存进缓存区，并且scanf("%d", &a)只会读走1，\n此时还在缓存区，之后轮到c读取，就会把\n读走了。

虽然是多个输入，但是实际上他和scanf("%d%c", &a, &c)是等价的！！
