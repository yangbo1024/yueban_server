# -*- coding:utf-8 -*-

"""
Simulation of redis-zset with ASC|DESC order
"""

import bisect


class _AscNode(object):
    def __init__(self, key, score, order):
        self.key = key
        self.score = score
        self.order = order

    def __lt__(self, other):
        if self.score < other.score:
            return True
        if self.score > other.score:
            return False
        return self.order < other.order

    def __gt__(self, other):
        if self.score > other.score:
            return True
        if self.score < other.score:
            return False
        return self.order > other.order


class _DescNode(object):
    def __init__(self, key, score, order):
        self.key = key
        self.score = score
        self.order = order

    def __lt__(self, other):
        if self.score > other.score:
            return True
        if self.score < other.score:
            return False
        return self.order < other.order

    def __gt__(self, other):
        if self.score < other.score:
            return True
        if self.score > other.score:
            return False
        return self.order > other.order


class ZSet(object):
    """
    zset
    """
    def __init__(self, asc=True):
        self.nodedict = {}
        self.nodelist = []
        self.node_class = _AscNode if asc else _DescNode

    def index(self, key):
        node = self.nodedict.get(key)
        if not node:
            return -1
        left = bisect.bisect_left(self.nodelist, node)
        for i in range(left, len(self.nodelist)):
            if self.nodelist[i].key == node.key:
                return i
        return -1

    def zadd(self, key, score, order=0):
        idx = self.index(key)
        if idx < 0:
            order = order or 0
            node = self.node_class(key, score, order)
            bisect.insort_right(self.nodelist, node)
            self.nodedict[key] = node
            return
        node = self.nodelist[idx]
        self.nodelist.pop(idx)
        node.score = score
        if order is not None:
            node.order = order
        bisect.insort_right(self.nodelist, node)
        return 1

    def zrem(self, key):
        idx = self.index(key)
        if idx < 0:
            return 0
        self.nodedict.pop(key)
        self.nodelist.pop(idx)
        return 1

    def zremrangebyrank(self, start, end):
        card = len(self.nodelist)
        if end < 0:
            end = card
        if start < 0:
            start = 0
        start = min(start, card)
        end = min(end + 1, card)
        low = self.nodelist[:start]
        mid = self.nodelist[start:end]
        high = self.nodelist[end:]
        for node in mid:
            self.nodedict.pop(node.key)
        low.extend(high)
        self.nodelist = low

    def zrank(self, key):
        return self.index(key)

    def zrevrank(self, key):
        idx = self.index(key)
        if idx < 0:
            return -1
        return len(self.nodelist) - idx - 1

    def zscore(self, key):
        node = self.nodedict.get(key)
        if not node:
            return 0
        return node.score

    def zcount(self, start, end):
        leftnode = self.node_class("", start, 0)
        rightnode = self.node_class("", end, 0)
        right = bisect.bisect_right(self.nodelist, rightnode)
        left = bisect.bisect_left(self.nodelist, leftnode)
        return right - left

    def zcard(self):
        return len(self.nodelist)

    def zrange(self, start, end, withscores=False):
        if end < 0:
            end = len(self.nodelist)
        end = min(len(self.nodelist), end + 1)
        nodes = self.nodelist[start:end]
        if not nodes:
            return []
        if not withscores:
            return [n.key for n in nodes]
        else:
            return [(n.key, n.score) for n in nodes]

    def zrevrange(self, start, end, withscores=False):
        card = len(self.nodelist)
        if end < 0:
            end = card
        if start > card:
            start = card
        left = card - end
        left = max(left, 0)
        right = card - start + 1
        right = min(card, right)
        nodes = self.nodelist[left:right][::-1]
        if not nodes:
            return []
        if withscores:
            return [(n.key, n.score) for n in nodes]
        else:
            return [n.key for n in nodes]

    def zrangebyscore(self, start, end, withscores=False):
        leftnode = self.node_class("", start, 0)
        rightnode = self.node_class("", end, 0)
        left = bisect.bisect_left(self.nodelist, leftnode)
        right = bisect.bisect_right(self.nodelist, rightnode)
        nodes = self.nodelist[left:right]
        if not nodes:
            return []
        if withscores:
            return [(x.key, x.score) for x in nodes]
        else:
            return [x.key for x in nodes]

    def zrevrangebyscore(self, start, end, withscores=False):
        return self.zrangebyscore(start, end, withscores)[::-1]

    def zincrby(self, key, score):
        node = self.nodedict.get(key)
        if not node:
            self.zadd(key, score)
            return score
        score = node.score + score
        self.zadd(key, score)
        return score

    def clear(self):
        self.nodedict = {}
        self.nodelist = []