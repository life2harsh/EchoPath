# EchoPath: Constraint-Aware Music Playlist Sequencing with Audio Classification and Informed Graph Search

## Abstract

Automated playlist generation requires more than identifying individually relevant tracks: a generated sequence must also satisfy user constraints, progress toward a musical target, and maintain coherent transitions. EchoPath models playlist construction as a constrained graph-search problem in which tracks are dynamically connected using audio-feature similarity, learned genre signals, mood-cluster membership, and transition policies. The system compares classical audio classifiers and spectrogram convolutional neural networks, then evaluates breadth-first search, depth-first search, uniform-cost search, iterative deepening, A*, IDA*, and three non-search baselines. A deterministic artist-isolated evaluation protocol, component ablations, repeated search cases, and an exploratory listening study are used to separate classification performance, computational behavior, and perceived playlist quality. Final numerical findings will be inserted from the versioned EchoPath experiment bundle after the full run is completed.

**Keywords:** music information retrieval, playlist generation, graph search, audio classification, recommender systems, convolutional neural networks

## 1. Introduction

Music recommendation commonly focuses on predicting which tracks a listener may prefer. Playlist generation adds a sequential decision problem: adjacent tracks should transition coherently, the sequence may need to move toward a target genre or mood, and practical restrictions such as duration, explicit-content filtering, and artist repetition must hold simultaneously. These requirements create a constrained search space rather than an independent ranking problem.

EchoPath investigates whether audio-derived representations and informed graph search can be combined into an auditable playlist-sequencing framework. Each partial playlist is a search state. Feasible successor tracks are generated dynamically, transition costs encode acoustic and semantic changes, and a target condition constrains the final track. Learned genre predictions can influence ranking and heuristic guidance, while a local hill-climbing stage attempts to reduce the final sequence cost.

The study addresses five research questions:

- **RQ1:** Which classical or convolutional model provides the strongest held-out genre-classification performance?
- **RQ2:** How do graph-search algorithms differ in target success, transition cost, runtime, and search effort?
- **RQ3:** Do learned genre signals improve ground-truth target success and sequence cost?
- **RQ4:** Which heuristic, candidate-ranking, and refinement components contribute to A* performance?
- **RQ5:** Do listeners prefer EchoPath sequences to random-valid and greedy baselines?

The contributions are:

1. A reproducible audio-processing and artist-isolated genre-classification pipeline.
2. A constraint-aware formulation of playlist sequencing as dynamic graph search.
3. A benchmark covering six search methods and three operational baselines.
4. Component ablations that distinguish learned signals, target ranking, heuristics, candidate limits, and local refinement.
5. An artifact workflow that records splits, predictions, configurations, raw trials, aggregate statistics, figures, checksums, and environment information.

## 2. Related Work

The Free Music Archive provides open audio, metadata, predefined subsets, and established genre-recognition tasks [@defferrard2017fma]. Automated playlist generation has been studied as a distinct recommendation problem involving sequence coherence, diversity, context, and user intent [@bonnin2014automated]. Content-based music recommendation uses acoustic descriptors when interaction histories are unavailable or sparse [@celma2010music]. EchoPath builds on these areas but focuses on the interaction between learned audio signals, hard sequence constraints, and explicit graph-search behavior.

Classical genre recognition commonly uses engineered spectral and rhythmic features with linear models, support vector machines, tree ensembles, or neural networks. Spectrogram CNNs instead learn local time-frequency patterns from two-dimensional representations. EchoPath evaluates both approaches under one split protocol rather than treating model outputs as independently reported experiments.

Graph-search algorithms offer different guarantees and resource requirements. BFS and DFS order states without transition-cost optimality, UCS prioritizes accumulated path cost, and A* adds an estimate of remaining cost [@hart1968formal]. IDS and IDA* reduce memory requirements through repeated depth or cost bounds [@korf1985depth]. EchoPath evaluates these methods on the same dynamically generated candidate graph and explicitly reports fallback use and raw-search success.

## 3. System Formulation

Let the music library be a set of tracks `V`. A playlist state is an ordered path

```text
P = [v_1, v_2, ..., v_k],  v_i in V.
```

The initial state contains a selected seed track. A successor appends a track not already in the path that satisfies the configured artist-repeat, explicit-content, and duration constraints. The goal requires the requested playlist length and a final track whose ground-truth label or cluster satisfies the target during evaluation.

For adjacent tracks `x` and `y`, normalized differences are

```text
d_tempo   = abs(tempo(x) - tempo(y)) / 120
d_energy  = abs(energy(x) - energy(y))
d_valence = abs(valence(x) - valence(y)).
```

The base transition cost is

```text
c_base(x, y) = 0.45 d_tempo
             + 0.30 d_energy
             + 0.20 d_valence
             + p_genre
             + p_cluster
             + p_policy.
```

Optional preference, mood-fit, and learned-genre terms form a non-negative signal adjustment. The path cost is the sum of consecutive composite transition costs. Candidate tracks are ranked by transition cost and target alignment before applying a configurable neighbor limit.

For A* and IDA*, the heuristic combines target distance, learned-signal penalty, and remaining path length. Cluster targets use distance to the target cluster centroid in normalized tempo-energy-valence space; integer cluster identifiers are not treated as ordinal distances.

## 4. Audio and Learning Pipeline

