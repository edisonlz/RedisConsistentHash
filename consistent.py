#coding=utf-8
import bisect
import hashlib
import redis
import time
import logging
import settings

class ConsistentHashRing(object):
    """Implement a consistent hashing ring."""

    def __init__(self, replicas=160):
        """Create a new ConsistentHashRing.

        :param replicas: number of replicas.

        """
        self.replicas = replicas
        self._keys = []
        self._nodes = {}

    def _hash(self, key):
        """Given a string key, return a hash value."""

        return long(hashlib.md5(key).hexdigest(), 16)

    def _repl_iterator(self, nodename):
        """Given a node name, return an iterable of replica hashes."""

        return (self._hash("%s:%s" % (nodename, i))
        for i in xrange(self.replicas))

    def __setitem__(self, nodename, node):
        """Add a node, given its name.
            The given nodename is hashed
            among the number of replicas.
        """

        for hash_ in self._repl_iterator(nodename):
            if hash_ in self._nodes:
                raise ValueError("Node name %r is "
                                 "already present" % nodename)
            self._nodes[hash_] = node
            bisect.insort(self._keys, hash_)

    def __delitem__(self, nodename):
        """Remove a node, given its name."""

        for hash_ in self._repl_iterator(nodename):
            # will raise KeyError for nonexistent node name
            del self._nodes[hash_]
            index = bisect.bisect_left(self._keys, hash_)
            del self._keys[index]

    def __getitem__(self, key):
        """Return a node, given a key.

        The node replica with a hash value nearest
        but not less than that of the given
        name is returned.   If the hash of the
        given name is greater than the greatest
        hash, returns the lowest hashed node.

        """
        hash_ = self._hash(key)
        start = bisect.bisect(self._keys, hash_)
        if start == len(self._keys):
            start = 0
        return self._nodes[self._keys[start]]


class RedisHashClient(object):
    """
        Consistent Hash Redis Client
    """


    def __init__(self, hosts_config):
        hosts = hosts_config.get("hosts")
        self.consistent_ring = ConsistentHashRing()
        self.redis_list = []

        for h in hosts:
            nodename = "%s:%s" % (h["host"], h["port"])
            r = redis.StrictRedis(host=h["host"], port=h["port"])
            self.redis_list.append(r)
            self.consistent_ring[nodename] = r

    def hget(self, key, field):
        client = self.consistent_ring[key]
        return client.hget(key, field)

    def hdel(self, key, field):
        client = self.consistent_ring[key]
        return client.hdel(key, field)

    def hset(self, key, field, value):
        client = self.consistent_ring[key]
        return client.hset(key, field, value)


    def set(self, key, value):
        client = self.consistent_ring[key]
        try:
            return client.set(key, value)
        except Exception, e:
            logging.error(e)
            return None


    def get(self, key):
        client = self.consistent_ring[key]
        try:
            return client.get(key)
        except Exception, e:
            logging.error(e)
            return None


    def expire(self, key, seconds=60 * 60 * 24 * 7):
        client = self.consistent_ring[key]
        client.expire(key, seconds)


    def ttl(self, key):
        client = self.consistent_ring[key]
        client.ttl(key)


    def hlen(self, key):
        client = self.consistent_ring[key]
        return client.hlen(key)


    def lpush(self, name, value):
        key = value
        client = self.consistent_ring[key]
        return client.lpush(name, value)

    def brpop(self, name):
        key = value
        client = self.consistent_ring[key]
        return client.brpop(name)

    def llen(self, key):
        client = self.consistent_ring[key]
        return client.llen(key)


if __name__ == "__main__":
    hosts = []

    for i in range(6):
        hosts.append({"host": "10.105.28.41", "port": 6379 + i})

    now = time.time()
    rhclient = RedisHashClient(settings.redis_config)
    print "initial use:", time.time() - now

    now = time.time()
    test_count = 1000

    now = time.time()
    for i in xrange(test_count):
        key = "test%s" % i
        attr = "xxxxxx"
        value = "1"
        a = rhclient.hset(key, attr, value)
        assert rhclient.hget(key, attr) == value
        if i % 1000 == 0:
            print "deal with:%s" % i

    print "hget&hset use:", time.time() - now, (time.time() - now) * 1.0 / test_count

    now = time.time()
    test_count = 1000
    for i in xrange(test_count):
        name = "test_queue%s" % i
        value = "1"
        rhclient.lpush(name, value)
        assert value == rhclient.brpop(name)[1]
        if i % 1000 == 0:
            print "deal with:%s" % i

        
    print "lpush&rpop use:", time.time() - now, (time.time() - now) * 1.0 / test_count

    for r in rhclient.redis_list:
        print r.info()["used_memory_human"]

        

