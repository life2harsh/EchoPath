import { buildStreamUrl } from "../lib/api";
import { formatDuration } from "../lib/format";
import type { TrackRecord } from "../lib/types";

interface AudioPreviewProps {
  track: TrackRecord | null;
}

export function AudioPreview({ track }: AudioPreviewProps) {
  if (!track) {
    return (
      <div className="preview-card preview-card--empty">
        <p>Select a track to inspect its metadata and preview surface.</p>
      </div>
    );
  }

  const streamUrl = buildStreamUrl(track);

  return (
    <div className="preview-card">
      <div className="preview-card__hero">
        <div>
          <p className="eyebrow">Selected Track</p>
          <h2>{track.title}</h2>
          <p className="preview-card__artist">{track.artist}</p>
        </div>
        <div className="pill-row">
          <span className="pill">{track.genre_label ?? "Genre pending"}</span>
          <span className="pill">Cluster {track.cluster_id ?? "?"}</span>
          <span className="pill">{formatDuration(track.duration_sec)}</span>
        </div>
      </div>

      <div className="preview-stats">
        <div>
          <strong>{track.tempo?.toFixed(0) ?? "--"}</strong>
          <span>Tempo</span>
        </div>
        <div>
          <strong>{track.energy?.toFixed(2) ?? "--"}</strong>
          <span>Energy</span>
        </div>
        <div>
          <strong>{track.valence?.toFixed(2) ?? "--"}</strong>
          <span>Valence</span>
        </div>
      </div>

      <p className="preview-card__summary">
        {track.summary ??
          "This slot is ready for waveform, spectrogram, and embedding explanations once the real dataset is loaded."}
      </p>

      {streamUrl ? (
        <audio key={track.track_id} controls className="audio-player" src={streamUrl}>
          Your browser does not support audio playback.
        </audio>
      ) : (
        <div className="preview-card__notice">
          Audio files are not wired yet for this sample library. The stream endpoint is ready for the real dataset.
        </div>
      )}
    </div>
  );
}
