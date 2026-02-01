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
          <p className="card__summary">{suggestion.text}</p>
          <span className={`impact impact--${suggestion.impact}`}>
            {suggestion.impact} impact
          </span>
        </article>
      ))}
    </div>
  )
}

export default SuggestionsTab
