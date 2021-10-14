import time
import logging
import pytest
import requests

from copy import deepcopy
from collections import namedtuple
from email.utils import formatdate
from requests_cache import CachedSession


CachedResponse = namedtuple('CachedResponse', ['timestamp', 'status', 'method', 'resp'])


class DictCachedClient:
    def __init__(self, expiration_interval=30):
        self._expiration_interval = expiration_interval

        self.cache = dict()
        self.logger = logging.getLogger(self.__class__.__name__)

    @property
    def expiration_interval(self):
        return self._expiration_interval

    @expiration_interval.setter
    def expiration_interval(self, value):
        self._expiration_interval = value
        self.cache.clear()

    def get(self, url, **kwargs):
        timestamp = time.time()
        entry = self.cache.get(url, False)

        if entry and (entry.timestamp + self.expiration_interval) <= timestamp:
            resp = requests.get(url, **kwargs)
            cache_resp = deepcopy(resp)
            self.cache[url] = CachedResponse(timestamp, cache_resp.status_code, cache_resp.request.method, cache_resp)
            resp.from_cache = False
            return resp
        elif entry:
            entry.resp.headers['Date'] = formatdate(timeval=None, localtime=False, usegmt=True)
            entry.resp.from_cache = True
            return entry.resp

        resp = requests.get(url, **kwargs)
        cache_resp = deepcopy(resp)
        self.cache[url] = CachedResponse(timestamp, cache_resp.status_code, cache_resp.request.method, cache_resp)
        resp.from_cache = False
        return resp


class ModuleCachedClient(CachedSession):
    @property
    def expiration_interval(self):
        return self.expire_after

    @expiration_interval.setter
    def expiration_interval(self, value):
        self.expire_after = value
        self.cache.clear()


module_cached_client = lambda expire_timeout: ModuleCachedClient('CurrencyClientCache',
                                                                 backend="filesystem",
                                                                 expire_after=expire_timeout)


class CurrencyClient:

    def __init__(self, webclient, interval=10): # (webclient, days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0)
        """
        Client to get currency value from the server

        webclient - HTTP client that can interact with web-server
                    and have a built-in caching solution
        interval (int) - cache entry expiration interval in seconds
        """
        self.webclient = webclient(interval)
        self.logger = logging.getLogger(self.__class__.__name__)

    def _get(self, resource):
        return self.webclient.get(f'http://localhost:8888/{resource}')

    def get_currency(self, currency: str):
        resp = self._get(str(currency).lower())
        if resp.from_cache:
            self.logger.info(f'Get cached data for {currency}')
        else:
            self.logger.info(f'{resp.request.method} {resp.request.url} - {resp.status_code}')
        return resp

    def set_interval(self, expire_timeout):  # (self, hours=0, minutes=0, seconds=30)
        self.logger.info(f'New expiration interval set to {expire_timeout}')
        self.webclient.expiration_interval = expire_timeout


@pytest.fixture
def dict_cache():
    return DictCachedClient

@pytest.fixture
def module_cache():
    return module_cached_client

@pytest.fixture(scope='function', params=["dict_cache", "module_cache"])
def currency_client(request):
    yield CurrencyClient(webclient=request.getfixturevalue(request.param))


def test_get_usd(currency_client):
    initial_resp = currency_client.get_currency('USD')
    time.sleep(currency_client.webclient.expiration_interval//2)
    cached_resp = currency_client.get_currency('USD')

    assert not initial_resp.from_cache
    assert cached_resp.from_cache
    assert initial_resp.content == cached_resp.content

    time.sleep(currency_client.webclient.expiration_interval + 1)
    expired_cache_resp = currency_client.get_currency('USD')

    assert not expired_cache_resp.from_cache
    assert initial_resp.content != expired_cache_resp.content


def test_get_eur(currency_client):
    initial_resp = currency_client.get_currency('EUR')
    time.sleep(currency_client.webclient.expiration_interval // 2)
    cached_resp = currency_client.get_currency('EUR')

    assert not initial_resp.from_cache
    assert cached_resp.from_cache
    assert initial_resp.content == cached_resp.content

    time.sleep(currency_client.webclient.expiration_interval + 1)
    expired_cache_resp = currency_client.get_currency('EUR')

    assert not expired_cache_resp.from_cache
    assert initial_resp.content != expired_cache_resp.content


def test_change_interval(currency_client):
    initial_resp = currency_client.get_currency('EUR')
    time.sleep(currency_client.webclient.expiration_interval+1)
    expired_cache_resp = currency_client.get_currency('EUR')

    assert not initial_resp.from_cache
    assert not expired_cache_resp.from_cache
    assert initial_resp.content != expired_cache_resp.content

    currency_client.set_interval(currency_client.webclient.expiration_interval // 2)

    initial_resp = currency_client.get_currency('EUR')
    time.sleep(currency_client.webclient.expiration_interval + 1)
    expired_cache_resp = currency_client.get_currency('EUR')

    assert not initial_resp.from_cache
    assert not expired_cache_resp.from_cache
    assert initial_resp.content != expired_cache_resp.content
