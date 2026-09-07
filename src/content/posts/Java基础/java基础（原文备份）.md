---
title: Java基础速成
published: 2026-01-19
pinned: false
description: 面向有编程经验的Java初学者的基础入门
tags: [Java]
category: Java
licenseName: "MIT"
author: Mem0rin
sourceLink: "https://blog.csdn.net/2501_93882415/article/details/157137010?spm=1001.2014.3001.5502"
draft: False
date: 2026-01-19
image: "./cover.jpg"
pubDate: 2026-01-19
---

# 目录

- [一、Java的特点](#一java的特点)
  - [1.面向对象语言](#1面向对象语言)
  - [2.静态类型语言](#2静态类型语言)
- [二、Java的简单入门语法](#二java的简单入门语法)
  - [1.条件语句：](#1条件语句)
    - [基础条件语句](#基础条件语句)
    - [大括号的使用](#大括号的使用)
    - [else](#else)
  - [2.自定义函数](#2自定义函数)
  - [3.数组（array）](#3数组array)
  - [4.循环语句](#4循环语句)
      - [while语句：](#while语句)
      - [for语句](#for语句)
      - [break和continue](#break和continue)
- [Homework 0](#homework-0)
  - [1.DrawTriangle（循环）](#1drawtriangle循环)
  - [2.FindMaxInArray（循环+数组+自定义函数）](#2findmaxinarray循环数组自定义函数)
  - [3.WindowsPosSum（自定义函数，条件，循环）](#3windowpossum自定义函数条件循环)


由于主包C转Java了，后面的更新内容基本都是java。
目前的主线是UC Berkeley的CS61B数据结构的内容，并会用国内课程加以补充。
# 一、Java的特点
分为以下几点
## 1.面向对象语言
意味着所有的代码都是存储在“类”（class）里的，并且类的名字要与代码的文件名保持一致，比如以下的“Hello World”代码：

```java
/** 包括主函数main，打印出Hello world! 
并且代码都在类HelloWorld内。*/
public class HelloWorld {
    public static void main(String[] args) {
        System.out.println("Hello world!");
	}
} 

```
在这段代码中有`public class`、`public static void main(String[] args)`这些不明所以的词，我们会在之后的学习中解释其作用。

## 2.静态类型语言
因此**所有的变量、参数和函数**都必须要提前声明其类型。而动态类型语言py不强制要求这一点。  
静态类型设计的优点包括：
①：在编码时能发现类型错误，减少调试负担；
②：避免用户的类型错误；
③：使得阅读和书写代码更加轻松；
④：避免了昂贵的类型检查，减少成本。
但也有其缺点，即代码冗长和推广度低。

# 二、Java的简单入门语法
## 1.条件语句：
### 基础条件语句
```java
/** 
* x在第一个条件分支上满足条件，x = x + 10，
* 第二个分支语句不满足条件，
* 因此x的输出值为15
*/
public class ClassNameHere {
    public static void main(String[] args) {
        int x = 5;

        if (x < 10)
            x = x + 10;

        if (x < 10)
            x = x + 10;

        System.out.println(x);
    }
}

```
可以在[Java可视化](https://cscircles.cemc.uwaterloo.ca/java_visualize/#)里观察代码运行的过程。
### 大括号的使用
用大括号可以执行多个语句，比如下列语句：（出于个人习惯，我会把if语句和大括号放在一起）
```java
/** 
* 加入了多个语句
*/
public class ConditionalsWithBlocks {
   public static void main(String[] args) {
      int x = 5;

      if (x < 10) {
         System.out.println("I shall increment x by 10.");
         x = x + 10;
      }

      if (x < 10) {
         System.out.println("I shall increment x by 10.");
         x = x + 10;
      }

      System.out.println(x);
   }
}
```
### else
同样java有else语句，如下：
```java
/** 用else语句模拟狗叫（什么鬼）*/
int dogSize = 20;
if (dogSize >= 50) {
    System.out.println("woof!");
} else if (dogSize >= 10) {
    System.out.println("bark!");
} else {
    System.out.println("yip!");
}

```
## 2.自定义函数
在java里自定义函数叫method，下面会附上java，py和c的自定义函数写法做对比：

### Python:
```python
def max(x, y):
    if (x > y):
        return x
    return y

print(max(5, 15))
```
### C语言:
```c
int max(int x, int y) {
	if (x > y) {
        return x;
    }
    return y;
}
```
### Java:
```java
public static int max(int x, int y) {
    if (x > y) {
        return x;
    }
    return y;
}

public static void main(String[] args) {
    System.out.println(max(10, 15));
}
```
我们将`public static int max(int x, int y)`称作方法签名（method's signature)，它列举了函数的参数，返回类型，函数名称和修饰符（`public`和`static`）。

## 3.数组（array）
数组定义：
```java
int[] numbers = new int[3];
numbers[0] = 4;
numbers[1] = 7;
numbers[2] = 10;
System.out.println(numbers[1]);
```
或者更简单的：
```java
int[] numbers = new int[]{4, 7, 10};
System.out.println(numbers[1]);
```

## 4.循环语句
### while语句：
在条件允许的情况下重复一段代码，例如
```java
int bottles = 99;
while (bottles > 0) {
    System.out.println(bottles + " bottles of beer on the wall.");
    bottles = bottles - 1;
}

```
同样你可以在[Java可视化](https://cscircles.cemc.uwaterloo.ca/java_visualize/#code=public+class+StdInDemo+%7B%0A++++public+static+void+main(String%5B%5D+args)+%7B%0A+++++++int+bottles+%3D+99%3B%0A+++++++while+(bottles+%3E+0)+%7B%0A++++++++++System.out.println(bottles+%2B+%22+bottles+of+beer+on+the+wall.%22)%3B%0A++++++++++bottles+%3D+bottles+-+1%3B%0A+++++++%7D%0A++++%7D%0A%7D&mode=display&curInstr=0)中观察其运行的流程。

### for语句
在使用while语句的过程中，人们发现，初始化变量，循环，条件判断，递增的操作具有普遍性，`for`语句便应运而生，格式为:
```java
for (initialization; termination; increment) {
    statement(s)
}

```
比如下方的求和函数，
```java
public class ClassNameHere {
    /** Uses a while loop to sum a. */
    public static int whileSum(int[] a) {
      int i = 0; //initialization
      int sum = 0;
      while (i < a.length) { //termination
            sum = sum + a[i];
            i = i + 1; //increment
      }
      return sum;
    }
    
	  /** Uses a basic for loop to sum A. */
    public static int sum(int[] a) {
      int sum = 0;
      for (int i = 0; i < a.length; i = i + 1) {
        sum = sum + a[i];
      }
      return sum;
    }
    
    public static void main(String[] args) {
      int[] a = {4, 3, 2, 1};
      System.out.println(sum(a));
    }
}
```
两个函数是等价的。
同样可以从[Java可视化](https://goo.gl/5fvnE7)看到这运行的过程。
### break和continue
break退出，continue跳过该次循环进入下一次循环，和其他编程语言一致。
## Homework 0
下面是CS61B的课后作业：
### 1.DrawTriangle（循环）
通过确定的n输出n行的星形三角形，例如n=5时输出的三角形就是
```
*
**
***
****
*****
```
```java
public class DrawTriangle {
    /**
     * Creative Exercise 1a: Drawing a Triangle
    public static void printStar(int n){
        int col = 0;
        while (col <= n) {
            System.out.print("*");
            col = col + 1;
        }
        System.out.println();
    }

    public static void main(String[] args) {
        int row = 0;
        int SIZE = 5;
        while (row < SIZE) {
            printStar(row);
            row = row + 1;
        }
    }
     */
    public static void drawTriangle(int N){
        int col = 0;
        int row = 0;
        while (col < N){
            while (row <= col){
                System.out.print("*");
                row = row + 1;
            }
            System.out.println();
            row = 0;
            col = col + 1;
        }
    }

    public static void main(String[] args){
        int SIZE = 10;
        drawTriangle(SIZE);
    }
}

```
### 2.FindMaxInArray（循环+数组+自定义函数）
要求是遍历找到数组中的最大值。
例如下列代码的数组的结果就是22。
```java
public class MaxNumberInArray {
    /** Returns the maximum value from m. */
    
    public static int max(int[] m) {
        int i = 0;
        int maximum = -1;
        while (i < m.length) {
            if (maximum < m[i]) {
                maximum = m[i];
            }
            i = i + 1;
        }
        return maximum;
    }
    
    /** Use a for loop to rewrite the solution. */
    public static int forMax(int[] arr){
        int max = -1;
        for (int i = 0; i < arr.length; i = i + 1) {
            if (arr[i] > max) {
                max = arr[i];
            }
        }
        return max;
    }
    public static void main(String[] args) {
        int[] numbers = new int[]{9, 2, 15, 2, 22, 10, 6};
        System.out.println(forMax(numbers));
    }
}
```

### 3.WindowsPosSum（自定义函数，条件，循环）
要求用自定义函数`windowPosSum(int[] a, int n)`实现：当a[i]为正的时候，将a[i]替换成a[i]到a[i + n]之和，如果超出了a的索引范围也就是a.length，则加到最后一个数为止。
例如对于数组`a = {1, 2, -3, 4, 5, 4}`和`n = 3`，我们有：
a[0] = a[0] + a[1] + a[2] + a[3]。
a[1] = a[1] + a[2] + a[3] + a[4]。
a[2]为负数不变
a[3] = a[3] + a[4] + a[5]。
a[4] = a[4] + a[5]。
a[5]是数组的最后一个数，也不变，即a[5] = a[5]。
得到结果`{4, 8, -3, 13, 9, 4}`。
代码如下：
```java
public class BreakContinue {
    public static void windowPosSum(int[] a, int n) {
        /** replaces each element a[i] with the sum of a[i] through a[i + n] */
        for (int i = 0; i < a.length; i = i + 1) {
            if (a[i] <= 0) {
                continue;
            }
            for (int j = 1; i + j < a.length && j <= n; j = j + 1) {
                a[i] = a[i] + a[i + j];
            }
        }
    }

    public static void main(String[] args) {
        int[] a = {1, -1, -1, 10, 5, -1};
        int n = 2;
        windowPosSum(a, n);

        // Should print 4, 8, -3, 13, 9, 4
        System.out.println(java.util.Arrays.toString(a));
    }
}
```