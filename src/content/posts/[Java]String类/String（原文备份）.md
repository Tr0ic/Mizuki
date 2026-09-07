---
title: Java：String类
published: 2026-03-20
pinned: false
description: Java中String类的定义、创建、比较和常用方法。
tags: [Java]
category: Java
licenseName: "MIT"
author: Mem0rin
sourceLink: "https://blog.csdn.net/2501_93882415/article/details/159252153?spm=1001.2014.3001.5502"
draft: False
date: 2026-03-20
image: "./cover.jpg"
pubDate: 2026-03-20
---

## 文章目录
- [一、字符串的创建](#一字符串的创建)
- [二、字符串的比较](#二字符串的比较)
- [三、字符串的不可变性](#三字符串的不可变性)
- [四、常用字符串函数](#四常用字符串函数)



## 一、字符串的创建
有以下常见的有以下四种：
```java
//字符串字面值定义
String s1 = "hello world";
//构造方法传参
String s2 = new String("hello world");
//利用字符数组传参
char[] c = {'h','e','l','l','o',' ','w', 'o' ,'r', 'l', 'd'};
String s3 = new String(c);
//valueOf()        
String s4 = String.valueOf(c);
```
但需要注意的是 `String` 类的对象在创建之后就不允许改变了，具体原因是因为在 `String` 类中，存放字符串的值的是被`private final`修饰的字节数组 `value` 。我们并不能在其他类访问 `value` 并对其中的值进行过修改，`String` 类也没有对应的修改方法。
如果想要一个可变的字符串的话可以用 `StringBuilder` 或者 `StringBuffer` 类进行定义。
关于这三者的区别会在后面慢慢说。

## 二、字符串的比较
### `==`比较字符串地址
字符串和其他对象变量一样，属于引用变量，变量名存放的是对象的地址，因此当我们运行 `s1 == s2` 的时候，其实是在比较两者的地址，也就是说判断的不是两个字符串的值是否相等，而是在判断这两个变量名是否指向同一个字符串。
比如我们运行如下的实例：
```java
String s1 = "hello world";
String s2 = new String("hello world");
String s3 = s1;

System.out.println(s1 == s2);
System.out.println(s1 == s3);
```
结果如下：
```
false
true
```
### `equals()` 方法判断字符串的值是否相等
如果我们需要比较两个字符串的值的话，可以用方法 `equals()`
比如以下实例：
```java
String s1 = "hello world";
String s2 = new String("hello world");
String s3 = s1;

System.out.println(s1.equals(s2));
System.out.println(s1.equals(s3));
```
结果为：
```
true
true
```
### `compareTo()` 方法比较字符串大小
如果想要比较出谁的字符串更大，可以用 `compareTo()` 方法。
`compareTo()` 方法的大小比较是按照字典排序的，从前到后比较每一个字符，一旦比较出大小就直接输出，因此字符串比较和字符串长度没有很大的关系。
比如以下实例：
```java
System.out.println(s1.compareTo(s3));
System.out.println(s1.compareTo("he"));
System.out.println(s1.compareTo("hero"));
```
得到的结果是：
```
0
9
-6
```
结果是整数的原因是 `compareTo()` 的返回值是 `int` 整数类型，如果运行 `s1.compareTo(s2)` 得到的结果为正数，说明s1比s2大，反之如果是负数，则s1比s2小，如果是0说明两个字符串相等。

## 三、字符串的不可变性
前面说到了字符串的不可变性及其原因，因此所有涉及修改字符串的方法都得创建一个新的对象，然后用这个新的对象覆盖掉原来的字符串对象。因此当涉及到字符串的修改的时候，应该尽量避免对 `String` 类型对象本身的修改。
例子是 `String` 类型对象的加法运算，在字符串通过加法串联的时候会不断新建并销毁对象，运算次数多的话效率会很低下。
因此当这个时候我们通常会采用可变的类型对象 `StringBuilder` 或者 `StringBuffer` 进行字符串的串联，具体操作如下：

```java
StringBuffer buffer = new StringBuffer("hello");
buffer.append(" world");
System.out.println(buffer);

StringBuilder builder = new StringBuilder("hello");
builder.append(" world");
System.out.println(builder);
```
我们现在讲一下 `StringBuffer` 类和 `StringBuilder` 类的区别。
两者最大的区别是 `StringBuilder` 不是线程安全的，而 `StringBuffer` 类通过加锁的机制，让同一个数据同时只能让一个线程进行访问，而不是多个线程一起修改到时候也不知道该保存谁的数据（这种数据我们叫做脏数据）
加锁的操作同样会牺牲一定的效率，因此单单从运行速度来讲，`StringBuilder` 是最快的。
## 四、常用字符串函数
### 字符串长度
`length()`
```java
public class StringDemo {

   public static void main(String args[]) {
      String palindrome = "Dot saw I was Tod";
      int len = palindrome.length();
      System.out.println( "String Length is : " + len );
   }
}
```
结果为17。

### 索引相关
| 方法 | 功能 |
| :--- | :--- |
| `char charAt(int index)` | 返回指定索引位置的字符。<br>若索引为负数或越界，抛出 `IndexOutOfBoundsException` |
| `int indexOf(int ch)`<br>`int indexOf(int ch, int fromIndex)`<br>`int indexOf(String str)`<br>`int indexOf(String str, int fromIndex)` | 返回指定字符（或字符串）第一次出现的位置。<br>可指定起始搜索位置。<br>未找到时返回 `-1` |
| `int lastIndexOf(int ch)`<br>`int lastIndexOf(int ch, int fromIndex)`<br>`int lastIndexOf(String str)`<br>`int lastIndexOf(String str, int fromIndex)` | 从后向前搜索，返回指定字符（或字符串）第一次出现的位置。<br>可指定起始搜索位置。<br>未找到时返回 `-1` |

### 截取子串相关
根据你的要求，将每个表格中功能相似的方法合并为一行，提取共同点。这里分别处理两个表格：

| 方法 | 功能 |
| :--- | :--- |
| `String[] split(String regex)`<br>`String[] split(String regex, int limit)` | 将字符串按正则表达式拆分。<br>可指定拆分的最大组数 `limit`，若省略则全部拆分。 |
| `String substring(int beginIndex)`<br>`String substring(int beginIndex, int endIndex)` | 截取字符串的子串。<br>可指定起始索引与结束索引（不含），若只传起始索引则截取到末尾。 |

### 字符串内容修改

| 方法 | 功能 |
| :--- | :--- |
| `String trim()` | 去掉字符串首尾空白字符，保留中间空格。 |
| `String toUpperCase()` | 将字符串中所有字符转换为大写。 |
| `String toLowerCase()` | 将字符串中所有字符转换为小写。 |
| `String replaceAll(String regex, String replacement)`<br>`String replaceFirst(String regex, String replacement)` | 使用正则表达式进行替换。<br>`replaceAll` 替换所有匹配项，`replaceFirst` 仅替换第一个匹配项。 |