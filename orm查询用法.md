看到 depts：哦，要去关联的部门表找。

看到 __name：哦，要看部门表里的 name 字段。

看到 __icontains：哦，要做模糊匹配。
模糊搜索：name__icontains="AGV"

数值比较：level__gte=10

范围查询：id__in=[1, 2, 3]

判空处理：pid__isnull=True

时间提取：created_at__year=2026

1. 基础匹配（搜索与筛选）
用于最常见的“根据名称、状态、类型”找数据。

__exact: 精确匹配（通常省略）。

User.filter(username="admin")

__icontains: 模糊搜索（不区分大小写），搜索框必备。

Job.filter(name__icontains="开发") → WHERE name LIKE '%开发%'

__startswith / __endswith: 匹配开头或结尾。

Role.filter(name__startswith="AGV_")

2. 数值与比较（电量、级别、排序）
在你的 AGV 系统里，处理电量、优先级或角色等级时必用。

__gt / __gte: 大于 / 大于等于 (Greater Than Equal)。

Role.filter(level__gte=10) → WHERE level >= 10

__lt / __lte: 小于 / 小于等于 (Less Than Equal)。

Agv.filter(battery__lt=20) → 查找电量低于 20% 的小车。

__in: 包含在列表中。

User.filter(id__in=[1, 5, 8]) → WHERE id IN (1, 5, 8)

__range: 范围查询（闭区间）。

Role.filter(level__range=(1, 5)) → 等同于 1 <= level <= 5

3. 空值与布尔（逻辑判断）
处理树形结构（如菜单父子关系）或启用状态。

__isnull: 判断是否为空。

Menus.filter(pid__isnull=True) → 查所有顶级菜单。

Menus.filter(pid__isnull=False) → 查所有子菜单。

直接布尔值:

User.filter(enabled=True) → 查活跃用户。

4. 时间提取（日志、报表）
用于按时间段统计任务。

__year / __month / __day: 提取特定时间单位。

Task.filter(created_at__year=2026)

__date: 提取具体日期。

Task.filter(created_at__date="2026-03-29")

5. 跨表穿透（核心灵魂）
通过双下划线直接访问关联表的字段。注意：前提是你在 Model 里定义了 ForeignKey 或 ManyToMany。

多对一 / 一对一:

OnlineUser.filter(user__username="admin") → 查“用户名为 admin”的在线状态。

多对多（你的 RBAC 核心）:

Role.filter(menus__title__icontains="控制") → 查“拥有‘控制’相关菜单权限”的所有角色。

User.filter(dept__name="技术部") → 查“技术部”的所有员工。