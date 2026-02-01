import { useEffect, useState, type FC } from 'react'
import { fetchIdeaSuggestions, type Suggestion } from '../api/mock'

type SuggestionsTabProps = {
  lastIdeaText: string
}

const SuggestionsTab: FC<SuggestionsTabProps> = ({ lastIdeaText }) => {
  const [suggestions, setSuggestions] = useState<Suggestion[]>([])
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    let isActive = true

    if (!lastIdeaText.trim()) {
      setSuggestions([])
      return
    }

    setIsLoading(true)
    fetchIdeaSuggestions(lastIdeaText)
      .then((data) => {
        if (isActive) {
          setSuggestions(data)
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
    return <p className="empty-state">Submit an idea to get suggestions.</p>
  }

  if (isLoading) {
    return <p className="loading-state">Loading suggestions…</p>
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
