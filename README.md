[![Build Status](https://travis-ci.org/geerk/toradbapi.svg?branch=master)](https://travis-ci.org/geerk/toradbapi)

Want to use twisted's adbapi in tornado but does not know how? Try toradbapi.

This is just wrapper for `twisted.enterprise.adbapi.ConnectionPool` to use with tornado. So documentation for `__init__` args you can find at [twisted docs](https://twistedmatrix.com/documents/14.0.2/api/twisted.enterprise.adbapi.ConnectionPool.html#__init__).

To install it run:

```
pip install toradbapi
```

Available methods in `toradbapi.ConnectionPool`:
- run_query
- run_operation
- run_interaction

They all have similar interface as twisted's corresponding methods. They return instance of `Future`, so can be yielded inside coroutine.

Example usage:

```python
from tornado import gen
from toradminapi import ConnectionPool

pool = ConnectionPool('MySQLdb', db='test')

@gen.coroutine
def get_entities():
  entities = yield pool.run_query('SELECT * FROM `entity`')
  raise gen.Return(entities)
```

Demo project is under demo.py file. Also there are plenty examples in tests.py.

Only Python 2.7 supported for now.
