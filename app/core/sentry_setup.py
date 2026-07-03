from contextlib import contextmanager
from typing import Iterator

import sentry_sdk


def configure_sentry(dsn: str, environment: str) -> None:
    if dsn:
        sentry_sdk.init(dsn=dsn, environment=environment, traces_sample_rate=1.0)


@contextmanager
def traced(operation: str, description: str) -> Iterator[None]:
    with sentry_sdk.start_span(op=operation, name=description):
        yield

