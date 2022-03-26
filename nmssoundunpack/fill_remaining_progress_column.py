from rich.console import RenderableType, ConsoleOptions, Console
from rich.measure import Measurement
from rich.progress import ProgressColumn, Task

class FillRemainingProgressColumn(ProgressColumn):
    def render(self, task: "Task") -> RenderableType:
        return FillRemainingRenderable()

# noinspection PyMethodMayBeStatic,PyUnusedLocal
class FillRemainingRenderable:
    def __rich_console__(self, console: Console, options: ConsoleOptions):
        return ""

    def __rich_measure__(
            self, console: Console, options: ConsoleOptions
    ) -> Measurement:
        return Measurement(0, options.max_width)
