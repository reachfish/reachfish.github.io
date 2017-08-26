---

title: memcached源码阅读1

---

[TOC]

* __item_alloc__

```c
item *item_alloc(char *key, size_t nkey, int flags, rel_time_t exptime, int nbytes)
```



