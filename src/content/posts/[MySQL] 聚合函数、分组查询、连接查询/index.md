---
title: "[MySQL] 聚合函数、分组查询、连接查询"
published: 2026-07-24T20:48:11+08:00
updated: 2026-07-24T20:50:37+08:00
description: "画师：竹取工坊大佬们好！我是Mem0rin！现在正在准备自学转码。如果我的文章对你有帮助的话，欢迎关注我的主页，一起进步！"
tags: ["MySQL", "数据库"]
category: "MySQL"
author: "Mem0rin"
sourceLink: "https://blog.csdn.net/2501_93882415/article/details/163172860"
draft: false
pinned: false
---

## 目录

- [一、聚合函数](#一聚合函数)
  - [（一）通用语法](#一通用语法)
  - [（二）常用聚合函数](#二常用聚合函数)
  - [（三）NULL 值的处理](#三null-值的处理)
- [二、分组查询（GROUP BY）](#二分组查询group-by)
  - [（一）通用语法](#一通用语法-1)
  - [（二）WHERE 与 HAVING](#二where-与-having)
  - [（三）分组查询的注意事项](#三分组查询的注意事项)
- [三、连接查询（JOIN）](#三连接查询join)
  - [（一）通用语法](#一通用语法-2)
  - [（二）内连接示例](#二内连接示例)
  - [（三）综合示例](#三综合示例)

> 画师：竹取工坊![画师：竹取工坊](../_assets/csdn-c5298a62a7dd5233.jpeg)  
>  大佬们好！我是Mem0rin！现在正在准备自学转码。  
>  如果我的文章对你有帮助的话，欢迎关注我的主页[Mem0rin](https://blog.csdn.net/2501_93882415?spm=1010.2135.3001.10640)，一起进步！

---

---

## 一、聚合函数

聚合函数用于对一组数据进行计算，并返回一个汇总结果。没有分组时，查询到的全部数据会作为一组；使用 `GROUP BY` 后，每个分组会分别得到一个结果。

### （一）通用语法

```sql
SELECT aggregate_function([DISTINCT] expression)
FROM table_name
[WHERE condition];
```

语法模板中的方括号表示可选内容，编写 SQL 时不需要输入方括号。

`DISTINCT` 表示先去除重复值，再进行聚合计算，可以根据需要省略。

### （二）常用聚合函数

| 函数 | 说明 |
| --- | --- |
| `COUNT(*)` | 统计查询结果的行数 |
| `COUNT([DISTINCT] expression)` | 统计表达式中非 `NULL` 值的数量 |
| `SUM([DISTINCT] expression)` | 计算数值的总和 |
| `AVG([DISTINCT] expression)` | 计算数值的平均值 |
| `MAX(expression)` | 查询最大值 |
| `MIN(expression)` | 查询最小值 |

例如，统计考试记录数量，并查询语文成绩的平均值、最高分和最低分：

```sql
SELECT
    COUNT(*) AS student_count,
    AVG(chinese) AS avg_chinese,
    MAX(chinese) AS max_chinese,
    MIN(chinese) AS min_chinese
FROM exam;
```

`SUM()` 和 `AVG()` 主要用于数值计算；`MAX()` 和 `MIN()` 还可以比较字符串、日期等可排序的数据。

### （三）NULL 值的处理

除 `COUNT(*)` 外，常用聚合函数都会忽略参与计算的 `NULL` 值。因此，`COUNT(*)` 统计结果行数，而 `COUNT(english)` 只统计英语成绩不为 `NULL` 的行数。

```sql
SELECT
    COUNT(*) AS total_count,
    COUNT(english) AS english_count
FROM exam;
```

聚合函数也可以对表达式进行计算：

```sql
SELECT AVG(chinese + english + math) AS avg_total_score
FROM exam;
```

需要注意的是，只要某一行的语文、英语或数学成绩中存在 `NULL`，这一行的加法结果就是 `NULL`，因此不会参与平均值计算。

## 二、分组查询（GROUP BY）

`GROUP BY` 会按照指定字段将数据划分为多个分组，再对每个分组分别进行聚合计算。例如，可以按照员工职位分组，计算每种职位的平均工资。

### （一）通用语法

```sql
SELECT group_column, aggregate_function(expression)
FROM table_name
[WHERE row_condition]
GROUP BY group_column
[HAVING group_condition]
[ORDER BY sort_expression];
```

在分组查询中，`SELECT` 后通常只能出现分组字段和聚合表达式。需要按照多个字段分组时，可以在 `GROUP BY` 后依次列出这些字段。

### （二）WHERE 与 HAVING

`WHERE` 和 `HAVING` 都可以进行条件筛选，但二者的作用阶段不同：

| 子句 | 筛选对象 | 书写位置 |
| --- | --- | --- |
| `WHERE` | 分组前的数据行 | `FROM` 之后、`GROUP BY` 之前 |
| `HAVING` | 分组后的结果 | `GROUP BY` 之后 |

下面按照职位分组，并筛选平均工资大于 10000 且小于 200000 的职位：

```sql
SELECT role, AVG(salary) AS avg_salary
FROM emp
GROUP BY role
HAVING AVG(salary) > 10000
    AND AVG(salary) < 200000;
```

可以将查询过程简单理解为：先用 `WHERE` 筛选数据行，再使用 `GROUP BY` 分组并计算聚合结果，最后使用 `HAVING` 筛选分组。

### （三）分组查询的注意事项

分组查询应先确定“按照什么字段分组”，再决定“每组需要统计什么数据”。如果查询的字段既没有参与分组、也没有放入聚合函数，并且不能由分组字段唯一确定，那么在启用 `ONLY_FULL_GROUP_BY` 模式时会产生错误。

## 三、连接查询（JOIN）

实际开发中，数据通常会被拆分到多张表中，以减少重复数据和增删改异常。连接查询可以根据表之间的关联字段，将多张表的数据组合到同一行中。

### （一）通用语法

```sql
SELECT alias1.column1, alias2.column2
FROM table1 AS alias1
[INNER] JOIN table2 AS alias2
    ON alias1.related_column = alias2.related_column
[WHERE condition];
```

`INNER JOIN` 表示内连接，只保留两张表中满足连接条件的数据，其中 `INNER` 可以省略。

### （二）内连接示例

编写连接查询时，可以按照以下步骤进行：

1. 确定参与查询的数据表。
2. 根据主键、外键或其他关联字段确定连接条件。
3. 使用“表别名.字段名”选择需要展示的字段。

例如，学生表 `student` 通过 `class_id` 与班级表 `class` 关联，可以查询学生及其班级名称：

```sql
SELECT
    s.id,
    s.name,
    c.name AS class_name
FROM student AS s
JOIN class AS c
    ON s.class_id = c.class_id;
```

如果省略连接条件，会得到两张表的笛卡尔积，产生大量无效的组合数据。因此，多表查询必须先确认表之间的关联关系。

### （三）综合示例

给定课程表 `course` 和成绩表 `score`，查询平均分在 50～80 分之间的课程，并按照平均分升序排列：

```sql
SELECT
    c.course_id,
    c.name AS course_name,
    AVG(s.score) AS avg_score
FROM course AS c
JOIN score AS s
    ON c.course_id = s.course_id
GROUP BY c.course_id, c.name
HAVING AVG(s.score) BETWEEN 50 AND 80
ORDER BY avg_score ASC;
```

这条语句先连接课程表和成绩表，再按照课程分组并计算平均分，随后使用 `HAVING` 筛选分组，最后使用 `ORDER BY` 排序。`BETWEEN 50 AND 80` 包含 50 和 80 两个边界值。

聚合函数负责汇总数据，`GROUP BY` 负责划分分组，`HAVING` 负责筛选分组结果，而 `JOIN` 负责组合多张表。理解这些关键字各自的作用阶段，可以更容易地编写复杂查询。
