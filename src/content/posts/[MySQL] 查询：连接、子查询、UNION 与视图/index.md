---
title: "[MySQL] 查询：连接、子查询、UNION 与视图"
published: 2026-08-11T15:53:50+08:00
updated: 2026-08-11T15:54:06+08:00
description: "结果中可能包含算法、定义者和安全上下文等信息，因此它比仅仅回忆原始SELECT更适合核对当前数据库中的真实定义。需要重复运行练习脚本时，可以先，再重新，避免同名对象已经存在导致脚本中断。"
tags: ["MySQL", "数据库"]
category: "MySQL"
author: "Mem0rin"
sourceLink: "https://blog.csdn.net/2501_93882415/article/details/163669807"
draft: false
pinned: false
---

## 目录

- [一、统一示例](#一统一示例)
- [二、连接查询（JOIN）](#二连接查询join)
  - [（一）内连接](#一内连接)
  - [（二）左外连接与右外连接](#二左外连接与右外连接)
  - [（三）ORDER BY 与稳定顺序](#三order-by-与稳定顺序)
  - [（四）自连接要让别名体现角色](#四自连接要让别名体现角色)
- [三、子查询](#三子查询)
  - [（一）标量子查询](#一标量子查询)
  - [（二）IN 与多行子查询](#二in-与多行子查询)
  - [（三）行子查询](#三行子查询)
  - [（四）FROM 中的派生表](#四from-中的派生表)
  - [（五）相关 EXISTS](#五相关-exists)
  - [（六）为什么 EXISTS（SELECT NULL）仍然为真](#六为什么-existsselect-null仍然为真)
- [四、集合查询（UNION）](#四集合查询union)
  - [（一）UNION 与 UNION ALL](#一union-与-union-all)
  - [（二）每部分必须结构兼容](#二每部分必须结构兼容)
  - [（三）最终排序写在集合查询末尾](#三最终排序写在集合查询末尾)
- [五、视图](#五视图)
  - [（一）创建并查询视图](#一创建并查询视图)
  - [（二）查看定义与删除视图](#二查看定义与删除视图)
  - [（三）视图不一定可更新](#三视图不一定可更新)
  - [（四）视图的意义](#四视图的意义)

一条查询往往需要同时解决多个问题：从多张表补全信息、用另一条查询提供条件、合并多个结果集，或者把复杂查询封装成可复用的逻辑表。本文以 `student`、`class`、`course` 和 `score` 四张表为例，整理连接、子查询、`UNION` 与视图的核心用法及边界。

## 一、统一示例

后文使用以下四张表：

| 表 | 主要字段 | 含义 |
| --- | --- | --- |
| `student` | `id`、`name`、`class_id` | 学生及其所在班级 |
| `class` | `id`、`name` | 班级 |
| `course` | `id`、`name` | 课程 |
| `score` | `id`、`student_id`、`course_id`、`score` | 学生的课程成绩 |

示例数据中，张三和李四属于一班，王五属于二班，赵六的 `class_id` 为 `NULL`；三班暂时没有学生。这样的数据可以同时观察连接成功、左侧未匹配和右侧未匹配三种情况。

## 二、连接查询（JOIN）

### （一）内连接

内连接只保留连接条件能够匹配的组合。查询学生及其班级名称时，可以写成：

```sql
SELECT
    s.id AS student_id,
    s.name AS student_name,
    c.name AS class_name
FROM student AS s
INNER JOIN class AS c
    ON s.class_id = c.id;
```

`INNER` 可以省略。`ON` 后的条件描述两张表如何关联；如果遗漏连接条件，就会产生笛卡尔积，把两张表中的行两两组合，通常不是业务真正需要的结果。

当前示例中，张三、李四和王五能够找到班级，因此会出现在结果中。赵六没有班级，三班也没有学生，二者都不会被内连接保留。

### （二）左外连接与右外连接

外连接需要先判断“保留侧”。左外连接完整保留 `LEFT JOIN` 左边的表，右外连接完整保留右边的表；另一侧没有匹配行时，其列使用 `NULL` 补齐。

以学生为保留侧：

```sql
SELECT
    s.id AS student_id,
    s.name AS student_name,
    c.name AS class_name
FROM student AS s
LEFT JOIN class AS c
    ON s.class_id = c.id
ORDER BY s.id;
```

四名学生都会出现。赵六没有匹配的班级，因此该行的 `class_name` 为 `NULL`。

以班级为保留侧，可以交换表的位置继续使用 `LEFT JOIN`，也可以使用 `RIGHT JOIN`：

```sql
SELECT
    c.id AS class_id,
    c.name AS class_name,
    s.name AS student_name
FROM student AS s
RIGHT JOIN class AS c
    ON s.class_id = c.id
ORDER BY c.id, s.id;
```

三个班级都会出现。三班没有学生，因此该行的 `student_name` 为 `NULL`。

### （三）ORDER BY 与稳定顺序

关系表本身没有可依赖的默认行顺序。即使同一条 SQL 连续执行时看起来顺序相同，优化器选择、索引、数据分布或版本变化也都可能改变返回顺序。

需要稳定结果时，必须显式写出足以确定顺序的条件：

```sql
ORDER BY c.id ASC, s.id ASC;
```

### （四）自连接要让别名体现角色

自连接不是特殊的连接类型，而是让同一张表以不同角色参与多次查询。例如，查询“计算机原理成绩高于 Java 成绩”的学生时，两份 `score` 分别代表 Java 成绩和计算机原理成绩：

```sql
SELECT
    s.id AS student_id,
    s.name AS student_name
FROM student AS s
JOIN score AS java_score
    ON java_score.student_id = s.id
JOIN course AS java_course
    ON java_course.id = java_score.course_id
JOIN score AS cs_score
    ON cs_score.student_id = s.id
JOIN course AS cs_course
    ON cs_course.id = cs_score.course_id
WHERE java_course.name = 'Java'
  AND cs_course.name = '计算机原理'
  AND cs_score.score > java_score.score
ORDER BY s.id;
```

`java_score` 与 `cs_score` 比 `s1`、`s2` 更容易检查，因为别名直接说明了每一份数据的角色。连接顺序可以拆成三步理解：先保证两条成绩属于同一名学生，再确定各自课程，最后比较分数。

如果数据模型允许同一学生出现多条同课程成绩，连接可能产生多种组合。此时应先确认业务需要哪一条记录，或者从表约束上避免无意义的重复。

## 三、子查询

子查询是嵌入另一条 SQL 的查询。选择哪种子查询，关键不在于“嵌套了几层”，而在于内层结果是一格、一列多行、一行多列，还是一张临时结果表。

### （一）标量子查询

标量子查询必须返回至多一行一列，可以像一个普通值一样参与比较。例如，查询与张三同班但排除张三本人的学生：

```sql
SELECT
    id,
    name,
    class_id
FROM student
WHERE class_id = (
    SELECT class_id
    FROM student
    WHERE name = '张三'
)
  AND name <> '张三';
```

如果内层查询返回多行，MySQL 会报错，而不是自动选择其中一行。因此，用姓名查找唯一学生时，应确保姓名本身唯一，或者改用真正唯一的标识。若内层没有返回行，标量结果按 `NULL` 处理，与它进行普通等值比较不会得到真值。

### （二）IN 与多行子查询

当内层查询返回一列多行时，可以使用 `IN` 判断某个值是否属于结果集合。例如，查询 Java 或计算机原理课程的成绩：

```sql
SELECT
    id,
    student_id,
    course_id,
    score
FROM score
WHERE course_id IN (
    SELECT id
    FROM course
    WHERE name IN ('Java', '计算机原理')
)
ORDER BY student_id, course_id;
```

`IN` 后的子查询必须返回一个可比较的列，不能写成 `SELECT *`。`NOT IN` 还要额外注意 `NULL`：如果候选集合中含有 `NULL`，比较结果可能变成未知，从而得不到直觉中的“其余行”。需要表达“不存在匹配记录”时，相关 `NOT EXISTS` 往往更直接。

### （三）行子查询

MySQL 可以把多个字段组成一个行值，再与子查询返回的多列结果比较。例如，找出 `student_id`、`course_id` 和 `score` 完全相同且重复出现的成绩记录：

```sql
SELECT
    id,
    student_id,
    course_id,
    score
FROM score
WHERE (student_id, course_id, score) IN (
    SELECT
        student_id,
        course_id,
        score
    FROM score
    GROUP BY student_id, course_id, score
    HAVING COUNT(*) > 1
)
ORDER BY student_id, course_id, score, id;
```

外层左侧有三个值，内层也必须返回三个顺序和类型可以对应的列。内层负责找出重复组合，外层再返回这些组合对应的完整记录。

### （四）FROM 中的派生表

放在 `FROM` 中的子查询会形成派生表。它适合先完成一次分组或计算，再对结果继续筛选。例如，查询平均分不低于 90 分的学生：

```sql
SELECT
    student_avg.student_id,
    student_avg.avg_score
FROM (
    SELECT
        student_id,
        AVG(score) AS avg_score
    FROM score
    GROUP BY student_id
) AS student_avg
WHERE student_avg.avg_score >= 90
ORDER BY student_avg.student_id;
```

派生表需要别名，这里的 `student_avg` 就像一张只在本条语句中存在的表。外层查询只能访问派生表实际输出的列，因此内层应为计算结果起清晰的列别名。

### （五）相关 EXISTS

`EXISTS` 只判断子查询是否至少返回一行，不关心这一行具体选择了什么值。查询至少有一门成绩不低于 90 分的学生，可以写成：

```sql
SELECT
    s.id AS student_id,
    s.name AS student_name
FROM student AS s
WHERE EXISTS (
    SELECT 1
    FROM score AS sc
    WHERE sc.student_id = s.id
      AND sc.score >= 90
)
ORDER BY s.id;
```

`sc.student_id = s.id` 引用了外层当前学生，这使它成为相关子查询。可以理解为：对每名学生，检查成绩表中是否存在一条属于他且满足分数条件的记录。外层按学生返回，所以一名学生即使有多门高分课程，也只会出现一次。

### （六）为什么 EXISTS（SELECT NULL）仍然为真

下面的子查询没有 `FROM` 和过滤条件：

```sql
SELECT NULL;
```

它会返回一行，只是该行的值为 `NULL`。`EXISTS` 判断的是“有没有行”，而不是“这一行的值是否为 `NULL`”，在数学上进行类比，我们可以把它看作是空集的集合，空集的集合不是空集，所以 `EXISTS (SELECT NULL)` 为真：

```sql
SELECT
    id,
    name
FROM student
WHERE EXISTS (SELECT NULL);
```

这个条件与外层学生没有任何关联，因此所有学生都会通过，不能用于逐个判断学生是否有成绩。`SELECT 1`、`SELECT NULL` 或 `SELECT *` 在 `EXISTS` 中通常具有相同的存在性语义；真正决定结果的是子查询的 `FROM` 与 `WHERE` 能否产生行。

## 四、集合查询（UNION）

### （一）UNION 与 UNION ALL

`UNION` 把多条查询的结果纵向合并，并对完整结果行去重；`UNION ALL` 保留所有行，不执行这一步去重。

```sql
SELECT name AS student_name
FROM student
WHERE class_id = 1

UNION

SELECT name AS student_name
FROM student
WHERE name IN ('张三', '赵六');
```

张三同时满足两部分条件。使用 `UNION` 时只保留一行张三；改成 `UNION ALL` 后，两行张三都会保留。是否去重取决于业务语义，而不是查询来自一张表还是多张表。明确允许重复时，`UNION ALL` 避免了集合去重工作，通常也更直接。

### （二）每部分必须结构兼容

参与集合查询的每个 `SELECT` 必须返回相同数量的列，对应位置的数据类型也应兼容：

```sql
SELECT id, name
FROM student
UNION ALL
SELECT id, name
FROM another_student;
```

列名由第一条查询决定，因此建议在第一条查询中给输出列设置清晰别名。列的对应关系按位置判断，不会因为两个列恰好同名就自动调整顺序。

### （三）最终排序写在集合查询末尾

如果需要整个结果集稳定有序，应把 `ORDER BY` 写在最后，并使用最终输出列名：

```sql
SELECT id AS student_id, name AS student_name
FROM student
WHERE class_id = 1

UNION ALL

SELECT id AS student_id, name AS student_name
FROM student
WHERE class_id = 2

ORDER BY student_id;
```

这条 `ORDER BY` 作用于合并后的完整结果。不要依赖各分支当前看起来的输出顺序，也不要根据 `UNION` 的去重过程推断最终顺序。

## 五、视图

视图保存的是查询定义，可以像表一样被查询。普通视图不会保存一份独立的查询结果；查询视图时，结果仍来自它依赖的基表。因此，基表数据变化后，再次查询视图会看到相应变化。

### （一）创建并查询视图

下面把学生与班级的左连接封装成视图：

```sql
CREATE VIEW v_student_class (
    student_id,
    student_name,
    class_name
) AS
SELECT
    s.id,
    s.name,
    c.name
FROM student AS s
LEFT JOIN class AS c
    ON c.id = s.class_id;
```

列名列表与 `SELECT` 的输出列按位置对应。创建后，可以把视图当作查询入口：

```sql
SELECT
    student_id,
    student_name,
    class_name
FROM v_student_class
WHERE class_name = '一班'
ORDER BY student_id;
```

视图适合封装会反复使用的连接与计算，也可以只暴露业务需要的列。不过，视图只是查询接口，不会自动替代底层表的权限设计、索引设计或数据约束。

### （二）查看定义与删除视图

`SHOW CREATE VIEW` 可以查看 MySQL 保存的完整定义：

```sql
SHOW CREATE VIEW v_student_class;
```

结果中可能包含算法、定义者和安全上下文等信息，因此它比仅仅回忆原始 `SELECT` 更适合核对当前数据库中的真实定义。

删除视图不会删除它依赖的基表：

```sql
DROP VIEW IF EXISTS v_student_class;
```

需要重复运行练习脚本时，可以先 `DROP VIEW IF EXISTS`，再重新 `CREATE VIEW`，避免同名对象已经存在导致脚本中断。

### （三）视图不一定可更新

“可以查询”不等于“可以更新”。简单、能够明确映射到基表行的视图可能允许 `INSERT`、`UPDATE` 或 `DELETE`，但包含聚合函数、`DISTINCT`、`GROUP BY`、`HAVING`、集合操作等结构的视图通常不可更新。涉及多表连接时，还要根据实际定义判断，不能仅凭“它是视图”或“它用了连接”下结论。

可以从 `INFORMATION_SCHEMA.VIEWS` 检查 MySQL 对当前视图的判断：

```sql
SELECT
    TABLE_SCHEMA,
    TABLE_NAME,
    IS_UPDATABLE
FROM INFORMATION_SCHEMA.VIEWS
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'v_student_class';
```

本次课程实操中的 `LEFT JOIN` 视图返回 `IS_UPDATABLE = 'NO'`，因此只把它作为查询入口，不通过它修改数据。这个结果针对当前视图定义，不代表所有连接视图都必然得到同一结论。

### （四）视图的意义

视图的主要价值可以概括为三点：

- 复用查询：把重复出现的连接、筛选或计算集中到一个定义中。
- 简化接口：调用方只需查询视图，不必每次重写底层 SQL。
- 限制暴露列：结合正确的权限配置，只提供调用方需要的数据入口。
