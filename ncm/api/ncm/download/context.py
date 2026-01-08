class DownloadContext:
    def __init__(self, orchestrator, process, scheduler):
        self.orchestrator = orchestrator
        self.process = process
        self.scheduler = scheduler