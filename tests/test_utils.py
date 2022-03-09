import pytest
from unittest.mock import Mock, patch

from datetime import datetime, timedelta

from dockerensure.utils import IntervalOffset


@pytest.mark.parametrize(
    "interval,offset,intervals",
    [
        (timedelta(days=1), datetime(year=2020, month=1, day=10, hour=0), 0),
        (timedelta(days=1), datetime(year=2020, month=1, day=9, hour=0), 1),
        (timedelta(hours=5), datetime(year=2020, month=1, day=9, hour=12), 4),
    ],
)
@patch("datetime.datetime")
def test_intervals(mock_datetime, interval, offset, intervals):
    now = datetime(year=2020, month=1, day=10, hour=12)
    mock_datetime.utcnow.return_value = now

    assert IntervalOffset(interval, offset).get_intervals() == intervals