### 4.1 Dataset

Experiments use FMA Small, containing 8,000 30-second tracks across eight top-level genres. Dataset archives are verified against the distributed track checksum manifest. Track metadata supplies genre and artist identities. The artifact bundle records the precise usable-track count, failed files, class distribution, and split assignments.

### 4.2 Feature extraction

Audio is loaded as mono at 22,050 Hz. Engineered features include tempo, RMS statistics, spectral centroid, zero-crossing rate, spectral rolloff, MFCC means and standard deviations, chroma means, and spectral contrast. The reported valence quantity is an acoustic brightness/chroma proxy and is not interpreted as emotional ground truth.

### 4.3 Evaluation split

Tracks are assigned to 70% training, 15% validation, and 15% test partitions. Artist groups are isolated so an artist cannot occur in multiple partitions. Split assignments and their dataset fingerprint are persisted and reused by classical and CNN experiments. Model and checkpoint selection use validation macro F1. The test partition is evaluated only after selection.

### 4.4 Classical models

The comparison includes logistic regression, linear SVM, RBF SVM, random forest, extra trees, and a multilayer perceptron. Missing values are imputed, zero-variance features are removed, and scaling is applied where required. Optional tuning uses artist-group-aware stratified cross-validation within the training partition.

### 4.5 Convolutional models

The CNN comparison includes LeNet-style, VGG-style, and ResNet-style architectures operating on normalized mel spectrograms. Spectrogram tensors are cached with a preprocessing schema fingerprint. Training supports CUDA mixed precision and resumable deterministic checkpoints. The selected architecture exports per-track predictions and confidence scores for downstream playlist experiments.

## 5. Playlist Search Methods

EchoPath evaluates BFS, DFS, UCS, IDS, A*, and IDA*. Random-valid, greedy target-aware, and acoustic nearest-neighbor methods provide operational baselines. Search cases are sampled deterministically across seed genres, seed clusters, target genres, and target clusters. Each method receives the same constraints and candidate-generation rules.

Primary results distinguish:

- Raw-search success before fallback
- Greedy fallback use
- Ground-truth target success
- Prediction-assisted target status
- Total transition cost
- Runtime and raw-search runtime
- States expanded and baseline candidate evaluations
- Constraint satisfaction and diversity metrics

Repetitions are averaged within each case before confidence intervals are computed across cases.

## 6. Experimental Design

The primary ML metric is macro F1 because it weights each genre equally. Accuracy, balanced accuracy, weighted F1, per-class precision and recall, confusion matrices, and prediction files are also reported.

The primary search benchmark compares all nine methods under cold-cache conditions using only the held-out test partition as the search graph. Consequently, learned signals used by the search are out-of-sample predictions from tracks that were not used for CNN fitting or architecture selection. A separate A* experiment removes learned signals, target-aware neighbor ranking, hill climbing, individual heuristic components, and alternative neighbor limits. Raw trials and aggregate tables are generated from the same command surface.

The exploratory listening study uses paired, randomized playlist comparisons. Participants rate transition smoothness, coherence, target progression, and overall preference. The protocol, consent text, and questionnaire are distributed with the repository. Institutional requirements must be confirmed before recruitment.

## 7. Results

### 7.1 Classical classification

Insert `research/windows/results/report/tables/classical_validation.csv` and the held-out values from `classical/final_test_metrics.json`.

### 7.2 CNN classification

Insert `research/windows/results/report/tables/cnn_validation.csv` and the held-out values from `cnn/final_test_metrics.json`.

### 7.3 Search comparison

Insert `research/windows/results/report/tables/search_primary.csv`. Report ground-truth target success separately from prediction-assisted status and identify every method's fallback rate.

### 7.4 Ablations

Insert `research/windows/results/report/tables/search_ablations.csv`. Discuss effect sizes and confidence intervals rather than ranking methods from point estimates alone.

### 7.5 Listening study

Insert participant count, exclusion criteria, paired ratings, uncertainty intervals, effect sizes, and the approved statistical analysis after data collection.

## 8. Discussion

The final discussion will connect classification reliability to downstream target guidance, distinguish computational efficiency from playlist quality, and identify whether gains remain after learned-signal and refinement ablations. Claims about perceived quality will be limited to the scope and size of the listening study.

## 9. Limitations

FMA genre labels are broad and do not capture every musical property relevant to sequencing. The valence value is a transparent acoustic proxy rather than an affect annotation. The fixed transition objective reflects design choices and cannot substitute for listener judgments. A small convenience sample limits generalization of the exploratory study. Dynamic candidate pruning may prevent globally optimal paths, and the A* heuristic is evaluated empirically rather than claimed to be admissible. Preference scores are heuristic unless real user interactions are collected.

## 10. Reproducibility and Ethics

The repository distributes code, split generation, experiment settings, raw and aggregate schemas, and artifact checksums. FMA audio remains subject to its per-track licenses and is downloaded from the official distribution rather than redistributed. Listening-study participation must be voluntary, consented, minimally identifying, and handled according to institutional policy.

## 11. Conclusion

EchoPath provides an auditable framework for studying how audio classification, hard constraints, and informed graph search interact in playlist sequencing. The final conclusion will be updated after the full experiment and listening-study results are available.

## References

References are stored in `paper/references.bib`.
