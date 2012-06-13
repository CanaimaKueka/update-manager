.. python-apt Backend module

Update Manager API: python-apt Backend module
=============================================

.. automodule:: UpdateManager.Backend.PythonApt

Interface implementations
-------------------------

These classes implement the backend interface.

.. autoclass:: PythonAptBackend
   :members:
   :undoc-members:

.. autoclass:: PackageInfoStore
   :members:
   :undoc-members:

.. autoclass:: PackageDependency
   :members:
   :undoc-members:

.. autoclass:: PackageInfo
   :members:
   :undoc-members:

Helper classes
--------------

These classes are pure helper classes and are unlikely to be useful
outside this module.

.. autoclass:: CacheProgressHelper
   :members:
   :undoc-members:

.. autoclass:: ListProgressHelper
   :members:
   :undoc-members:

.. autoclass::  DownloadProgressHelper
   :members:
   :undoc-members:

.. autoclass:: InstallProgressHelper
   :members:
   :undoc-members:

Helper functions
----------------

.. autofunction:: _translate_relation

Constants
---------

.. autodata:: FETCH_STATUS