import datetime
from dataclasses import dataclass


@dataclass
class IntervalOffset:
    interval: datetime.timedelta
    offset: datetime.datetime = datetime.datetime(
        2000, 1, 1, tzinfo=datetime.timezone.utc
    )

    def get_intervals(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        print(now)
        print(self.offset)
        delta = now - self.offset
        print(delta)
        return delta // self.interval
