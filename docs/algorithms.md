# EchoPath Algorithms

This document describes the two main computational pipelines used by EchoPath:

1. Constraint-aware playlist generation using graph-search algorithms.
2. Audio feature extraction, clustering, and genre classification using classical machine learning and convolutional neural networks.

---

## Algorithm 1: Constraint-Aware Playlist Generation

**Input:** Seed track `s`, target type `t` (genre or mood cluster), target value `v`, playlist length `L`, search algorithm `A`, and playlist constraints `C`.

**Output:** An ordered playlist `P`, total transition cost, search statistics, target status, and quality metrics.

### Step 1: Initialize the search

1. Load the track library and locate the seed track `s`.
2. Initialize the first search state as:

   ```text
   P = [s]
   g(P) = 0
   ```

3. Select one of the supported search methods:

   ```text
   A in {BFS, DFS, UCS, IDS, A*, IDA*}
   ```

### Step 2: Generate valid neighboring tracks

For the current track `x`, inspect candidate tracks `y` from the library. A candidate is valid only when all the following conditions hold:

```text
y is not already present in P
artist_count(y, P) < artist_repeat_limit
y is not explicit when explicit filtering is enabled
duration(P) + duration(y) <= maximum duration, when a limit exists
```

Rank valid candidates using transition quality and target alignment. Keep the highest-ranked candidates as the neighbors of `x`.

### Step 3: Calculate transition cost

For each transition from track `x` to track `y`, calculate normalized feature differences:

```text
energy_delta  = abs(energy(x) - energy(y))
valence_delta = abs(valence(x) - valence(y))
```

The base transition cost is:

```text
base_cost(x, y) =
    0.45 * tempo_delta
  + 0.30 * energy_delta
  + 0.20 * valence_delta
  + genre_penalty
  + cluster_penalty
  + tempo_policy_penalty
```

The tempo policy contributes an additional penalty:

```text
any      : 0
steady   : 0.60 * tempo_delta
lift     : max(0, tempo(x) - tempo(y)) / 120
cooldown : max(0, tempo(y) - tempo(x)) / 120
```

Machine-learning signals adjust the cost of selecting `y`:

```text
signal_penalty(y) =
    0.12 * (1 - preference_score(y))
  + 0.06 * (1 - mood_fit_score(y))
  + genre_prediction_penalty(y)
```

If the predicted genre matches the target genre, prediction confidence reduces the penalty. Otherwise, confidence increases it.

The final edge cost is:

```text
edge_cost(x, y) = max(0, base_cost(x, y) + signal_penalty(y))
```

The total path cost is the sum of all consecutive edge costs:

```text
g(P) = sum(edge_cost(P[i - 1], P[i])) for i = 1 to length(P) - 1
```

### Step 4: Search for a complete playlist

Run the selected search algorithm over partial playlists. A state is a goal when:

```text
length(P) = L
and
last(P) matches the requested genre or mood cluster
```

The search methods prioritize states as follows:

| Method | State-selection rule |
| --- | --- |
| BFS | Select the oldest generated state. |
| DFS | Select the most recently generated state. |
| UCS | Select the state with minimum path cost `g(P)`. |
| IDS | Repeat depth-limited DFS with increasing depth limits. |
| A* | Select the state with minimum `f(P) = g(P) + h(P)`. |
| IDA* | Repeat depth-first search using increasing `f`-cost bounds. |

For A* and IDA*, estimate the remaining cost using:

```text
h(P) =
    target_penalty(last(P))
  + 0.50 * signal_penalty(last(P))
  + 0.08 * (L - length(P))
```

Stop when a goal is found, no states remain, or the search reaches the expansion limit.

### Step 5: Apply a greedy fallback

If the selected search method cannot find a complete target-matching playlist:

1. Start again from the seed track.
2. Generate valid neighbors of the current track.
3. Select the neighbor with the lowest transition and target-ranking cost.
4. Append it to the playlist.
5. Repeat until the requested length is reached or no valid neighbor remains.

The fallback can return an approximate playlist that is shorter than requested or does not reach the target.

### Step 6: Refine the playlist with hill climbing

For at most two refinement passes:

1. Select a non-seed position in the playlist.
2. Generate valid replacements for the track at that position.
3. Reject replacements that violate playlist constraints or remove the final target match.
4. Calculate the new total path cost.
5. Keep the first replacement that strictly lowers the cost.
6. Stop when a complete pass produces no improvement.

### Step 7: Return the result

Return:

```text
playlist ID
ordered tracks
selected search algorithm
total transition cost
runtime
number of expanded states
target-match status
constraint summary
transition explanations
playlist quality metrics
```

---

## Algorithm 2: Audio Processing and Machine-Learning Pipeline

**Input:** A collection of audio files and optional track metadata containing titles, artists, genres, and durations.

