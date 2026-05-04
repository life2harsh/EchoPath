import json
import numpy as np
from sklearn.cluster import KMeans

INPUT_FILE = "data/library/tracks_updated.json"
OUTPUT_FILE = "data/library/tracks_clustered.json"

# Load data
with open(INPUT_FILE, "r") as f:
    data = json.load(f)

X = []
valid_indices = []

# Extract usable features
for i, track in enumerate(data):
    tempo = track.get("tempo", 0)
    energy = track.get("energy", 0)
    valence = track.get("valence", 0)

    if tempo > 0:
        X.append([tempo, energy, valence])
        valid_indices.append(i)

X = np.array(X)

print(f"Using {len(X)} tracks for clustering")

# KMeans
kmeans = KMeans(n_clusters=4, random_state=42)
labels = kmeans.fit_predict(X)

# Assign cluster IDs
for idx, label in zip(valid_indices, labels):
    data[idx]["cluster_id"] = int(label)

# Save output
with open(OUTPUT_FILE, "w") as f:
    json.dump(data, f, indent=2)

print("✅ Clustering complete!")
print(f"Saved to: {OUTPUT_FILE}")