---
title: mongodb知识点学习
---

* mongodb是面向文档的数据库，而不是关系型数据库。

## 键
* 键是字符串，除了少数例外情况，键可以使用任意UTF8字符
键不能含有\0。.和$具有特殊意义，这两个字符被保留。
* 每个文档都有一个特殊的见 \_id。
* 文档中不能含有重复的键
```mongodb
#err
{"a" : 1, "a" : 1} 
```
* 文档中的键值对是有序的
```mongodb
{"a" : 1, "b" : 2} 和 { "b" : 2, "a" : 1 } 是两个不同的文档。
```

## 基本操作
* 插入 table.insert(record)
* 插入文档数组 table.batchInsert(records)
* 读取 table.find(), table.findOne()
* 更新 table.update(select, new_value)
* 删除 table.remove(select)， 如果不指定select，则会删除所有记录。清空时，可以使用 table.drop()。

## 基本类型
* 整数 
  { "x" : NumberInt("3") } 或 { "x" : NumberLong("3") }
* 日期 
  { "x" : new Date() }
* 数组
  { "x" : [1,2,3] }
* 内嵌文档
  { "x" : { "foo" : "bar" } }
* 对象id，12个字节的Id，是文档的唯一标识。
  { "x" : ObjectId() }

## 更新
### 修改器
$inc 增加
$set 设置值
$unset 删除键值

$push 向已有的数组末尾增加一个元素，如果没有就创建一个新的数组
{ "$push" : { "comment" : {"$each" : [1,2,3,4]} } } //向comment末尾中分别添加1,2,3,4
