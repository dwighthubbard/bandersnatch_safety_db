
[![Pipeline Status](https://cd.screwdriver.cd/pipelines/2820/badge)](https://cd.screwdriver.cd/pipelines/2820/events)  [![codecov](https://codecov.io/gh/dwighthubbard/bandersnatch_safety_db/branch/master/graph/badge.svg)](https://codecov.io/gh/dwighthubbard/bandersnatch_safety_db)

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
