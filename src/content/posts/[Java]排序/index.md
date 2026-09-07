---
title: "[Java]排序"
published: 2026-04-22T21:03:46+08:00
updated: 2026-04-22T21:03:54+08:00
description: "整理插入、选择、堆、冒泡、快速和归并排序的实现，并比较它们的时间复杂度、空间复杂度和稳定性。"
tags: ["Java", "数据结构"]
category: "Java"
author: "Mem0rin"
sourceLink: "https://blog.csdn.net/2501_93882415/article/details/160410630"
draft: false
pinned: false
---

## 目录

- [一、时间复杂度、空间复杂度和稳定性](#一时间复杂度空间复杂度和稳定性)
  - [1. 时间复杂度](#1-时间复杂度)
  - [2. 空间复杂度](#2-空间复杂度)
  - [3. 稳定性](#3-稳定性)
- [二、插入排序](#二插入排序)
  - [1. 直接插入排序](#1-直接插入排序)
  - [2.哈希排序](#2哈希排序)
- [三、选择排序](#三选择排序)
  - [1. 选择排序](#1-选择排序)
  - [2. 堆排序](#2-堆排序)
- [四、交换排序](#四交换排序)
  - [1. 冒泡排序](#1-冒泡排序)
  - [2. 快速排序](#2-快速排序)
- [五、归并排序](#五归并排序)

> 画师：竹取工坊![画师：竹取工坊](../_assets/csdn-c5298a62a7dd5233.jpeg)  
>  大佬们好！我是Mem0rin！现在正在准备自学转码。  
>  如果我的文章对你有帮助的话，欢迎关注我的主页[Mem0rin](https://blog.csdn.net/2501_93882415?spm=1010.2135.3001.10640)，欢迎互三，一起进步！

---

---

接下来会介绍几种排序方法，并分析时间复杂度、空间复杂度和稳定性。希望能有所帮助。

## 一、时间复杂度、空间复杂度和稳定性

### 1. 时间复杂度

时间复杂度和空间复杂度都是相对于单位时间而言的，其中 `n` 可以理解为数据的大小，从而代表运行程序所需要的时间。

时间复杂度主要是由遍历和递归的次数和深度决定的，如果是能够由相对固定的，有限的时间内得出结果的则为O(1)。

其他则根据 `n` 趋近于无穷大的时候运行时间和 `n` 的正比关系决定，比如二分查找的时间复杂度就为O(logn)。

### 2. 空间复杂度

空间复杂度则是由创建临时变量占用的内存决定的。

如果是固定数量的临时变量，比如遍历数组求最大值的时候用到的 `max` 临时变量，当 `n` 趋近于无穷大的时候，内存占比趋于0，此时空间复杂度为O(1)。

其他则根据趋近于无穷相关小的时候创造的临时变量的数量和大小决定，比如快速排序的空间复杂度为O(logn)。

### 3. 稳定性

当数据本身存在先后关系的时候，比如班级排名，如果这个排序方法会打乱原有的先后关系，则我们称这样的排序方法是**不稳定**的。（比如本来是张三在李四的前面，但是在排序之后李四跑到了张三前面）

## 二、插入排序

### 1. 直接插入排序

可以理解成插入扑克牌，具体的操作就是把扑克牌往前遍历找到该有的位置然后插进去。

这样的操作需要保证前面的牌都是有序的，因此这是一个从小到大逐渐有序的过程。

在具体实现中，我们直接跳过第一张牌的插入，因为一张牌必定是有序的，之后往后抽取数据，往前遍历，直到数据介于前后之间或者遍历到最后，进行插入操作，具体实现如下：

```java
// 插入排序
    public static void insertSort(int[] arr){
        int i = 1;
        while (i < arr.length) {
            int j = i - 1;
            int tmp = arr[i];
            while (j >= 0 && arr[j] > tmp) {
                arr[j + 1] = arr[j];
                j--;
            }
            arr[j + 1] = tmp;
            i++;
        }
    }
```

这样的排序是稳定的，时间复杂度为O(n^2)，空间复杂度为O(1)。  
 而且需要注意的是在最好和最差情况下的直接插入排序的时间复杂度是不一样的，如果数组本身就是有序的话，只需要O(n)次遍历就可以实现。

### 2.哈希排序

哈希排序是多次的插入排序，是在现在数组中取出部分的数据进行排序，然后再不断增加排序的数据的数量，直到最后对整个数组进行排序。

我们采用等间隔的取数方式，用 `gap` 表示数和数的下标差，然后不断缩小 `gap` 直到1。

对于每次取出来的数据我们分别采用直接插入排序即可。

具体实现如下：

```java
        // 希尔排序
    public static void shellSort(int[] array){
        int gap = array.length / 2;
        for (; gap >= 1; gap /= 2) {
            shell(array, gap);
        }

    }
    //按照gap插入排序
    private static void shell(int[] array, int gap) {
        for (int i = gap; i < array.length; i++) {
            int tmp = array[i];
            int j = i - gap;
            for (; j >= 0; j -= gap) {
                if (array[j] > tmp) {
                    array[j + gap] = array[j];
                } else {
                    break;
                }
            }
            array[j + gap] = tmp;
        }
    }
```

需要注意的是哈希排序因为是间隔取数据进行排序，是不稳定的，比如对221进行哈希排序，得到的122，改变了原来的2的先后顺序。  
 时间复杂度目前没有的准确的说法，因为不同的取间隔方式有不同的时间复杂度，目前的说法是在O(n ^ 1.3)到O(n ^ 1.5)之间。空间复杂度为O(1)。

## 三、选择排序

选择排序的原理是从数组中找到最大（最小）的数据，并放在数组的开头（末尾）。常见的有选择排序和堆排序。

### 1. 选择排序

原理是找到最大的元素的下标，然后和数组最前面的数据交换。之后从第二个数据开始往后找到第二大的数据的下标交换，以此类推。

```java
    public static void swap(int[] array, int a, int b) {
        int tmp = array[a];
        array[a] = array[b];
        array[b] = tmp;
    }

    public static void selectSort(int[] array) {
        for (int i = 0; i < array.length; i++) {
            int minIndex = i;
            for (int j = i; j < array.length; j++) {
                if (array[minIndex] > array[j]) {
                    minIndex = j;
                }
            }
            swap(array, minIndex, i);
        }
    }
```

但是选择排序是不稳定的，比如：988，最后得到的889先后顺序不同。

时间复杂度为O(n2)，空间复杂度为O(1)。

还有一种选择排序的变式，在遍历的时候同时确定最大和最小值的值，然后再进行交换。因为时间复杂度并没有显著提升因此不做讨论。

### 2. 堆排序

建立在优先级队列的数据结构的排序方式，要升序排序只需要建立大根堆逐个弹出即可。

堆排序在[[Java/数据结构]PriorityQueue](https://blog.csdn.net/2501_93882415/article/details/160191949?spm=1001.2014.3001.5502)讲过了，故不再赘述。

```java
    public static void heapSort(int[] array) {
        int len = array.length;;
        for (int parent = len / 2; parent >= 0; parent--) {
            siftDown(array, parent, len);
        }
        for (int i = len - 1; i >= 0; i--) {
            swap(array, 0, i);
            siftDown(array,0, i);
        }
    }


    private static void siftDown(int[] array, int parent, int len) {
        int child = parent * 2 + 1;
        while (child < len) {
            if (child + 1 < len && array[child] < array[child + 1]) {
                child++;
            }
            if (array[child] > array[parent]) {
                swap(array, parent, child);
                parent = child;
                child = parent * 2 + 1;
            } else {
                break;
            }
        }
    }
```

时间复杂度为O(nlogn)，空间复杂度为O(1)，不稳定，反例为42(1)32(2)，第一次弹出为32(1)2(2)4，第二次弹出为2(1)2(2)34，第三次弹出为2(2)2(1)34。

## 四、交换排序

思想是通过不断交换，让小的数据往头（或者尾）走，大的数据往另一边走。

### 1. 冒泡排序

梦的开始。像是一个泡泡不断升到顶，原理是通过不断交换把最大（最小）的数据放到末尾。

```java
    public static void bubbleSort(int[] array) {
        int len = array.length;
        for (int i = 0; i < len; i++) {
            int flag = 1;
            for (int j = 0; j < len - i - 1; j++) {
                if (array[j + 1] < array[j]) {
                    swap(array, j, j + 1);
                    flag = 0;
                }
            }
            if (flag == 1) {
                break;
            }

        }
    }
```

我们对冒泡排序进行了简单的优化，也就是如果一次冒泡的过程中发现数据已经有序，则停止排序直接输出。  
 这样哪怕冒泡排序的时间复杂度为O(n2)，在数据已经有序的情况下却可以达到O(n)。  
 空间复杂度为O(1)。是稳定的。

### 2. 快速排序

快排是基于二叉树结构的排序方式，原理是确认一个点的下标后对左右两侧进行二分以此递归下去。

确认一个点的下标的充要条件是这个点前面的所有数据都比这个点的数据小，后面所有的数据都比这个点大。

我们不妨以最开始的点为参照，之后设置两个指针，分别指向左右两边往中间遍历，把比参照小的放在左边，大的放在右边，最后把参照的数据放在中间。

其中一种实现方式是分别定位到比参照大和小的两个数据，然后交换。代码如下：

```java
    private static int partition(int[] array, int start, int end) {
        int tmp = array[start];
        int right = end;
        int left = start;
        while (left < right) {
            while (left < right && array[right] >= tmp) {
                right--;
            }

            while (left < right && array[left] <= tmp) {
                left++;
            }

            swap(array, left, right);

        }
        swap(array, right, start);
        return right;
    }
```

或者是挖坑法，形象地说就是一开始把开头的数据挖出来，这个时候如果右边有比参照小的，就把数据挪过去，把坑填上，挪过去的数据原来的位置就是一个新坑，如果左边有数据比参照大，就把这个数据挪到坑里，更新新坑，以此往复。

代码如下：

```java
    private static int partition1(int[] array, int start, int end) {
        int index = start;
        int right = end;
        int left = start;
        while (left < right) {
            while (left < right && array[right] >= array[index]) {
                right--;
            }
            swap(array, index, right);
            index = right;

            while (left < right && array[left] <= array[index]) {
                left++;
            }

            swap(array, left, index);
            index = left;

        }
        return index;

    }
```

时间复杂度为O(nlogn)，空间复杂度为O(n)，是不稳定的。反例是322。

但是快速排序有一个问题就是在面对基本有序的数组时，反而会退化成O(n 2)，针对这种问题可以采用三数取中法，取开头末尾和中间的三个数的中位数作为参照即可，不过这也没办法完全改善这种情况就是了。

## 五、归并排序

原理是用分治思想把数组分成小份各自排序再合并。

```java
    //合并数组，经典入门算法题
    private static void merge(int[] array, int start, int mid, int end) {
        int[] tmp = new int[end - start + 1];
        int k = 0;
        int s1 = start;
        int s2 = mid + 1;
        while (s1 <= mid && s2 <= end) {
            if (array[s1] <= array[s2]) {
                tmp[k++] = array[s1++];
            } else {
                tmp[k++] = array[s2++];
            }
        }
        while (s1 <= mid) {
            tmp[k++] = array[s1++];
        }
        while (s2 <= end) {
            tmp[k++] = array[s2++];
        }
        for (int i = 0; i < k; i++) {
            array[i + start] = tmp[i];//i + start用于定位数组元素位置
        }
    }
    //指定首位的排序，用于递归
    private static void mergeSort(int[] array, int start, int end) {
        if (start >= end) {
            return;
        }
        int mid = (start + end) / 2;
        mergeSort(array, start, mid);//左边
        mergeSort(array, mid + 1, end);//右边
        merge(array, start, mid, end);//合并
    }

    // 归并排序---递归
    public static void mergeSort(int[] array){
        mergeSort(array, 0, array.length - 1);
    }
```

时间复杂度为O(nlogn)，空间复杂度为O(n)（因为创建了 `tmp` 数组）。  
 是稳定的。
