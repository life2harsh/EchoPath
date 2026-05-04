import { formatDuration } from "../lib/format";
import type { TrackRecord } from "../lib/types";

interface TrackCardProps {
  track: TrackRecord;
  active: boolean;
  onSelect: (track: TrackRecord) => void;
}

export function TrackCard({ track, active, onSelect }: TrackCardProps) {
  return (
    <button
      type="button"
      className={`track-card ${active ? "track-card--active" : ""}`}
      onClick={() => onSelect(track)}
    >
      <div className="track-card__cluster">Cluster {track.cluster_id ?? "?"}</div>
      <h3>{track.title}</h3>
      <p className="track-card__artist">{track.artist}</p>
      <div className="track-card__meta">
        <span>{track.genre_label ?? "Unlabeled"}</span>
        <span>{formatDuration(track.duration_sec)}</span>
      </div>
      {track.summary ? <p className="track-card__summary">{track.summary}</p> : null}
    </button>
  );
}
