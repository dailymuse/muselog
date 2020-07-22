from muselog import context


class ClearContext:
    """Clear context after test finishes."""

    def tearDown(self) -> None:
        context.clear()
        super().tearDown()
