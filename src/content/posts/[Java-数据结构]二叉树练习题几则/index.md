---
title: "[Java/数据结构]二叉树练习题几则"
published: 2026-04-15T10:27:25+08:00
updated: 2026-04-15T10:28:55+08:00
description: "画师：竹取工坊大佬们好！我是Mem0rin！现在正在准备自学转码。如果我的文章对你有帮助的话，欢迎关注我的主页，欢迎互三，一起进步！"
tags: ["Java", "数据结构"]
category: "Java"
author: "Mem0rin"
sourceLink: "https://blog.csdn.net/2501_93882415/article/details/160154554"
draft: false
pinned: false
---

## 目录

- [一、前序+中序 或 后序+中序求二叉树](#一前序中序-或-后序中序求二叉树)
- [二、两个节点的最近祖先](#二两个节点的最近祖先)
  - [1. 递归](#1-递归)
  - [2. 非递归](#2-非递归)
- [三、二叉树的遍历构造](#三二叉树的遍历构造)

> 画师：竹取工坊![画师：竹取工坊](../_assets/csdn-c5298a62a7dd5233.jpeg)  
>  大佬们好！我是Mem0rin！现在正在准备自学转码。  
>  如果我的文章对你有帮助的话，欢迎关注我的主页[Mem0rin](https://blog.csdn.net/2501_93882415?spm=1010.2135.3001.10640)，欢迎互三，一起进步！

---

---

挑了点我不是很熟悉的题目进行宣讲自己巩固一下，希望有所帮助。

## 一、前序+中序 或 后序+中序求二叉树

[Leetcode链接](https://leetcode.cn/problems/construct-binary-tree-from-preorder-and-inorder-traversal/)  
 给定两个整数数组 preorder 和 inorder ，其中 preorder 是二叉树的先序遍历， inorder 是同一棵树的中序遍历，请构造二叉树并返回其根节点。

我们采用递归的方式进行实现。

思路和之前做小题的思路是相同的，只需要从前序节点中找到根节点的位置，然后在中序节点中找到根节点，并把根节点的索引前后切割成左右子树，再对左树和右树的数组分别递归处理。

首先来实现找到根节点的功能，根节点可以通过前序节点来确定，那么需要做的就是找到对应的中序节点的位置。我们用 `findVal` 方法来实现：

```java
public int findVal(int val, int[] inorder) {
        int i = 0;
        for (;i < inorder.length; i++) {
            if (inorder[i] == val) {
                return i;
            }
        }
        return i;
    }
```

为了切割根节点前后的数组，我们采用索引指定范围的方法，用 `indexBegin` 指定树的左边界， `indexEnd` 指定右边界，`index` 指定根节点的位置，那么我们就可以给出递归实现树的构造的框架。

```java
public TreeNode buildTree(int[] inorder, 
                            int[] preorder,
                            int indexBegin, 
                            int indexEnd) {
        if (indexBegin > indexEnd) {
            return null;
        }
        // int val = ...
        TreeNode node = new TreeNode(val);

        int inIndex = findVal(val, inorder);
        node.left = buildTree(inorder, preorder, indexBegin, inIndex - 1);
        node.right = buildTree(inorder, preorder, inIndex + 1, indexEnd);
        
        return node;
    }
```

但现在我们面临一个问题，就是我们如何从前序遍历中读取根节点呢？

从前往后就行，但是为了让读取的进程不被递归重置，我们只能把指向前序遍历的索引设置为成员变量。

这下我们可以把整个代码完善出来了。

```java
class Solution {
    public int findVal(int val, int[] inorder) {
        int i = 0;
        for (;i < inorder.length; i++) {
            if (inorder[i] == val) {
                return i;
            }
        }
        return i;
    }

    public int preIndex;

    public TreeNode buildTree(int[] inorder, 
                            int[] preorder, 
                            int indexBegin, 
                            int indexEnd) {
        if (indexBegin > indexEnd) {
            return null;
        }
        int val = preorder[preIndex];
        TreeNode node = new TreeNode(val);
        preIndex++;

        int inIndex = findVal(val, inorder);
        node.left = buildTree(inorder, preorder, indexBegin, inIndex - 1);
        node.right = buildTree(inorder, preorder, inIndex + 1, indexEnd);
        
        return node;
    }
    
    public TreeNode buildTree(int[] preorder, int[] inorder) {
        preIndex = 0;
        return buildTree(inorder, preorder, 0, preorder.length - 1);
    }
    
}
```

后序遍历同理，但是需要注意的是有以下几点不同：

1. 后序遍历是从后往前寻找根节点的。
2. 因为是从后往前遍历，因此构造子树的顺序也是先构造右树再构造左树。

## 二、两个节点的最近祖先

[Leetcode链接](https://leetcode.cn/problems/lowest-common-ancestor-of-a-binary-tree/description/)

给定一个二叉树, 找到该树中两个指定节点的最近公共祖先。

百度百科中最近公共祖先的定义为：“对于有根树 T 的两个节点 p、q，最近公共祖先表示为一个节点 x，满足 x 是 p、q 的祖先且 x 的深度尽可能大（一个节点也可以是它自己的祖先）。”

我们采用递归和非递归两种方法进行解决：

### 1. 递归

我们的前提是 `p` 和 `q` 都在树内。那么就会有以下三种情况：

1. `p` 或 `q` 在树的根节点上
2. `p` 和 `q` 在树的两侧
3. `p` 和 `q` 在树的同侧

前两个情况的最近祖先都是 `root`，第三种情况只需要继续往下递归直到出现上面两种情况即可。

```java
    public TreeNode lowestCommonAncestor(TreeNode root, TreeNode p, TreeNode q) {
        if (root == null) {
            return null;
        }
        if (root == p || root == q) {
            return root;
        }

        TreeNode leftRoot = lowestCommonAncestor(root.left, p, q);
        TreeNode rightRoot = lowestCommonAncestor(root.right, p, q);

        if (leftRoot != null && rightRoot != null) {
            return root;
        }

        return leftRoot == null ? rightRoot : leftRoot;
    }
```

### 2. 非递归

我们使用栈的数据结构实现：

思想和“找到两个链表的交点”类似，但是区别在于二叉树是非线性的，因此只是记录节点之间的距离是不够的，而是需要保存下来从根节点到对应节点的路径。

我们对此的思路是，采用前序遍历，遍历到的节点都入栈，如果入栈的节点左右都没有找到，则出栈。

```java
    public Stack<TreeNode> findNode (TreeNode root, TreeNode p) {
        Stack<TreeNode> stack = new Stack<>();
        TreeNode cur = root;
        TreeNode prev = null;
        while (cur != null || !stack.isEmpty()) {
            while (cur != null) {
                stack.push(cur);
                if (cur == p) {
                    System.out.println("Find it");
                    return stack;
                }
                cur = cur.left;
            }
            TreeNode top = stack.peek();
            if (top.right == null || top.right == prev) {
                stack.pop();
                prev = top;
            } else {   
                cur = top.right;
            }
        }
        return stack;
    }


    public TreeNode lowestCommonAncestor(TreeNode root, TreeNode p, TreeNode q) {
        Stack<TreeNode> stack1 = findNode(root, p);
        Stack<TreeNode> stack2 = findNode(root, q);
        int size1 = stack1.size();
        System.out.println("size1 = " + size1);
        int size2 = stack2.size();
        System.out.println("size2 = " + size2);
        while (size1 > size2) {
            stack1.pop();
            size1--;
        }
        while (size2 > size1) {
            stack2.pop();
            size2--;
        }
        while (stack1.peek() != stack2.peek()) {
            stack1.pop();
            stack2.pop();
        }
        return stack1.pop();

    }
```

## 三、二叉树的遍历构造

[nowcoder链接](https://www.nowcoder.com/practice/4b91205483694f449f94c179883c1fef?tpId=60&&tqId=29483&rp=1&ru=/activity/oj&qru=/ta/tsing-kaoyan/question-ranking)

读入用户输入的一串先序遍历字符串，根据此字符串建立一个二叉树（以指针方式存储）。 例如如下的先序遍历字符串： ABC##DE#G##F### 其中“#”表示的是空格，空格字符代表空树。建立起此二叉树以后，再对二叉树进行中序遍历，输出遍历结果。

难度有点小大，关键在于如何用 “#” 去确定二叉树的形状。

明显的思路是如果遍历到的字符不为 “#” 则继续往下递归，如果为 “#”，则返回null。

简单的代码如下：

```java
if (c != '#) {
    TreeNode root = new TreeNode(c);
    root.left = createTree(str);
    root.right = createTree(str);
} else {
    return null
}
return root;
```

之后就是字符串遍历的问题，和上面的前序+中序构建二叉树的时候，遍历前序的方法一样，我们同样构建一个成员变量用于指向字符串遍历到的位置。

中序遍历在上一篇博客有说明，不再赘述。

具体实现如下：

```java
    static int i;  
    public static TreeNode createTree(String str) {  
        TreeNode root = null;    
        if (i < str.length()) {
            char c = str.charAt(i);
            i++;
            if (c != '#') {
                root = new TreeNode(c);
                root.left = createTree(str);
                root.right = createTree(str);
            }
            
        }
        return root;
    }

    // 中序遍历
    static void inOrder(TreeNode root) {
        if (root == null) {
            return;
        }
        inOrder(root.left);
        System.out.print(root.val);
        System.out.print(' ');
        inOrder(root.right);
    }

    public static void main(String[] args) {
        Scanner in = new Scanner(System.in);
        while (in.hasNext()) {
            i = 0;
            String str = in.nextLine();
            TreeNode node = createTree(str);
            inOrder(node);
        }
        
    }
```

如果题目没有给出 `main` 方法，只需要再写一个方法把 `i` 封装进去就好。
