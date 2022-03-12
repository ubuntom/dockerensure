from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

import pytest

from dockerensure.utils import IntervalOffset


@pytest.mark.parametrize(
    "interval,offset,intervals",
    [
        (timedelta(days=1), datetime(year=2020, month=1, day=10, hour=0, tzinfo=timezone.utc), 0),
        (timedelta(days=1), datetime(year=2020, month=1, day=9, hour=0, tzinfo=timezone.utc), 1),
        (timedelta(hours=5), datetime(year=2020, month=1, day=9, hour=12, tzinfo=timezone.utc), 4),
    ],
)
@patch("datetime.datetime")
def test_intervals(mock_datetime, interval, offset, intervals):
    now = datetime(year=2020, month=1, day=10, hour=12, tzinfo=timezone.utc)
    mock_datetime.now.return_value = now

    assert IntervalOffset(interval, offset).get_intervals() == intervals