**Output:** An enriched track manifest, mood clusters, trained genre-classification models, predictions, confidence scores, and evaluation reports.

### Step 1: Load audio and metadata

1. Discover supported audio files recursively:

   ```text
   {MP3, WAV, FLAC, OGG, M4A}
   ```

2. Match each audio file with its metadata when metadata is available.
3. Load up to the first 30 seconds of each track.
4. Convert the signal to mono audio sampled at `22,050 Hz`.
5. Skip files that cannot be decoded and record them in a failure log.

### Step 2: Extract audio features

For each valid track, compute:

```text
tempo
RMS energy mean and standard deviation
valence proxy based on spectral brightness and chroma
spectral centroid mean and standard deviation
zero-crossing rate
spectral rolloff
13 MFCC means and standard deviations
12 chroma means
spectral contrast means
```

Normalize the backend-facing energy value to `[0, 1]`. Estimate valence using:

```text
brightness = normalize(spectral_centroid, 500, 5000)

valence = clip(
    0.70 * brightness + 0.30 * mean(chroma),
    0,
    1
)
```

This value is an audio-based proxy and is not emotional-valence ground truth.

### Step 3: Build the track manifest

Combine metadata and extracted features into one record per track:

```text
track ID
title
artist
duration
genre label
audio path
tempo
energy
valence
additional numerical audio features
```

Write the resulting records to a JSON manifest and a feature CSV file.

### Step 4: Assign mood clusters

1. Form a numerical feature vector `X_i` for every track.
2. Replace missing feature values with zero.
3. Standardize every feature:

   ```text
   Z_ij = (X_ij - mean(X_j)) / standard_deviation(X_j)
   ```

4. Apply K-Means clustering with the requested number of clusters.
5. Store the assigned cluster ID in each track record.

### Step 5: Train classical genre classifiers

1. Remove classes that do not contain enough examples.
2. Optionally balance the number of examples per class.
3. Encode genre names as numerical labels.
4. Split the feature matrix into training and test sets using a stratified split when possible.
5. Train and compare:

   ```text
   Logistic Regression
   Linear Support Vector Machine
   RBF Support Vector Machine
   Random Forest
   Extra Trees
   Multilayer Perceptron
   ```

6. Optionally tune model hyperparameters using stratified cross-validation.
7. Predict genre labels for the held-out test set.
8. Evaluate each model using:

   ```text
   accuracy
   balanced accuracy
   macro F1 score
   weighted F1 score
   per-class precision, recall, and F1 score
   ```

9. Select the model with the highest macro F1 score.
10. Save the model, label encoder, feature-column list, class distribution, and evaluation reports.

### Step 6: Train spectrogram CNN classifiers

1. Encode genre names as numerical class labels.
2. Split the tracks into stratified training and test sets.
3. Convert each audio sample into a fixed-size mel-spectrogram representation.
4. Train one or more convolutional architectures:

   ```text
   LeNet-style CNN
   VGG-style CNN
   ResNet-style CNN
   ```

5. Run training on a GPU when CUDA is available; otherwise, use the CPU.
6. Evaluate each architecture using test loss, accuracy, macro F1, and weighted F1.
7. Save each trained model and its classification report.
8. Rank architectures by macro F1 and report the best-performing architecture.

### Step 7: Enrich tracks with ML signals

For every track, add the available integration signals:

```text
preference score
mood-fit score
predicted genre
genre-prediction confidence
prediction source
```

When exported CNN predictions are available, use them directly. Otherwise, the enrichment process may use a cluster-majority genre proxy. These fields are stored in the backend manifest and influence playlist transition costs, target penalties, and search heuristics.

### Step 8: Classify an uploaded track

When a user uploads a new track:

1. Extract tempo, energy, valence, MFCC, chroma, spectral contrast, and related features.
2. Assign the track to its nearest mood-cluster centroid.
3. Find the nearest labeled tracks using normalized tempo, energy, and valence distance.
4. Predict the genre using majority voting among the nearest tracks.
5. Calculate prediction confidence from the neighbor votes.
6. Insert the analyzed track into the in-memory library.
7. Make the track immediately available as a playlist seed and graph-search candidate.

---

## Combined EchoPath Flow

```text
Audio Dataset
    |
    v
Feature Extraction
    |
    +----> K-Means Mood Clusters
    |
    +----> Classical Genre Models
    |
    +----> Spectrogram CNN Models
    |
    v
Enriched Track Manifest
    |
    v
Constraint Filtering and Dynamic Neighbor Generation
    |
    v
BFS / DFS / UCS / IDS / A* / IDA*
    |
    v
Greedy Fallback, if required
    |
    v
Hill-Climbing Refinement
    |
    v
Final Playlist and Quality Metrics
```
