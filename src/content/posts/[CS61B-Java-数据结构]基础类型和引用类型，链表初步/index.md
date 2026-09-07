---
title: "[CS61B/Java/数据结构]基础类型和引用类型，链表初步"
published: 2026-01-29T21:52:47+08:00
updated: 2026-01-29T21:52:49+08:00
description: "梳理 Java 基础类型与引用类型的内存语义、参数传递规则，并以链表为例说明引用的实际用法。"
tags: ["Java", "数据结构"]
category: "Java"
author: "Mem0rin"
sourceLink: "https://blog.csdn.net/2501_93882415/article/details/157512981"
draft: false
pinned: false
---

## 目录

- [一、基础类型](#一基础类型)
  - [1.变量类型](#1变量类型)
  - [2. 变量创建](#2-变量创建)
- [二、引用类型](#二引用类型)
  - [1.变量类型](#1变量类型-1)
  - [2.变量创建](#2变量创建)
- [三、GRoE准则（Golden Rule of Equals For primitives）](#三groe准则golden-rule-of-equals-for-primitives)
  - [传值和传址](#传值和传址)
- [四、链表初步](#四链表初步)
  - [1.链表建立](#1链表建立)
  - [2.链表的基本函数](#2链表的基本函数)

> 画师：竹取工坊![画师：竹取工坊](../_assets/csdn-c5298a62a7dd5233.jpeg)  
>  大佬们好！我是Mem0rin！现在正在准备自学转码。  
>  如果我的文章对你有帮助的话，欢迎关注我的主页[Mem0rin](https://blog.csdn.net/2501_93882415?spm=1010.2135.3001.10640)，欢迎互三，一起进步！

该博客为CS61B的Lec4的复习，

## 一、基础类型

### 1.变量类型

在Java中有8个**基础变量**，分别为`byte`, `short`, `int`, `long`, `float`, `double`, `boolean`以及 `char`。每个基础变量都在内存中对应着固定的bit数，例如`short`变量占用16个bit，`bype`占用8bit。

### 2. 变量创建

当我们声明基础变量的时候，计算机会在内存中开辟足够数量的bit用于存放数据。例如当我们声明`int x`的时候，计算机会在内存中开辟32bit的空间。  
 而当我们通过`int y = x`的方式定义变量的时候，我们可以简单理解成通过`int y`开辟内存，然后用`y = x`把x对应的bit一一复制到y对应的内存中。

## 二、引用类型

### 1.变量类型

在C语言我们知道，数组中的数组名其实是地址，指向数组首元素。在Java中也是这样。并且不只是数组，通过类创建的实例对象也表示的是地址，这样的数据类型我们称作**引用类型**。或者换一种说法，不在八个基础类型内的数据类型都是引用变量。

### 2.变量创建

虽然数组可以通过别的方式定义，但为了叙述方便，我们统一用`new`的方式进行定义。  
 当我们用`new`创建引用类型的变量的时候，同样计算机会在内存中开辟足够的空间，比如`int`和`double`类型各有一个的变量，计算机就会开辟96bit（32+64）的内存。默认初始值为0，但是默认值不允许访问的。在创建好变量之后，就会返回一个大小为64bit的地址，存储在创建的变量上。  
 当我们用类似于`Dog bigDog = smallDog`时，其实是我们创建好了实例之后，把smallDog的对应的值按照bit一一复制到了bigDog中。

## 三、GRoE准则（Golden Rule of Equals For primitives）

当我们`=`传输数据的时候，我们始终遵循着的原则是**一一复制**。  
 而基础类型和引用类型所表示的数据是不一样的，因此就和C语言一样延伸出了**传值和传址**的概念。  
 需要进一步了解的可以去我的往期博客[传值与传址](https://blog.csdn.net/2501_93882415/article/details/156130860?spm=1001.2014.3001.5502)的第一部分

### 传值和传址

当我们定义类：

```java
public static class Walrus {
    public int weight;
    public double tuskSize;

    public Walrus(int w, double ts) {
          weight = w;
          tuskSize = ts;
    }
}
```

考虑以下方法：

```java
public class PassByValueFigure {
    public static void main(String[] args) {
           Walrus walrus = new Walrus(3500, 10.5);
           int x = 9;

           doStuff(walrus, x);
           System.out.println(walrus);
           System.out.println(x);
    }

    public static void doStuff(Walrus W, int x) {
           W.weight = W.weight - 100;
           x = x - 5;
    }
}
```

我们会发现main方法中的`x`并不会因为`doStuff`方法中`x`的改变而改变。这是因为当方法传参的时候，基础类型的变量传参是把变量本身的值一一复制到形参的内存中。也就是所谓的“**传值**”。  
 而对于引用类型，是以“**传址**”的形式传参的，也就是说`doStuff`中的`W`其实是`walrus`一一复制bit的结果，这意味着W和walrus一样对应着对象`walrus`的地址，因此通过`W.weight = W.weight - 100`能够确切的改变对象的值。

## 四、链表初步

### 1.链表建立

有了这些前置知识我们就可以创造出一个**可加长**的数组`IntList`,对应的类设计如下：

```java
public class IntList {
    public int first;
    public IntList rest;        

    public IntList(int f, IntList r) {
        first = f;
        rest = r;
    }
}
```

这是类似于链表的结构，first存储指针的信息，rest存储下一个指针的地址。  
 如果我们要创建一个5,10,15的链表，我们可以采取以下方式：

```java
IntList L = new IntList(5, null);
L.rest = new IntList(10, null);
L.rest.rest = new IntList(15, null);
```

但是更优雅的方式是下面的方式，

```java
IntList L = new IntList(15, null);
L = new IntList(10, L);
L = new IntList(5, L);
```

虽然`IntList`原则上可以存储所有的整数列表，但是这样会导致代码丑陋且容易出错。

### 2.链表的基本函数

#### ① 链表长度函数size()

可以通过递归和迭代两种方式实现：

```java
/** Return the size of the list using... recursion! */
public int size() {
    if (rest == null) {
        return 1;
    }
    return 1 + this.rest.size();
}
/** Return the size of the list using no recursion! */
public int iterativeSize() {
    IntList p = this;
    int totalSize = 0;
    while (p != null) {
        totalSize += 1;
        p = p.rest;
    }
    return totalSize;
}
```

注意递归的终止条件是`rest == null`而不是`this == null`，这是因为如果我们对一个值为`null`的L使用L.size()，我们期望的并不是0，而是你不能对一个为null的列表求长度，因此应该为 NullPointer 的错误。

#### ② 获取第n个数据get()

依旧可以通过递归和迭代两种方式实现：

```java
/** Return the nth member of the list using... recursion! */
public int get(int n) {
	if (n == 0) {
		return first;
	}
	return rest.get(n - 1);
}

/** Return the nth member of the list using no recusion! */
public int iterativeGet(int n){
	IntList p = this;
	while (n > 0) {
		p = p.rest;
		n -= 1;
	}
	return p.first;
}
```

以上。
