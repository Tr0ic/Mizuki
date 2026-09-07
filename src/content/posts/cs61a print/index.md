---
title: "CS61A：Print 初探（附图解）"
published: 2025-12-04T08:51:18+08:00
updated: 2025-12-04T09:15:14+08:00
description: "从 Python print 的基本输出讲到嵌套调用，结合求值顺序说明表达式、返回值和 None 如何被打印。"
tags: ["Python", "CS61A"]
category: "Python"
author: "Mem0rin"
sourceLink: "https://blog.csdn.net/2501_93882415/article/details/155542031"
draft: false
pinned: false
image: "./cover.jpg"
licenseName: "Unlicensed"
---

## 目录

- [一、print函数的基础使用](#一print函数的基础使用)
- [二、print函数的嵌套以及运行顺序](#二print函数的嵌套以及运行顺序)

孩子们CS61A真的做的太好了我巴不得写100篇。

下期讲C语言的printf。

观前提醒：本文使用的知识内容包括：自定义函数，print函数嵌套，所有的指令均在命令行进行。

**目录**

[一、print函数的基础使用](#%E4%B8%80%E3%80%81print%E5%87%BD%E6%95%B0%E7%9A%84%E5%9F%BA%E7%A1%80%E4%BD%BF%E7%94%A8)

[二、print函数的嵌套以及运行顺序](#%E4%BA%8C%E3%80%81print%E5%87%BD%E6%95%B0%E7%9A%84%E5%B5%8C%E5%A5%97%E4%BB%A5%E5%8F%8A%E8%BF%90%E8%A1%8C%E9%A1%BA%E5%BA%8F)

---

## **一、print函数的基础使用**

顾名思义就是print（打印）。比如：

```python
>>> -2
-2
>>> print(-2)
-2
```

        但正如上面所看到的，直接打-2也可以输出-2，为什么要用print？

        在下面的代码中我们就可以看出两者的差别：

```python
>>> "hello"
'hello'
>>> print("hello")
hello
>>> None
>>> print(None)
None
```

           其中的核心在于：print的规则是**自动显示内部输入的任何表达式的值**，因此尽管None不会显示任何信息也会被print忠实地打印下来。

        print还可以同时打印多个数据，并把逗号转化为空格。

```python
>>> print(1,2,3)
1 2 3
>>> print(None,None)
None None
>>> print('hello','world')
hello world
```

        我们还可以在print的表达式中调用函数：

```python
>>> def square(x):
...     return x**2
...
>>> from operator import add
>>> print(add(3,2),square(4))
5 16
```

        我们用图解来表示这个过程（图像由GPT生成，虽然还是很丑但差不多是这个意思）：

![](print1.png)

        print函数首先运行的是add(3,2)，调用函数add()，求出add(3,2)=5，然后调用自定义函数square()得到16，最后再回到print函数输出5 16。

        从这个例子中我们也可以意识到，当我们运行函数的时候，他会先把里面的函数的值全部求出来，再用print输出，在下面的内容我们会有更深的理解。

## 二、print函数的嵌套以及运行顺序

        如果我们输入print(print(1),print(2))会怎么样？

```python
>>> print(print(1),print(2))
1
2
None None
```

这个None是什么鬼，为什么会有这样的结果？

事实上print是Non-Pure Function，这意味着print函数除了输入和输出是有side effect的，而这个副作用就是打印值。![](print2.png)

我们可以通过代码进行验证

```python
>>> a = print(1)
1
>>> a
>>> print(a)
None
```

同时我们需要注意的是，python的print是自带换行符的。

现在按照我们前面提到的所有的点，让我们用这个例子串起来吧——

①当我们运行print的时候需要先把里面的值全部求出来，才会用print进行打印；

②print运行的时候，作为调用语句的副作用，会打印出括号内的值，同时本身有返回值None；

③print在打印出值后会自动换行。

那么聪明的你就可以理解为什么是这样的结果了，同样我们用图像分解一下（图片来自CS61A）：![](print3.png)

要运行print(print(1),print(2))首先要分别运行print(1)，print(2)，换行打印side effect 1和2，同时返回None None，最后输出print(None,None)，把逗号换成空格，得到None None。

来试试这个课后小题吧！用代码确认你的答案！

```python
>>> def square(x):
...     print("result:")
...     return x**2
...
>>> from operator import add
>>> print(1,print(add(3,2)),square(4))
```
