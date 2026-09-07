---
title: 面向对象：类的定义和使用
published: 2026-01-20
pinned: false
description: Java面向对象编程中类的核心概念和使用方法。
tags: [Java, Class]
category: Java
licenseName: "MIT"
author: Mem0rin
sourceLink: "https://blog.csdn.net/2501_93882415/article/details/157183304?spm=1001.2014.3001.5502"
draft: False
date: 2026-01-20
image: "./cover.jpg"
pubDate: 2026-01-20
---

# 目录
- [一、Main方法和客户程序（client program）](#一main方法和客户程序client-program)
- [二、类的定义和使用](#二类的定义和使用)
    - [（一）定义和使用](#一定义和使用)
    - [（二）静态和实例方法 （static or  Non-static）](#二静态和实例方法-static-or--non-static)
    - [（三）实例创建的方式](#三实例创建的方式)
    - [（四）静态变量和实例变量（static or instance variable）](#四静态变量和实例变量static-or-instance-variable)
    - [（五）点表示法（dot notation）](#五点表示法dot-notation)
- [public static void main(String[] args)是什么东西？](#public-static-void-mainstring-args是什么东西)

面向对象的绝妙之处在于class的使用，下面的文章也会着重介绍这点，尝试解释类之间是如何联系和使用的。
# 一、Main方法和客户程序（client program）
首先一个java程序有且仅有一个main方法，作为整个函数的入口，我们不妨将其成为主函数。在以往的java程序的编写中，我们常把主函数和程序的其他部分放在同一个类中，但是这在面对大型项目的时候会冗长且难以维护。  
因此将程序的功能进行分区分别放入多个类，然后再调用函数和数据就有必要了，此时我们把其他的class称作**客户程序**。那么就会引申出这么一个问题：怎么使用别的类？
# 二、类的定义和使用
## （一）定义和使用
假设我们有一个`Group`的类，用于存放个人信息。并且我们希望能够用一个`GroupLauncher`的main方法对`Group`进行使用。我们可以写出以下的程序，结果为`Hello!!!`：  
Group：
```java
public class Group {
    public static void hello(){
        System.out.println("Hello!!!");
    }

}
```
GroupLauncher：
```java
public class GroupLauncher {
    public static void main(String[] args){
        Group.hello();
    }

}

```
在这里我们使用了`Group`并通过`GroupLauncher`进行调用，从而完成了打招呼的操作。
需要注意的是，调用的时候我们采用的是**点表示语法**，这在后面会详细的阐述。
## （二）静态和实例方法 （static or  Non-static）
在上面的定义中我们给方法`hello`加上了修饰符`static`，从而表示这是一个静态函数，我们可以直接调用它。  
但我们知道，group中的人不可能都是一模一样的，我们需要一些针对特定的人的特定函数，所以我们把`static`去掉就得到了**实例方法**。  
实例方法要求创建一个实例，也就是面向对象中的对象”Object“，并且由这个实例进行调用。  
因此我们需要设置一个特定的人物，存储他的对应信息，并且用实例方法输出特定结果。  
不妨我们对原来的函数做出修改。  
Group：
```java
public class Group {

    public String name;
    public void hello(){
        System.out.println("Hello!!!I am " + name);
    }

}
```
GroupLauncher：
```java
public class GroupLauncher {
    public static void main(String[] args){
        Group jack;
        jack = new Group();
        jack.name = "Jack";
        jack.hello();
    }

}
```
输出的结果为`Hello!!!I am Jack`。  
让我们梳理这个代码讲了什么：  
① 我们通过`Group jack`和`jack = new Group()`创建了一个实例`jack`，相当于我们给jack这个人发了一张身份证，告诉电脑有这么一个人存在。  
② 我们通过`jack.name = "Jack"`传递数据，存储实例的信息，相当于告诉电脑这个人的名字是jack。  
③ 用实例方法输出结果，得到了属于Jack的特定结果`Hello!!!I am Jack`。  
你可以类比成`int a`,`a = 1`。


我们可以用下面的两个方法进行对比实例方法和静态方法的区别。  

现在我们分别用实例方法和静态方法写一下比较年龄的函数：（这里我们假定两个人的年龄是不同的）

Group：
```java
public class Group {

    public String name;

    public int age;
    public void hello(){
        System.out.println(name + " is older");
    }

    public Group older(Group p){
        if (age > p.age) {
            return this;
        }
        return p;
    }

    public static Group staticOlder(Group p1, Group p2) {
        if (p1.age > p2.age) {
            return p1;
        }
        return p2;
    }

}
```
GroupLauncher:
```java
public class GroupLauncher {
    public static void main(String[] args){
        Group jack;
        jack = new Group();
        jack.name = "Jack";
        jack.age = 20;
        Group kitty;
        kitty = new Group();
        kitty.name = "Kitty";
        kitty.age = 18;
        Group p1 = Group.staticOlder(jack, kitty);
        Group p2 = jack.older(kitty);
        p1.hello();
        p2.hello();
    }

}
```

运行结果都是`Jack is older`。

==实例方法的核心在于特定二字==，也就是说，实例方法只能被实例调用，要求不同的实例运行实例方法会有不一样的结果。而静态方法则是只能被类自己调用，按照固定流程运行，运行结果仅与参数有关，通常在不涉及类内部的变化，因此两者有不同的应用场景 。比如Math库的sqrt，因为仅作为计算的工具，因此我们只需要`Math.sqrt()`即可，如果要用实例方法，就会变得很别扭:
```java
Math m = new Math();
m.sqrt(5.6);
```
明明一行就能搞定的东西。

## （三）实例创建的方式
在上面的代码中，我们定义一个实例需要用四行，也就是
```java
Group jack;
jack = new Group();
jack.name = "Jack";
jack.age = 20;
```
这也太臃肿了，因此我们考虑是否有类似于`int a = 1`这种一步到位的创建方式呢？答案是有的，但是我们需要一个构建函数（Constructor），我们可以在里面设置好所有的参数：
```java
public Group(String n, int a){
        name = n;
        age = a;
    }
```
这样我们就可以很轻松地定义实例了：
```java
Group jack = new Group("Jack", 20);
Group kitty = new Group("Kitty", 18);
```

## （四）静态变量和实例变量（static or instance variable） 
同样是有无`static`的区别，实例变量是可以在创建实例的时候定义的部分，换而言之是每一个实例都会不同的变量，比如上面代码中的`name`和`age`，而静态变量则是对于每一个实例都是一样的。  
对于静态变量可以采取以下定义：
```java
public static String kind = "human";
```
表明实例的普遍特征（group里的都是人类），在调用时，尽管我们可以用`jack.kind`来访问，但是我们通常使用类名而不是实例，虽然实例可行，但是这并不是一个好的代码习惯。

## （五）点表示法（dot notation）
我们把类中的方法和变量都统一称作类的成员，而访问这些成员的方式就是点表示法，我们注意到在前面的代码中，不管是静态还是实例的变量和方法，我们都用（类名/实例）.（方法/变量）来进行访问。

# public static void main(String[] args)是什么东西？
**static** : 表明这是一个静态的方法，与特定的实例无关。  
**void**: 表明方法没有返回值。  
**main**：方法名。  
**String[] args**：方法的参数类型和名称。  
在命令行中，String[] args是函数的第一个参数，也就是说在通过`java GroupLauncher`运行代码的时候，如果我们在后面输入一些东西，就会存进args里。  
比如以下代码：
```java
public class ArgsDemo {
    public static void main(String[] args){
        int sum = 0;
        for (int i = 0; i < args.length; i = i + 1){
            sum = sum + Integer.parseInt(args[i]);
        }
        System.out.println(sum);
    }
}
```

当我们编译好了之后，在命令行输入`java ArgsDemo 1 2 3 4 5 10`，就会输出25.