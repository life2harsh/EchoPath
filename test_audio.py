import librosa

path = "C:\\Dataset\\fma_small\\000\\000002.mp3"

y, sr = librosa.load(path, duration=10)
print("Loaded successfully", len(y))