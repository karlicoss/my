"""
Feel free to remove this if you don't need it/add your own custom settings and use them
"""

from my.core import Paths, PathIsh

class hypothesis:
    # expects outputs from https://github.com/karlicoss/hypexport
    # (it's just the standard Hypothes.is export format)
    export_path: Paths = '/path/to/hypothesis/data'

class instapaper:
    export_path: Paths = ''

class pocket:
    export_path: Paths = ''

class github:
    export_path: Paths = ''

class reddit:
    export_path: Paths = ''

class endomondo:
    export_path: Paths = ''

class exercise:
    workout_log: PathIsh = '/some/path.org'

class bluemaestro:
    export_path: Paths = ''

class google:
    takeout_path: Paths = ''


from typing import Sequence, Union, Tuple
from datetime import datetime, date
DateIsh = Union[datetime, date, str]
LatLon = Tuple[float, float]
class location:
    # todo ugh, need to think about it... mypy wants the type here to be general, otherwise it can't deduce
    # and we can't import the types from the module itself, otherwise would be circular. common module?
    home: Union[LatLon, Sequence[Tuple[DateIsh, LatLon]]] = (1.0, -1.0)


# todo hmm it's getting out of hand.. perhaps better to keep stubs in the actual my.config presetn in the repository instead
class time:
    class tz:
        pass
