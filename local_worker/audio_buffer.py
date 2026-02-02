import numpy as np
import torch

class AudioBuffer:
    def __init__(self, sample_rate=16000, chunk_sec=10, overlap_sec=3):
        self.sr = sample_rate
        self.chunk_size = chunk_sec * sample_rate
        self.step_size = (chunk_sec - overlap_sec) * sample_rate
        self.buffer = np.zeros(0, dtype=np.float32)
        self.consumed_samples = 0

    def push(self, samples: np.ndarray):
        self.buffer = np.concatenate([self.buffer, samples])

    def pop_chunk(self):
        if len(self.buffer) < self.chunk_size:
            return None

        chunk = self.buffer[: self.chunk_size]
        self.buffer = self.buffer[self.step_size :]
        start_time = float(self.consumed_samples) / float(self.sr)
        self.consumed_samples += self.step_size
        return torch.tensor(chunk).unsqueeze(0), start_time
