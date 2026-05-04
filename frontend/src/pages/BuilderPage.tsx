import { startTransition, useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { SectionCard } from "../components/SectionCard";
import { fetchClusters, fetchTracks, generatePlaylist } from "../lib/api";
import { titleCase } from "../lib/format";
import type { AlgorithmName, PlaylistRequest, TargetType, TempoPolicy } from "../lib/types";

const algorithms: AlgorithmName[] = ["astar", "idastar", "ucs", "bfs", "dfs", "ids"];
const tempoPolicies: TempoPolicy[] = ["any", "steady", "lift", "cooldown"];

export function BuilderPage() {
  const navigate = useNavigate();
  const { data: tracks = [] } = useQuery({ queryKey: ["builder-tracks"], queryFn: () => fetchTracks() });
  const { data: clusters = [] } = useQuery({ queryKey: ["clusters"], queryFn: fetchClusters });

  const genres = useMemo(
    () => Array.from(new Set(tracks.map((track) => track.genre_label).filter(Boolean))) as string[],
    [tracks],
  );

  const [seedTrackId, setSeedTrackId] = useState("");
  const [targetType, setTargetType] = useState<TargetType>("genre");
  const [targetValue, setTargetValue] = useState("");
  const [algorithm, setAlgorithm] = useState<AlgorithmName>("astar");
  const [playlistLength, setPlaylistLength] = useState(5);
  const [tempoPolicy, setTempoPolicy] = useState<TempoPolicy>("lift");
  const [artistRepeatLimit, setArtistRepeatLimit] = useState(1);
  const [explicitFilter, setExplicitFilter] = useState(true);

  const mutation = useMutation({
    mutationFn: generatePlaylist,
    onSuccess: (result) => {
      startTransition(() => {
        navigate(`/results/${result.playlist_id}`);
      });
    },
  });

  const effectiveSeedTrackId = seedTrackId || tracks[0]?.track_id || "";
  const effectiveTargetValue =
    targetValue || (targetType === "genre" ? genres[0] ?? "" : clusters[0]?.cluster_id?.toString() ?? "");

  const submit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const payload: PlaylistRequest = {
      seed_track_id: effectiveSeedTrackId,
      target_type: targetType,
      target_value: effectiveTargetValue,
      algorithm,
      playlist_length: playlistLength,
      constraints: {
        artist_repeat_limit: artistRepeatLimit,
        explicit_filter: explicitFilter,
        tempo_policy: tempoPolicy,
      },
    };

    mutation.mutate(payload);
  };

  return (
    <div className="page-grid page-grid--builder">
      <SectionCard
        eyebrow="Playlist Builder"
        title="Set the graph search problem"
        subtitle="Same UI contract now, smarter heuristics later."
      >
        <form className="builder-form" onSubmit={submit}>
          <label>
            Seed track
            <select value={effectiveSeedTrackId} onChange={(event) => setSeedTrackId(event.target.value)}>
              {tracks.map((track) => (
                <option key={track.track_id} value={track.track_id}>
                  {track.title} / {track.artist}
                </option>
              ))}
            </select>
          </label>

          <label>
            Target type
            <select
              value={targetType}
              onChange={(event) => {
                const nextType = event.target.value as TargetType;
                setTargetType(nextType);
                setTargetValue("");
              }}
            >
              <option value="genre">Genre</option>
              <option value="cluster">Cluster</option>
            </select>
          </label>

          <label>
            Target value
            <select value={effectiveTargetValue} onChange={(event) => setTargetValue(event.target.value)}>
              {targetType === "genre"
                ? genres.map((genre) => (
                    <option key={genre} value={genre}>
                      {genre}
                    </option>
                  ))
                : clusters.map((cluster) => (
                    <option key={cluster.cluster_id} value={cluster.cluster_id}>
                      Cluster {cluster.cluster_id} / {cluster.descriptor}
                    </option>
                  ))}
            </select>
          </label>

          <label>
            Algorithm
            <select value={algorithm} onChange={(event) => setAlgorithm(event.target.value as AlgorithmName)}>
              {algorithms.map((item) => (
                <option key={item} value={item}>
                  {titleCase(item)}
                </option>
              ))}
            </select>
          </label>

          <label>
            Playlist length
            <input
              type="range"
              min={3}
              max={10}
              value={playlistLength}
              onChange={(event) => setPlaylistLength(Number(event.target.value))}
            />
            <span>{playlistLength} tracks</span>
          </label>

          <label>
            Tempo policy
            <select value={tempoPolicy} onChange={(event) => setTempoPolicy(event.target.value as TempoPolicy)}>
              {tempoPolicies.map((policy) => (
                <option key={policy} value={policy}>
                  {titleCase(policy)}
                </option>
              ))}
            </select>
          </label>

          <label>
            Artist repeat limit
            <input
              type="number"
              min={1}
              max={3}
              value={artistRepeatLimit}
              onChange={(event) => setArtistRepeatLimit(Number(event.target.value))}
            />
          </label>

          <label className="checkbox-row">
            <input
              type="checkbox"
              checked={explicitFilter}
              onChange={(event) => setExplicitFilter(event.target.checked)}
            />
            Filter explicit tracks
          </label>

          <button className="primary-button" type="submit" disabled={mutation.isPending || !effectiveSeedTrackId}>
            {mutation.isPending ? "Generating..." : "Generate playlist"}
          </button>

          {mutation.isError ? (
            <p className="error-text">{(mutation.error as Error).message}</p>
          ) : null}
        </form>
      </SectionCard>

      <SectionCard
        eyebrow="How To Read This"
        title="What this builder already proves"
        subtitle="Even before the real dataset lands, the UI and API contract are aligned with the final architecture."
      >
        <ul className="bullet-list">
          <li>The builder already sends a typed playlist-generation request to the backend.</li>
          <li>The backend already chooses between BFS, DFS, UCS, IDS, A*, and IDA*.</li>
          <li>Cluster and genre targets are first-class fields, not demo-only placeholders.</li>
          <li>When the dataset arrives, this form does not need redesign; it just gets better data.</li>
        </ul>
      </SectionCard>
    </div>
  );
}
