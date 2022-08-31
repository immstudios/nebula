__all__ = ["cache", "Cache"]

import time
from nxtools import log_traceback, critical_error, logging

from nx.core.common import config

try:
    import pylibmc  # noqa
except ModuleNotFoundError:
    pylibmc = None

try:
    import redis  # noqa
except ModuleNotFoundError:
    redis = None


MAX_RETRIES = 5


class RedisEngine:
    def __init__(self):
        if redis is None:
            critical_error("redis module is not installed")

    def configure(self):
        self.site = config["site_name"]
        self.host = config.get("redis_host", "localhost")
        self.port = config.get("redis_port", 6379)
        self.connect()

    def connect(self):
        self.conn = redis.Redis(
            self.host,
            self.port,
            charset="utf-8",
            decode_responses=True,
        )

    def load(self, key: str):
        return self.conn.get(key)

    def save(self, key: str, value):
        self.conn.set(key, value)

    def delete(self, key: str):
        self.conn.delete(key)


class MemcachedEngine:
    def __init__(self):
        if pylibmc is None:
            critical_error("pylibmc module is not installed")

    def configure(self):
        self.site = config["site_name"]
        self.host = config.get("cache_host", "localhost")
        self.port = config.get("cache_port", 11211)
        self.connect()

    def connect(self):
        self.cstring = f"{self.host}:{self.port}"
        self.pool = False
        self.conn = pylibmc.Client([self.cstring])

    def load(self, key):
        if config.get("mc_thread_safe", False):
            return self.threaded_load(key)

        try:
            result = self.conn.get(key)
        except pylibmc.ConnectionError:
            self.connect()
            result = False
        except ValueError:
            result = False
        return result

    def save(self, key, value):
        if config.get("mc_thread_safe", False):
            return self.threaded_save(key, value)

        for i in range(MAX_RETRIES):
            try:
                self.conn.set(str(key), str(value))
                break
            except Exception:
                log_traceback(f"Cache save failed ({key})")
                time.sleep(0.1)
                self.connect()
        else:
            critical_error("Memcache save failed. This should never happen.")
        return True

    def delete(self, key):
        if config.get("mc_thread_safe", False):
            return self.threaded_delete(key)
        for i in range(MAX_RETRIES):
            try:
                self.conn.delete(key)
                break
            except Exception:
                log_traceback(f"Cache delete failed ({key})")
                time.sleep(0.3)
                self.connect()
        else:
            critical_error("Memcache delete failed. This should never happen.")
        return True

    def threaded_load(self, key):
        if not self.pool:
            self.pool = pylibmc.ThreadMappedPool(self.conn)
        result = False
        with self.pool.reserve() as mc:
            try:
                result = mc.get(key)
            except pylibmc.ConnectionError:
                self.connect()
                result = False
        self.pool.relinquish()
        return result

    def threaded_save(self, key, value):
        if not self.pool:
            self.pool = pylibmc.ThreadMappedPool(self.conn)
        with self.pool.reserve() as mc:
            for i in range(MAX_RETRIES):
                try:
                    mc.set(str(key), str(value))
                    break
                except Exception:
                    log_traceback(f"Cache save failed ({key})")
                    time.sleep(0.3)
                    self.connect()
            else:
                critical_error("Memcache save failed. This should never happen.")
        self.pool.relinquish()
        return True

    def threaded_delete(self, key):
        if not self.pool:
            self.pool = pylibmc.ThreadMappedPool(self.conn)
        with self.pool.reserve() as mc:
            for i in range(MAX_RETRIES):
                try:
                    mc.delete(key)
                    break
                except Exception:
                    log_traceback(f"Cache delete failed ({key})")
                    time.sleep(0.3)
                    self.connect()
            else:
                critical_error("Memcache delete failed. This should never happen.")
        self.pool.relinquish()
        return True


class Cache:
    def __init__(self):
        self.site = config["site_name"]

    def configure(self):
        if config.get("redis_host"):
            logging.debug("Initializing redis cache")
            self.engine = RedisEngine()
        elif config.get("cache_host"):
            logging.debug("Initializing memcached")
            self.engine = MemcachedEngine()
        else:
            critical_error("Cache is not configured properly")
        self.engine.configure()

    def load(self, key: str):
        key = f"{self.site}-{key}"
        return self.engine.load(key)

    def save(self, key, value):
        key = f"{self.site}-{key}"
        return self.engine.save(key, value)

    def delete(self, key):
        key = f"{self.site}-{key}"
        return self.engine.delete(key)


cache = Cache()
