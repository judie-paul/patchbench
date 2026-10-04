from cachekit_lru import LRUCache


def test_put_and_get():
    cache = LRUCache(2)
    cache.put("a", 1)
    assert cache.get("a") == 1


def test_evicts_oldest():
    cache = LRUCache(2)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.put("c", 3)
    assert cache.get("a") is None


def test_len_counts_entries():
    cache = LRUCache(5)
    cache.put("a", 1)
    cache.put("b", 2)
    assert len(cache) == 2
