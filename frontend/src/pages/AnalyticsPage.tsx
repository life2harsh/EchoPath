import { useQuery } from "@tanstack/react-query";

import { SectionCard } from "../components/SectionCard";
import { fetchClusters, fetchModels, fetchSearchAlgorithms } from "../lib/api";
import { titleCase } from "../lib/format";

export function AnalyticsPage() {
  const { data: clusters = [] } = useQuery({ queryKey: ["analytics", "clusters"], queryFn: fetchClusters });
  const { data: models = [] } = useQuery({ queryKey: ["analytics", "models"], queryFn: fetchModels });
  const { data: searchAlgorithms = [] } = useQuery({
    queryKey: ["analytics", "search"],
    queryFn: fetchSearchAlgorithms,
  });

  return (
    <div className="page-grid">
      <SectionCard
        eyebrow="Mood Clusters"
        title="Cluster summaries ready for the real embeddings"
        subtitle="These cards already match the outputs we’ll compute from the dataset pipeline."
      >
        <div className="analytics-grid">
          {clusters.map((cluster) => (
            <article key={cluster.cluster_id} className="analytics-card">
              <p className="eyebrow">Cluster {cluster.cluster_id}</p>
              <h3>{cluster.descriptor}</h3>
              <p>{cluster.anchor_genres.join(" / ")}</p>
              <dl className="stats-list">
                <div>
                  <dt>Tempo</dt>
                  <dd>{cluster.avg_tempo}</dd>
                </div>
                <div>
                  <dt>Energy</dt>
                  <dd>{cluster.avg_energy}</dd>
                </div>
                <div>
                  <dt>Valence</dt>
                  <dd>{cluster.avg_valence}</dd>
                </div>
              </dl>
            </article>
          ))}
        </div>
      </SectionCard>

      <SectionCard
        eyebrow="Search Stack"
        title="Algorithm surface already wired"
        subtitle="Benchmarks are still sample-backed, but the API and UI are ready for the real experiment outputs."
      >
        <div className="analytics-grid">
          {searchAlgorithms.map((item) => (
            <article key={item.algorithm} className="analytics-card">
              <p className="eyebrow">{titleCase(item.algorithm)}</p>
              <h3>{item.readiness}</h3>
              <p>{item.notes}</p>
            </article>
          ))}
        </div>
      </SectionCard>

      <SectionCard
        eyebrow="Model Roadmap"
        title="Classical and CNN comparisons"
        subtitle="Once training runs exist, this page can swap from status cards to confusion matrices and benchmark charts."
      >
        <div className="analytics-grid">
          {models.map((model) => (
            <article key={model.model_name} className="analytics-card">
              <p className="eyebrow">{model.family}</p>
              <h3>{model.model_name}</h3>
              <p className={`status-badge status-badge--${model.status}`}>{model.status}</p>
              <p>{model.notes}</p>
            </article>
          ))}
        </div>
      </SectionCard>
    </div>
  );
}
