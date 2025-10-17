"""Message posted when a download starts"""

from textual.message import Message


class DownloadStarted(Message):
    """Message when model download has started successfully"""
    
    def __init__(self, model_id: str):
        super().__init__()
        self.model_id = model_id
