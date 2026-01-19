from ncm.service.download.orchestrator import DownloadOrchestrator, DownloadProcess
from ncm.service.download.orchestrator.scheduler import ProcessScheduler


class DownloadContext:
    def __init__(self, orchestrator: DownloadOrchestrator, process: DownloadProcess, scheduler: ProcessScheduler):
        self.orchestrator = orchestrator
        self.process = process
        self.scheduler = scheduler