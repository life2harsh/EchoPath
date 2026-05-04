import json
import librosa
import numpy as np
from tqdm import tqdm

INPUT_FILE = "data/library/tracks.json"
OUTPUT_FILE = "data/library/tracks_updated.json"

def extract_features(audio_path):
    try:
        # Load audio safely (force mono)
        y, sr = librosa.load(audio_path, duration=30, mono=True)

        if y is None or len(y) == 0:
            print(f"Empty audio: {audio_path}")
            return 0.0, 0.0, 0.0

        # Ensure it's 1D
        y = np.asarray(y).flatten()

        # Tempo
        tempo = librosa.beat.tempo(y=y, sr=sr)
        tempo = float(tempo[0]) if isinstance(tempo, np.ndarray) else float(tempo)

        # Energy (RMS)
        rms = librosa.feature.rms(y=y)
        energy = float(np.mean(rms)) if rms is not None else 0.0

        # Valence approximation
        spec_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
        valence = float(np.mean(spec_centroid) / 5000) if spec_centroid is not None else 0.0

        print(f"✔ {audio_path} | tempo={tempo:.2f}, energy={energy:.4f}")

        return tempo, energy, valence

    except Exception as e:
        print(f"❌ Error processing {audio_path}: {e}")
        return 0.0, 0.0, 0.0

def main():
    with open(INPUT_FILE, "r") as f:
        data = json.load(f)

    updated_data = []

    for track in tqdm(data):
        audio_path = track.get("path")

        tempo, energy, valence = extract_features(audio_path)

        updated_track = {
            "track_id": track["track_id"],
            "title": track["title"],
            "artist": track.get("artist", "Unknown"),

            # FIXED FIELD NAMES
            "genre_label": track.get("genre", "unknown"),
            "duration_sec": track.get("duration_sec", 180),
            "audio_path": audio_path,

            # NEW FEATURES
            "tempo": tempo,
            "energy": energy,
            "valence": valence,

            # TEMP DEFAULT (we'll fix in Step 2)
            "cluster_id": 0,

            "explicit": False
        }

        updated_data.append(updated_track)
        # Save progress every 50 tracks
        if len(updated_data) % 50 == 0:
         with open(OUTPUT_FILE, "w") as f:
          json.dump(updated_data, f, indent=2)

    with open(OUTPUT_FILE, "w") as f:
        json.dump(updated_data, f, indent=2)

    print("\n✅ Feature extraction complete!")
    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()