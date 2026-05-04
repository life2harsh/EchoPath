import { useDeferredValue, useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { AudioPreview } from "../components/AudioPreview";
import { SectionCard } from "../components/SectionCard";
import { TrackCard } from "../components/TrackCard";
import { fetchTracks } from "../lib/api";
import type { TrackRecord } from "../lib/types";

export function LibraryPage() {
  const [search, setSearch] = useState("");
  const [selectedTrack, setSelectedTrack] = useState<TrackRecord | null>(null);
  const deferredSearch = useDeferredValue(search);

  const tracksQuery = useQuery({
    queryKey: ["tracks", deferredSearch],
    queryFn: () => fetchTracks(deferredSearch),
  });

  useEffect(() => {
    if (!selectedTrack && tracksQuery.data?.length) {
      setSelectedTrack(tracksQuery.data[0]);
    }
  }, [selectedTrack, tracksQuery.data]);

  return (
    <div className="page-grid page-grid--library">
      <SectionCard
        eyebrow="Music Library"
        title="Search the working track universe"
        subtitle="This is the first surface we’ll swap from sample metadata to the real extracted library."
        actions={
          <label className="search-input">
            <span>Search</span>
            <input
              type="search"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Try artist, title, or genre"
            />
          </label>
        }
      >
        <div className="track-grid">
          {tracksQuery.data?.map((track) => (
            <TrackCard
              key={track.track_id}
              track={track}
              active={selectedTrack?.track_id === track.track_id}
              onSelect={setSelectedTrack}
            />
          ))}
        </div>
      </SectionCard>

      <SectionCard
        eyebrow="Track Inspector"
        title="Preview metadata, audio readiness, and feature cues"
        subtitle="Waveforms and spectrogram media can plug into this card later without changing the route shape."
      >
        <AudioPreview track={selectedTrack} />
      </SectionCard>
    </div>
  );
}
