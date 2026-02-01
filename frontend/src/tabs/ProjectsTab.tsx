import type { FC } from 'react'
import type { Project } from '../api/mock'

type ProjectsTabProps = {
  lastIdeaText: string
  isScoring: boolean
  projects: Project[]
}

const ProjectsTab: FC<ProjectsTabProps> = ({ lastIdeaText, isScoring, projects }) => {
  if (!lastIdeaText.trim()) {
    return <p className="empty-state">Submit an idea to see similar projects.</p>
  }

  if (isScoring) {
    return <p className="loading-state">Loading similar projects…</p>
  }

  if (!projects.length) {
    return <p className="empty-state">No close matches found yet.</p>
  }

  return (
    <div className="card-list">
      {projects.map((project) => (
        <article className="card" key={project.id}>
          <header className="card__header">
            <h3>{project.title}</h3>
            <span className="similarity-chip">
              {(project.similarity * 100).toFixed(0)}% match
            </span>
          </header>
          <p className="card__summary">
            {project.url ? (
              <a href={project.url} target="_blank" rel="noreferrer">
                {project.summary}
              </a>
            ) : (
              project.summary
            )}
          </p>
          <div className="similarity-bar" role="presentation">
            <span style={{ width: `${project.similarity * 100}%` }} />
          </div>
          <div className="tag-row">
            {project.tags.map((tag) => (
              <span className="tag" key={tag}>
                {tag}
              </span>
            ))}
          </div>
        </article>
      ))}
    </div>
  )
}

export default ProjectsTab
