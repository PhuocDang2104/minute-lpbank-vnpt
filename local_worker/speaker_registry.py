import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class SpeakerRegistry:
    def __init__(self, threshold=0.75):
        self.speakers = []
        self.threshold = threshold

    def match_or_create(self, embedding: np.ndarray):
        if not self.speakers:
            self.speakers.append(embedding)
            return "USER_1", 1.0

        sims = cosine_similarity([embedding], self.speakers)[0]
        idx = sims.argmax()

        if sims[idx] >= self.threshold:
            return f"USER_{idx+1}", float(sims[idx])

        self.speakers.append(embedding)
        return f"USER_{len(self.speakers)}", 0.5
