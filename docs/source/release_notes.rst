Release Notes
=============

.. role:: small

Version 1.0
-----------

1.0.5 :small:`2021-16-08`
~~~~~~~~~~~~~~~~~~~~~~~~~
- Setting :attr:`omnipath.options.cache` to ``None`` will now disable it (use ``'memory'`` instead)
- Fix writing empty values into cache
- Fix memory cache not copying data before storing it
- Fix various :mod:`pandas` warnings
- Remove redundant step from CI

1.0.4 :small:`2020-27-12`
~~~~~~~~~~~~~~~~~~~~~~~~~
- Fix recursion error
- Remove duplicated ``PostTranslational`` class
- Add interactions tests

1.0.3 :small:`2020-08-12`
~~~~~~~~~~~~~~~~~~~~~~~~~
- Add :class:`omnipath.interactions.PostTranslational`
- Add possibility to download all :class:`omnipath.requests.Annotations`

1.0.2 :small:`2020-29-11`
~~~~~~~~~~~~~~~~~~~~~~~~~
- Fix small bug when converting boolean values
- Fix typos
- Add option to create interaction graphs

1.0.1 :small:`2020-29-11`
~~~~~~~~~~~~~~~~~~~~~~~~~
- Fix bug of not correctly passing datasets in interactions
- Fix the way the progress bar is getting content size
- Add comparison tests with OmnipathR

1.0.0 :small:`2020-23-11`
~~~~~~~~~~~~~~~~~~~~~~~~~
- Fix minor bugs
- Add options improvements
- Add tests
