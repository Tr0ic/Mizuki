---
title: MIT-Missing-Semester Lecture1整理和习题答案
published: 2025-12-02
pinned: false
description: 对于MIT课程内容的整理
tags: [PowerShell, Linux]
category: Linux
licenseName: "Unlicensed"
author: Memorin
sourceLink: "https://blog.csdn.net/2501_93882415/article/details/155483208?spm=1001.2014.3001.5502"
draft: false
date: 2025-12-02
image: "./cover.jpg"
pubDate: 2025-12-02
---

# MIT-Missing-Semester Lcture1整理和习题答案

以下内容均在 WSL 的 powershell 运行

## 目录

- \1. `date` —— 获取系统时间
- \2. `echo` —— 参数与内容打印
- \3. 程序搜索与环境变量 PATH
- \4. Shell 中的目录导航
- \5. `ls` —— 查看文件与权限
- \6. 重定向与管道：< > >> |
- \7. `mkdir` —— 创建文件夹
- \8. 课程补充与课后习题说明

课程内容整理

### 1.date——获取时间：

```bash
memo@Troic16:/$ date
Tue Dec 2 09:40:47 CST 2025
```

### 2.echo——参数打印

（包括字符串，变量的值等）

虽然说下面的“Hello World"不加双引号也可以输出,但为了避免特殊参数的干扰
还是加上比较好。
也可以用转义字符告诉计算机这个空格也要算进去。
单引号和双引号的区别之后会提到。

```bash
memo@Troic16:/$ echo hello
hello
memo@Troic16:/$ echo Hello World
Hello World
memo@Troic16:/$ echo "Hello World"
Hello World
memo@Troic16:/$ echo Hello\ World
Hello World
memo@Troic16:/$ echo 'Hello World'
Hello World
```

### 3.搜索程序（环境变量$PATH——路径变量）

上面提到了，`echo` 可以打印变量，环境变量当然也是变量，因此可以通过打印
路径变量 PATH 得到计算机查找 `echo`，`data` 这些内置程序的绝对路径

```bash
memo@Troic16:~$ echo $PATH
/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/usr/lib/wsl/lib:/mnt/d/mingw64/bin:/mnt/c/Program Files (x86)/Windows Kits/10/Windows Performance Toolkit/:/mnt/c/Program Files/Git/cmd:/mnt/c/Program Files/TortoiseGit/bin:/mnt/c/Users/zzj06/.cargo/bin:/mnt/d/Scripts/:/mnt/d/:/mnt/c/Users/zzj06/AppData/Local/Programs/Python/Launcher/:/mnt/c/Users/zzj06/AppData/Local/Microsoft/WindowsApps:/mnt/d/Microsoft VS Code/bin:/mnt/c/msys64/ucrt64/bin:/snap/bin
memo@Troic16:~$ which echo
/usr/bin/echo
memo@Troic16:~$ /usr/bin/echo $PATH
/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/usr/lib/wsl/lib:/mnt/d/mingw64/bin:/mnt/c/Program Files (x86)/Windows Kits/10/Windows Performance Toolkit/:/mnt/c/Program Files/Git/cmd:/mnt/c/Program Files/TortoiseGit/bin:/mnt/c/Users/zzj06/.cargo/bin:/mnt/d/Scripts/:/mnt/d/:/mnt/c/Users/zzj06/AppData/Local/Programs/Python/Launcher/:/mnt/c/Users/zzj06/AppData/Local/Microsoft/WindowsApps:/mnt/d/Microsoft VS Code/bin:/mnt/c/msys64/ucrt64/bin:/snap/bin
```

这里的/usr/bin/echo 其实就是用` echo `的**绝对路径**运行，等效于 `echo $PATH`，比如：

```bash
memo@Troic16:~$ /usr/bin/echo hello
hello
```

用**相对路径**就要保证路径正确了，==在不同工作目录的相对路径是不同的==，比如：

```bash
memo@Troic16:/$ ./usr/bin/echo hello
hello
memo@Troic16:/$ cd usr
memo@Troic16:/usr$ ./usr/bin/echo hello
-bash: ./usr/bin/echo: No such file or directory
```

### 4.在 shell 导航

`cd`——切换目录，`pwd`——查看当前目录

根目录——`/`，主目录——`~`，当前目录——`.`，父目录——`..`，返回上一个目录——`-`

cd 绝对路径——直接到达对应路径
cd 相对路径——从当前工作目录开始导航

