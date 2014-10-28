RedisConsistentHash
===================

Redis Consistent Hash For Python


How to Use:
```
rhclient = RedisHashClient(settings.redis_config)
key = "xxx"
a = rhclient.hset(key, "attr", " 1")
assert rhclient.hget(key, "attr") == 1
```

Use to be distribution Queue
```
rhclient.lpush(name, value)
assert value == rhclient.brpop(name)[1]
```

How to get redis list:
```
for r in rhclient.redis_list:
        print r.info()["used_memory_human"]
```