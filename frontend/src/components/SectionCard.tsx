import type { PropsWithChildren, ReactNode } from "react";

interface SectionCardProps extends PropsWithChildren {
  eyebrow?: string;
  title: string;
  subtitle?: string;
  actions?: ReactNode;
}

export function SectionCard({ eyebrow, title, subtitle, actions, children }: SectionCardProps) {
  return (
    <section className="section-card">
      <div className="section-card__header">
        <div>
          {eyebrow ? <p className="eyebrow">{eyebrow}</p> : null}
          <h2>{title}</h2>
          {subtitle ? <p className="section-card__subtitle">{subtitle}</p> : null}
        </div>
        {actions ? <div className="section-card__actions">{actions}</div> : null}
      </div>
      {children}
    </section>
  );
}
