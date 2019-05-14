
[![Pipeline Status](http://45.79.65.140:9000/pipelines/2/badge)](http://45.79.65.140:9000/pipelines/2/events)  [![codecov](https://codecov.io/gh/dwighthubbard/bandersnatch_safety_db/branch/master/graph/badge.svg)](https://codecov.io/gh/dwighthubbard/bandersnatch_safety_db)

-----

# Bandersnatch Safety DB filtering plugin

This package provides a bandersnatch plugin that filters releases based on [safety-db]().

## Installation

``` command
pip install bandersnatch bandersnatch_safety_db
```

## Configuration

To enable add `safety_db_release` to the [blacklist] plugins setting of the bandersnatch.conf.  

```
[blacklist]
plugins =
    safety_db_release
```
