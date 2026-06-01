from dataclasses import dataclass


@dataclass(slots=True)
class AdapterRuntime:
    source: str = "mock"
    detail: str = ""


class RuntimeAwareAdapter:
    runtime: AdapterRuntime

    def set_runtime(self, source: str, detail: str = "") -> None:
        self.runtime = AdapterRuntime(source=source, detail=detail)
