import type { FC } from 'react'
import type { Project } from '../api/mock'

type ProjectsTabProps = {
  lastIdeaText: string
  isScoring: boolean
  projects: Project[]
  totalProjects: number | null
}

const ProjectsTab: FC<ProjectsTabProps> = ({
  lastIdeaText,
  isScoring,
  projects,
  totalProjects,
}) => {
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
        <article className="card project-card" key={project.id}>
          <header className="card__header project-card__header">
            <h3>{project.title}</h3>
            <span className="similarity-chip project-card__chip">
              {(project.similarity * 100).toFixed(0)}% match
            </span>
          </header>
          <p className="card__summary">{project.summary}</p>
          <div className="project-meta">
            {project.startedDate && (
              <span className="project-date">
                {new Date(project.startedDate).toLocaleDateString()}
              </span>
            )}
            <div className="project-links">
              {project.devpostUrl && (
                <a href={project.devpostUrl} target="_blank" rel="noreferrer">
                  Devpost
                </a>
              )}
              {project.repoUrl && (
                <a href={project.repoUrl} target="_blank" rel="noreferrer">
                  GitHub
                </a>
              )}
            </div>
          </div>
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
