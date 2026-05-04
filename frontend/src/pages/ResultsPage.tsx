import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";

import { SectionCard } from "../components/SectionCard";
import { buildApiUrl, fetchPlaylist } from "../lib/api";
import { formatDuration, titleCase } from "../lib/format";

export function ResultsPage() {
  const { playlistId } = useParams();
  const playlistQuery = useQuery({
    queryKey: ["playlist", playlistId],
    queryFn: () => fetchPlaylist(playlistId!),
    enabled: Boolean(playlistId),
  });

  if (!playlistId) {
    return (
      <SectionCard
        eyebrow="No Playlist Yet"
        title="Generate a path from the builder"
        subtitle="This route is ready to display the next playlist as soon as the generator returns."
      >
        <Link className="primary-button primary-button--inline" to="/builder">
          Open the builder
        </Link>
      </SectionCard>
    );
  }

  if (playlistQuery.isLoading) {
    return <SectionCard title="Loading playlist" subtitle="Pulling the generated path from the backend." />;
  }

  if (playlistQuery.isError || !playlistQuery.data) {
    return (
      <SectionCard title="Playlist unavailable" subtitle="The current playlist could not be loaded from the API." />
    );
  }

  const playlist = playlistQuery.data;

  return (
    <div className="page-grid">
      <SectionCard
        eyebrow="Generated Playlist"
        title={`${titleCase(playlist.algorithm)} route to ${playlist.target_type} ${playlist.target_value}`}
        subtitle={playlist.explanation}
        actions={
          <a
            className="primary-button primary-button--inline"
            href={buildApiUrl(`/playlists/${playlist.playlist_id}/export?format=json`)}
          >
            Export JSON
          </a>
        }
      >
        <div className="metric-row">
          <div className="metric-card">
            <span>Runtime</span>
            <strong>{playlist.runtime_ms.toFixed(2)} ms</strong>
          </div>
          <div className="metric-card">
            <span>Nodes expanded</span>
            <strong>{playlist.nodes_expanded}</strong>
          </div>
          <div className="metric-card">
            <span>Total cost</span>
            <strong>{playlist.total_cost.toFixed(3)}</strong>
          </div>
          <div className="metric-card">
            <span>Target hit</span>
            <strong>{playlist.target_hit ? "Yes" : "Approximate"}</strong>
          </div>
        </div>
      </SectionCard>

      <SectionCard
        eyebrow="Transition Walkthrough"
        title="Why each jump was selected"
        subtitle={playlist.constraint_summary}
      >
        <div className="playlist-steps">
          {playlist.steps.map((step) => (
            <article key={step.track.track_id} className="playlist-step">
              <div className="playlist-step__order">{step.order}</div>
              <div className="playlist-step__body">
                <div className="playlist-step__head">
                  <h3>{step.track.title}</h3>
                  <span>{step.track.artist}</span>
                </div>
                <p>{step.explanation}</p>
                <div className="pill-row">
                  <span className="pill">{step.track.genre_label ?? "Unlabeled"}</span>
                  <span className="pill">Cluster {step.track.cluster_id ?? "?"}</span>
                  <span className="pill">{formatDuration(step.track.duration_sec)}</span>
                  <span className="pill">Edge {step.edge_cost.toFixed(3)}</span>
                </div>
              </div>
            </article>
          ))}
        </div>
      </SectionCard>
    </div>
  );
}
