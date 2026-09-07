---
title: Java：链表
published: 2026-04-02
pinned: false
description: Java中链表的实现原理和使用方法。
tags: [Java]
category: Java
licenseName: "MIT"
author: Mem0rin
sourceLink: "https://blog.csdn.net/2501_93882415/article/details/159735934?spm=1001.2014.3001.5502"
draft: False
date: 2026-04-02
image: "./cover.jpg"
pubDate: 2026-04-02
---

## 文章目录
- [一、单向链表](#一单向链表)
  - [1.链表的概念和结构](#1链表的概念和结构)
  - [2.链表的功能及实现](#2链表的功能及实现)
    - [链表的主体](#链表的主体)
    - [链表的遍历](#链表的遍历)
    - [添加节点的方法add()](#添加节点的方法add)
    - [删除节点remove()](#删除节点remove)
- [二、双向链表](#二双向链表)
    - [1.双向链表的结构](#1双向链表的结构)
    - [2.双向链表的实现](#2双向链表的实现)
        - [节点设计](#节点设计)
        - [链表的遍历](#链表的遍历-1)
        - [添加节点](#添加节点)
        - [删除节点](#删除节点)
- [三、LinkedList的使用](#三LinkedList的使用)
  - [构造方法](#构造方法)
  - [迭代元素](#迭代元素)
  - [常用方法](#常用方法)



主要内容是无头的单向和双向的链表的实现和使用。依旧，我们只针对data为整数的情况进行模拟实现，如果需要了解泛型的具体实现请参考官方文档。
图片来自知乎[一口气搞懂「链表」，就靠这20+张图了](https://zhuanlan.zhihu.com/p/249144171)。
## 一、单向链表
### 1.链表的概念和结构
结构如图：

![图片来自https://zhuanlan.zhihu.com/p/249144171](1.png)
链表上的每一个节点都包含一个 `data` 数据和一个 `next` 引用数据，用来指向下一个节点，节点与节点的跳转就是通过 `next` 进行的。

链表的优势在于添加和删除节点的时间复杂度为O(1)，只需要改变前后节点的引用即可 。

![图片来自https://zhuanlan.zhihu.com/p/249144171](2.png)
### 2.链表的功能及实现
#### 链表的主体
链表的主体是用一个内部类 `ListNode` 实现的，包括储存值的 `val` 和储存下一个节点位置的引用类型 `ListNode next` ，我们用 `head` 来指定链表的入口，也就是链表的第一个节点，如果 `head` 为null，说明链表为空。并在最后一个节点在`next` 上用null表示链表的尽头，定义如下：

```java
    public static class ListNode {
        public int val;
        public ListNode next;

        public ListNode(int val) {
            this.val = val;
        }
    }
    public ListNode head;
```
#### 链表的遍历
这样我们就可以实现简单的链表遍历和相关的方法了：
```java  
    public int size() {
        int size = 0;
        ListNode cur = head;
        while (cur != null) {
            cur = cur.next;
            size++;
        }
        return size;
    }
    public void display() {
        ListNode cur = head;
        while (cur != null) {
            System.out.print(cur.val + " ");
            cur = cur.next;
        }
    }
    public boolean contains(int key) {

        ListNode cur = head;
        while (cur != null) {
            if (cur.val == key) {
                return true;
            }
            cur = cur.next;
        }
        return false;
    }
    public void clear() {
        head = null;
    }
```
#### 添加节点的方法add()
我们分为三种情况，在头部添加节点，在尾部添加节点，以及进一步地，在任意索引处添加节点。
```java
    //头插法
    public void addFirst(int data) {
        ListNode node = new ListNode(data);
        if (head == null) {
            head = node;
        } else {
            node.next = head;
            head = node;
        }
    }
    //尾插法
    public void addLast(int data) {
        if (head == null) {
            addFirst(data);
        } else {
            ListNode node = new ListNode(data);
            ListNode cur = head;
            while (cur.next != null) {
                cur = cur.next;
            }
            cur.next = node;
        }

    }

    //任意位置插入,第一个数据节点为0号下标
    public boolean addIndex(int index,int data) {
        int len = size();
        if (index < 0 || index > len) {
            return false;
        } else if (index == 0) {
            addFirst(data);
        } else if (index == len) {
            addLast(data);
        } else {
            ListNode node = new ListNode(data);
            ListNode cur = head;
            ListNode pre = null;
            for (int i = 0; i < index; i++) {
                pre = cur;
                cur = cur.next;
            }
            pre.next = node;
            node.next = cur;
        }
        return true;
    }
```
因为 `addIndex` 方法存在索引超出范围的情况，因此我们给方法的输出类型为 `boolean` 而非 `void` 。

我们也会发现在该方法的内部我们用pre来存储前一个节点，从而进行前后节点的修改，这样的备份在链表的操作中是常出现的。

#### 删除节点remove()
如图所示，删除节点相当于是把上一个节点的next指向了当前节点的下一个节点，也就是用 `pre.next = cur.next` 。
![图片来自https://zhuanlan.zhihu.com/p/249144171](3.png)
```java
//删除第一次出现关键字为key的节点
    public void remove(int key) {
        if (contains(key)) {
            if (head.val ==key) {
                head = head.next;
                return;
            }
            ListNode pre = head;
            ListNode cur = head.next;
            while (cur != null) {
                if (cur.val == key) {
                    pre.next = cur.next;
                    return;
                }
                pre = cur;
                cur = cur.next;
            }
        }
    }
    //删除所有值为key的节点
    public void removeAllKey(int key) {
        if (head != null) {
            while (head != null && head.val == key) {
                head = head.next;
            }
            ListNode pre = null;
            ListNode cur = head;
            while (cur != null) {
                if (cur.val == key) {
                    pre.next = cur.next;
                }
                pre = cur;
                cur = cur.next;
            }
        }
    }
```
## 二、双向链表
### 1.双向链表的结构
双向链表是解决了单向链表只能从前往后遍历的缺点，内部有两个指针 `prev` 和 `next`，分别指向链表的前驱节点和后继节点。

![图片来自https://zhuanlan.zhihu.com/p/249144171](4.png)

其中链表的头的前驱和尾的后继均指向null。

### 2.双向链表的实现
#### 节点设计
![图片来自https://zhuanlan.zhihu.com/p/249144171](5.png)
对于每个节点，都有储存数据的 `data`，前驱节点 `prev`， 后继节点 `next`。我们用 `head` 表示链表的头节点，并用 `last` 表示链表的尾节点。

实现如下：
```java
    static class ListNode {
        public int val;
        public ListNode prev;
        public ListNode next;

        public ListNode(int val) {
            this.val = val;
        }
    }
    public ListNode head;
    public ListNode last;
```
#### 链表的遍历
```java
    //查找是否包含关键字key是否在单链表当中
    public boolean contains(int key) {
        ListNode cur = head;
        while (cur != null) {
            if (cur.val == key) {
                return true;
            }
            cur = cur.next;
        }
        return false;
    }
    public int size() {
        int size = 0;
        ListNode cur = head;
        while (cur != null) {
            cur = cur.next;
            size++;
        }
        return size;
    }
    public void display() {
        ListNode cur = head;
        while (cur != null) {
            System.out.print(cur.val + " ");
            cur = cur.next;
        }
    }
    public void clear() {
        head = null;
        last = null;
    }
```
#### 添加节点
![图片来自https://zhuanlan.zhihu.com/p/249144171](6.png)
双向链表的添加节点如图所示，可以看到，我们需要改变的值有上一个节点的 `next`， 下一个节点的 `prev`，和插入节点的 `prev` 和 `next`。

而头和尾的节点删除只需要从 `head` 和 `last` 处进行操作即可。

具体实现如下：
```java
    public void addFirst(int data) {
        ListNode node = new ListNode(data);
        if (head == null) {
            head = node;
            last = node;
        } else {
            head.prev = node;
            node.next = head;
            head = node;
        }
    }
    //尾插法
    public void addLast(int data) {
        if (head == null) {
            addFirst(data);
        } else {
            ListNode node = new ListNode(data);
            last.next = node;
            node.prev = last;
            last = node;
        }

    }

    //任意位置插入,第一个数据节点为0号下标
    public boolean addIndex(int index,int data) {
        int len = size();
        if (index < 0 || index > len) {
            return false;
        } else if (index == 0) {
            addFirst(data);
        } else if (index == len) {
            addLast(data);
        } else {
            ListNode node = new ListNode(data);
            ListNode cur = head;
            for (int i = 0; i < index; i++) {
                cur = cur.next;
            }
            node.prev = cur.prev;
            node.next = cur;
            cur.prev.next = node;
            cur.prev = node;
        }
        return true;
    }
```
#### 删除节点
![双向链表的删除操作](7.png)
删除 `cur` 节点需要让前驱节点指向后驱节点，然后让后驱节点执行前驱节点，用代码表示就是 `cur.prev.next = cur.next; cur.next.prev = cur.prev`。
具体实现如下：
```java
    public void remove(int key) {
        if (!contains(key)) {
            return;
        }
        if (head.val == key) {
            head = head.next;
            if (head != null) {
                head.prev = null;
            }
        } else {
            ListNode cur = head;
            while (cur.next != null) {
                if (cur.val == key) {
                    cur.prev.next = cur.next;
                    cur.next.prev = cur.prev;
                    return;
                }
                cur = cur.next;
            }
            if (cur.val == key) {
                last = cur.prev;
                cur.prev.next = null;
            }
        }

    }
    //删除所有值为key的节点
    public void removeAllKey(int key) {
        if (!contains(key)) {
            return;
        }
        while (head.val == key) {
            head = head.next;
            if (head == null) {
                return;
            }
            head.prev = null;
        }
        ListNode cur = head;
        while (cur.next != null) {
            if (cur.val == key) {
                cur.prev.next = cur.next;
                cur.next.prev = cur.prev;
            }
            cur = cur.next;
        }
        if (cur.val == key) {
            last = cur.prev;
            cur.prev.next = null;
        }

    }
```
## 三、LinkedList的使用
LinkedList类是Java内置的数据结构，底层是双向链表。这使得我们不必每次都去手动去实现一个双向链表，而是直接调用现成的数据结构即可：

在集合框架下实现的接口和继承的父类如下：
![ListNode实现的接口和继承的类](8.png)
1. LinkedList实现了List接口
2. LinkedList的底层使用了双向链表
3. LinkedList没有实现RandomAccess接口，因此LinkedList不支持随机访问
4. LinkedList的任意位置插入和删除元素时效率比较高，时间复杂度为O(1)
5. LinkedList比较适合任意位置插入的场景

### 构造方法

| 方法 | 解释 |
|--|--|
| `LinkedList()` | 无参构造 |
| `public LinkedList(Collection<? extends E> c)` |  用实现了Collection的其他元素进行构造 |

### 迭代元素
一般有三种方法：for循环，for-each循环，以及用迭代器遍历

```java
// foreach遍历
	for (int e:list) {
		System.out.print(e + " ");
	}
	System.out.println();
// 使用迭代器遍历---正向遍历
	ListIterator<Integer> it = list.listIterator();
	while(it.hasNext()){
		System.out.print(it.next()+ " ");
	}
	System.out.println();
// 使用反向迭代器---反向遍历
	ListIterator<Integer> rit = list.listIterator(list.size());
	while (rit.hasPrevious()){
		System.out.print(rit.previous() +" ");
	}
	System.out.println();
```
### 常用方法
根据功能相似性，将 `List` 接口中的方法进行合并，提取共同点，形成以下表格：

| 方法 | 功能 |
| :--- | :--- |
| `boolean add(E e)`<br>`void add(int index, E element)`<br>`boolean addAll(Collection<? extends E> c)` | 添加元素或集合。<br>可尾插单个元素、在指定位置插入单个元素，或尾插整个集合。 |
| `E remove(int index)`<br>`boolean remove(Object o)` | 删除元素。<br>可按索引删除，或删除第一个匹配的指定对象。 |
| `E get(int index)`<br>`E set(int index, E element)` | 访问索引位置元素。<br>`get` 获取指定位置元素，`set` 将指定位置元素替换为新值并返回旧值。 |
| `int indexOf(Object o)`<br>`int lastIndexOf(Object o)` | 查找元素位置。<br>返回第一个或最后一个匹配对象的下标，未找到时返回 `-1`。 |
| `boolean contains(Object o)` | 判断是否包含指定对象。 |
| `void clear()` | 清空线性表中所有元素。 |
| `List<E> subList(int fromIndex, int toIndex)` | 截取列表的子列表（视图），包含起始索引，不包含结束索引。 |

