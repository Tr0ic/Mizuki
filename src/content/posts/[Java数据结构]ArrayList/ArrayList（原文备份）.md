---
title: Java：ArrayList
published: 2026-03-26
pinned: false
description: Java中ArrayList的实现原理和使用方法。
tags: [Java]
category: Java
licenseName: "MIT"
author: Mem0rin
sourceLink: "https://blog.csdn.net/2501_93882415/article/details/159495525?spm=1001.2014.3001.5502"
draft: False
date: 2026-03-26
image: "./cover.png"
pubDate: 2026-03-26
---

## 文章目录
- [一、线性表](#一线性表)
- [二、ArrayList](#二ArrayList)
  - [1.ArrayList的基本结构](#1ArrayList的基本结构)
  - [2.ArrayList的使用](#2ArrayList的使用)
  - [3.ArrayList的缺点](#3ArrayList的缺点)



## 一、线性表
线性表是数据结构中最简单的结构，专门用来存储“一对一”的数据，也就是说数据本身与前驱，本身与后继都是一一对应的。
线性表分为顺序表和链表，前者为顺序存储结构，后者为链式存储结构。常见的线性表有顺序表，队列，栈，链表等等


## 二、ArrayList
`ArrayList`是顺序表的一种具体实现方式，底层依赖数组实现，并实现了 `List` 接口，具体的框架如下：![图片来自菜鸟教程](ArrayList.png)
`ArrayList` 相较于数组的优点在于没有固定的大小限制，可以添加或者删除元素，或者对原来的顺序表进行扩容。

`ArrayList`具有有以下特点：
1. ArrayList是以泛型方式实现的，使用时必须要先实例化
2. ArrayList实现了RandomAccess接口，表明ArrayList支持随机访问
3. ArrayList实现了Cloneable接口，表明ArrayList是可以clone的
4. ArrayList实现了Serializable接口，表明ArrayList是支持序列化的
5. 和Vector不同，ArrayList不是线程安全的，在单线程下可以使用，在多线程中可以选择Vector或者
CopyOnWriteArrayList
6. ArrayList底层是一段连续的空间，并且可以动态扩容，是一个动态类型的顺序表
### 1.ArrayList的基本结构
模拟实现如下（以下顺序表仅基于 int 类型数据进行实现）
#### 初始化：
```java
public int[] elem;
public int usedSize;//0
    //默认容量
private static final int DEFAULT_SIZE = 10;

public MyArraylist() {
    this.elem = new int[DEFAULT_SIZE];
}
```
`elem`：存储对象

`usedSize`：顺序表内的数据数量

`DEFAULT_SIZE`：顺序表的初始大小

#### isFull()方法：
用于判断顺序表是否无法继续添加对象。
```java
public boolean isFull() {
    return usedSize == DEFAULT_SIZE;
}
```

#### grow()方法：
对顺序表进行扩容：
```java
public void grow() {
    this.elem = Arrays.copyOf(elem, 2 * elem.length);
}
```
#### add()方法：
默认向数组尾端添加数据：
```java
public void add(int data) {
    if (isFull()) {
        grow();
    }
    this.elem[usedSize] = data;
    this.usedSize++;
}
```
也可以用`add(int index, int data)`重载方法实现特定索引的插入，但是`pos`并不一定是安全的，因此我们期望的是如果`pos`的值异常，可以让用户知道程序错误，如果`pos`正常则正常进行。

可行的方法是写一个检查`pos`的函数，如果错误抛出**自定义的顺序表异常**。
```java
public class ArrayException extends Exception{
    public ArrayException() {}

    public ArrayException(String msg) {
        super(msg);
    }

}
private boolean checkPosInAdd(int pos) throws ArrayException{
        if (pos > usedSize || pos < 0) {
            throw new ArrayException("POS ERROR");
        }
        return true;//合法
    }

// 在 pos 位置新增元素
public void add(int pos, int data) {
    try {
        if (isFull()) {
            this.elem = Arrays.copyOf(this.elem, 2 * DEFAULT_SIZE);
        }

        if(checkPosInAdd(pos)) {
            for (int i = usedSize; i > pos; i--) {
                this.elem[i] = this.elem[i - 1];
            }
            this.elem[pos] = data;
            this.usedSize++;
        }
    } catch(ArrayException e) {
            e.printStackTrace();
    }
}
```
#### 其余实现
```java
// 判定是否包含某个元素
    public boolean contains(int toFind) {
        for (int i = 0; i < usedSize; i++) {
            if (this.elem[i] == toFind) {
                return true;
            }
        }
        return false;
    }
    // 查找某个元素对应的位置
    public int indexOf(int toFind) {
        for (int i = 0; i < usedSize; i++) {
            if (this.elem[i] == toFind) {
                return i;
            }
        }
        return -1;
    }

    // 获取 pos 位置的元素
    public int get(int pos) {
        try {
            if (pos < 0 || pos >= usedSize) {
                throw new ArrayException("POS ERROR");
            }
            return this.elem[pos];
        } catch (ArrayException e) {
            e.printStackTrace();
        }
        return 0;
    }

    private boolean isEmpty() {
        return usedSize == 0;
    }
    // 给 pos 位置的元素设为【更新为】 value
    public void set(int pos, int value) {
        try {
            if (pos < 0 || pos >= usedSize) {
                throw new ArrayException("POS ERROR");
            }
            this.elem[pos] = value;
        } catch (ArrayException e) {
            e.printStackTrace();
        }
    }

    /**
     * 删除第一次出现的关键字key
     * @param key
     */
    public void remove(int key) {
        if (contains(key)) {
            int index = indexOf(key);
            for (int i = index; i < this.usedSize - 1; i++) {
                this.elem[i] = this.elem[i + 1];
            }
            usedSize--;
        }
    }

    // 获取顺序表长度
    public int size() {
        return this.usedSize;
    }

    // 清空顺序表
    public void clear() {
        for (int i = 0; i < usedSize; i++) {
            this.elem[i] = 0;
        }
        this.usedSize = 0;
    }
```
实际上`ArrayList`的实现远比这复杂，这样的简单实现主要是为了对`ArrayList`的运行方式有一个整体的概念。
### 2.ArrayList的使用
#### ArrayLIst的构造
|构造方法  | 解释 |
|--|--|
| `ArrayList()` | 无参构造，按照默认设置生成 |
| `ArrayList(Collection<? extends E> c) `| 利用其它 `Collection`  对象构造 `ArrayList` |
 `ArrayList(int initialCapacity)` |指定顺序表的初始容量
 

```java
 public static void main(String[] args) {
        // ArrayList创建，推荐写法
        // 构造一个空的列表
        List<Integer> list1 = new ArrayList<>();
        // 构造一个具有10个容量的列表
        List<Integer> list2 = new ArrayList<>(10);
        list2.add(1);
        list2.add(2);
        list2.add(3);
        // list2.add("hello"); // 编译失败，List<Integer>已经限定了，list2中只能存储整形元素
        // list3构造好之后，与list中的元素一致
        ArrayList<Integer> list3 = new ArrayList<>(list2);
        // 避免省略类型，否则：任意类型的元素都可以存放，使用时将是一场灾难
        List list4 = new ArrayList();
        list4.add("111");
        list4.add(100);
  }
```
#### ArrayList实战(杨辉三角)
杨辉三角：
```java
public class PascalTriangle {


    public static void main(String[] args) {
        List<List<Integer>> list = new ArrayList<>();
        List<Integer> list0 = new ArrayList<>();
        list0.add(1);
        list.add(list0);

        for (int i = 1; i < 5; i++) {
            List<Integer> curList = new ArrayList<>();
            List<Integer> preList = list.get(i - 1);
            //头
            curList.add(1);
            //中间
            for (int j = 1; j < i; j++) {
                curList.add(j, preList.get(j - 1) + preList.get(j));
            }
            //尾
            curList.add(1);

            list.add(curList);
        }

        for (List<Integer> curList : list) {
            for (Integer integer : curList) {
                System.out.print(integer + " ");
            }
            System.out.println("");
        }


    }
}
```
可以发现封装的数据结构比裸露的二维数组更清楚。

### 3.ArrayList的缺点
但是顺序结构的线性表有一个问题就是：无论是添加还是删除元素都需要批量的移动数据，时间复杂度是O(N)的，因此如果对于需要频繁添加删除但是对查询要求较低的数据可以采用链式结构，也就是下一个博客的内容。


