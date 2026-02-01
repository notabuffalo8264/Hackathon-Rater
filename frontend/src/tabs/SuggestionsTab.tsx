import type { FC } from 'react'
import type { Suggestion } from '../api/mock'

type SuggestionsTabProps = {
  lastIdeaText: string
  isScoring: boolean
  suggestions: Suggestion[]
}

const SuggestionsTab: FC<SuggestionsTabProps> = ({
  lastIdeaText,
  isScoring,
  suggestions,
}) => {
  if (!lastIdeaText.trim()) {
    return <p className="empty-state">Submit an idea to get suggestions.</p>
  }

  if (isScoring) {
    return <p className="loading-state">Loading suggestions…</p>
  }

  if (!suggestions.length) {
    return <p className="empty-state">No suggestions yet. Try refining the idea.</p>
  }

  return (
    <div className="card-list">
      {suggestions.map((suggestion) => (
        <article className="card" key={suggestion.id}>
          <div className="card__header">
            <p className="card__summary">{suggestion.text}</p>
            {suggestion.isBeta && <span className="beta-badge">Beta</span>}
          </div>
        </article>
      ))}
    </div>
  )
}

export default SuggestionsTab
