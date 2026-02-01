import { useEffect, useState, type FC } from 'react'
import { fetchSimilarProjects, type Project } from '../api/mock'

type ProjectsTabProps = {
  lastIdeaText: string
}

const ProjectsTab: FC<ProjectsTabProps> = ({ lastIdeaText }) => {
  const [projects, setProjects] = useState<Project[]>([])
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    let isActive = true

    if (!lastIdeaText.trim()) {
      setProjects([])
      return
    }

    setIsLoading(true)
    fetchSimilarProjects(lastIdeaText)
      .then((data) => {
        if (isActive) {
          setProjects(data)
        }
      })
      .finally(() => {
        if (isActive) {
          setIsLoading(false)
        }
      })

    return () => {
      isActive = false
    }
  }, [lastIdeaText])

  if (!lastIdeaText.trim()) {
    return <p className="empty-state">Submit an idea to see similar projects.</p>
  }

  if (isLoading) {
    return <p className="loading-state">Loading similar projects…</p>
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
          <p className="card__summary">{project.summary}</p>
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
