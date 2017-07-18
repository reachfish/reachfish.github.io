---
title: MySql知识点学习
---

### 数据类型

* 数值类型

tinyint(1字节),smallint(2字节),int(4字节),bigint(8字节)
float(4字节),double(8字节)

* 字符串

char(0-255个字节，定长字符串), varchar(0-65535个字节，变长字符串)
tinytext(0-255个字节，短文本字符串), text(0-65535个字节，长文本数据)
tinyblob(0-255个字节，二进制字符串), blob(0-65535个字节，长文本二进制字符串)


### 数据库

* 创建 

create dbname

* 删除 

drop dbname 

* 使用

use dbname

### 数据表

* 创建 

create table tblname

```mysql 
CREATE TABLE IF NOT EXISTS `runoob_tbl`(
	`runoob_id` INT UNSIGNED AUTO_INCREMENT,
	`runoob_title` VARCHAR(100) NOT NULL,
	`runoob_author` VARCHAR(40) NOT NULL,
	`submission_date` DATE,
	PRIMARY KEY ( `runoob_id` )
)ENGINE=InnoDB DEFAULT CHARSET=utf8;
```

* 删除 

drop table tblname


### 记录

* 插入 

insert into tblname (field1, field2, ...) values (value1, value2, ...)

* 查询

select col1, col2
from tblname 
[where clause]
[order by field1 [asc|desc], field2, ...]
[offset M]
[limit N]

* 更新 

update tblname set field1=value1, field2=value2, ...
[where clause]

* 删除 

delete frome tblname 
[where clause]

### 其它 

* 模糊匹配 

like '%com': 以com结尾，%类似正则式中的*。

* union 集合的并集

union 是无重复的并集，而 union all 是包含重复的并集。

select country from apps 
union [all] 
select country from websites;

* group by 分组

select ...
from ...
[where clause]
group by colm;

* join 连接

inner join(就是join):

SELECT a.runoob_id, a.runoob_author, b.runoob_count 
FROM runoob_tbl a INNER JOIN tcount_tbl b 
ON a.runoob_author = b.runoob_author;

left join:

right join:

* 索引

MySQL索引的建立对于MySQL的高效运行是很重要的，索引可以大大提高MySQL的检索速度。

但过多的使用索引将会造成滥用。因此索引也会有它的缺点：虽然索引大大提高了查询速度，同时却会降低更新表的速度，如对表进行INSERT、UPDATE和DELETE。因为更新表时，MySQL不仅要保存数据，还要保存一下索引文件。


create index idxname on tblname;
drop index idxname on tblname;