```bash
memo@Troic16:/usr$ cd ./bin
memo@Troic16:/usr/bin$ cd ..
memo@Troic16:/usr$ cd -
/usr/bin
memo@Troic16:/usr/bin$ cd ~
memo@Troic16:~$ pwd
/home/memo
memo@Troic16:~$ cd /home/memo/graph_projects
memo@Troic16:~/graph_projects$ cd ../../../usr/bin
memo@Troic16:/usr/bin$ ./echo hello
hello
memo@Troic16:/usr/bin$ pwd
/usr/bin
```

### 5.ls——显示文件

```bash
memo@Troic16:/$ ls
bin boot etc init lib.usr-is-merged lost+found mnt proc run sbin.usr-is-merged srv tmp var
bin.usr-is-merged dev home lib lib64 media opt root sbin snap sys usr
memo@Troic16:/$ ls -l
total 2740
lrwxrwxrwx 1 root root 7 Apr 22 2024 bin -> usr/bin
drwxr-xr-x 2 root root 4096 Feb 26 2024 bin.usr-is-merged
drwxr-xr-x 2 root root 4096 Apr 22 2024 boot
```

太长了就不一一展示了

-l 可以显示更加详细的信息，比如 rwx 就可以反映用户的读写运行的权限

（一共有三组 rwx，它们分别代表了文件所有者，用户组（users）以及其他所有人具有的权限。其中 - 表示该用户不具备相应的权限。从上面的信息来看，只有文件所有者可以修改（w）文件夹（例如，添加或删除文件夹中的文件）。可以使用 chmod 开放）

可以用 `man ls `或者` ls --help `查看更多参数和介绍

### 6.重定向 —— < , | , >

`cat`——显示文件信息

避免复制粘贴，简单说就是，`< ` `>`是在数据流中给出一个方向，让输入输出可以进行传递。比如：

```bash
memo@Troic16:~$ echo hello > hello.txt
memo@Troic16:~$ cat hello.txt
hello
memo@Troic16:~$ cat < hello.txt > hello2.txt
memo@Troic16:~$ cat hello2.txt
hello
memo@Troic16:~$ echo "world" >> hello2.txt
memo@Troic16:~$ cat hello2.txt
hello
world
```

顺带一提，`echo 'world' >hello2.txt `会直接替代掉原文本，>>是给文件追加内容

`|` 的作用是将上一个程序的输出变成下一个程序的输入，比如：

```bash
memo@Troic16:~$ cat hello2.txt | head -1 > hello1.txt
memo@Troic16:~$ cat hello1.txt
hello
memo@Troic16:~$ cat hello2.txt | tail -1 >> hello1.txt
memo@Troic16:~$ cat hello1.txt
hello
world

```

这里把` cat` 输出的 hello\nworld 作为 `head` 的输入，取第一行，保存进了 hello1.txt，因此得到了 hello，再取尾部第一行的 world，追加进 hello1.txt

但是要注意一点的是，==重定向的符号两侧**只负责传输数据**==，实际上右侧的程序是不知道左侧发生过了什么的，只是看到有数据传输过来了而已。

下面用 `sudo` 来解释这点，当我们尝试修改路径 /sys/class/backlight 下的文件的时候，因为没有管理员权限无法修改，自然地我们想着这么去解决

```bash
sudo echo 1 > brightness

```

但是这样是错误的，因为根据 ">" 进行划分我们会发现其实是`（sudo echo 1） > （brightness）`
而不是` sudo（echo 1 > brightness）`，==因此 `sudo `的管理员权限**只给到了 `echo`**，**而不是整个语句**==。

为什么呢，就是上面提到的重定向的符号只负责传输数据。

我们可以这么操作，这样` sudo `的权限就给到 `tee` 从而就可以对文件进行修改了。

```bash
echo 3 | sudo tee brightness

```

### 7.mkdir——创建文件夹

`mkdir` + 文件名

```bash
memo@Troic16:~$ mkdir missing
memo@Troic16:~$ ls
graph_projects hello.txt hello1.txt hello2.txt last-modified.txt missing my photos projects serverexample

```

需要注意的是如果要建立的文件夹名称带空格，要用引号括起来（mkdir "my photos"，如果用的是 my photos 就会像上面一样生成两个文件夹，一个是 my，一个是 photos)。

## 课后习题

[Solution-课程概览与 shell · the missing semester of your cs education]( [Solution-课程概览与 shell · the missing semester of your cs education](https://missing-semester-cn.github.io/missing-notes-and-solutions/2020/solutions/course-shell-solution/) )

需要注意的是，第五题的 semester 运行会显示 Permission denied，因为用户没有编辑的权限，用 chmod -777 文件名放开权限就可以了。

第九题也可以用 head 和 tail 混用来获得单行的内容。

WSL 的用户没有第十题的文件？其实我前面的 brightness 和这道题的电量文件夹下面都是空。

