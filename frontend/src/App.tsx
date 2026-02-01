import { useState } from 'react'
import MainRater from './components/MainRater'
import SidebarTabs from './components/SidebarTabs'
import {
  buildProjectsFromNeighbors,
  buildSuggestionsFromList,
  commentForScore,
  fetchProjects,
  fetchScore,
  fetchSuggestions,
  postIdea,
  type Project,
  type Suggestion,
} from './api/mock'
import { getCharacterById } from './data/characters'
import { tabs } from './data/tabs'

function App() {
  const [activeTabId, setActiveTabId] = useState(tabs[0]?.id ?? 'projects')
  const [selectedCharacterId, setSelectedCharacterId] = useState(
    'monacle-man',
  )
  const [ideaDescription, setIdeaDescription] = useState('')
  const [lastIdeaText, setLastIdeaText] = useState('')
  const [lastScore, setLastScore] = useState<number | null>(null)
  const [lastComment, setLastComment] = useState('Tell me your idea.')
  const [isScoring, setIsScoring] = useState(false)
  const [projects, setProjects] = useState<Project[]>([])
  const [suggestions, setSuggestions] = useState<Suggestion[]>([])

  const handleSubmit = async () => {
    if (ideaDescription.trim().length === 0 || isScoring) {
      return
    }

    setIsScoring(true)
    try {
      await postIdea(ideaDescription)
      const [scoreResponse, projectNeighbors, suggestionList] =
        await Promise.all([
          fetchScore(),
          fetchProjects(),
          fetchSuggestions(),
        ])
      const score = scoreResponse.score_recent ?? scoreResponse.score_all
      setLastScore(score)
      setLastComment(commentForScore(score, selectedCharacterId))
      setLastIdeaText(ideaDescription.trim())
      setProjects(buildProjectsFromNeighbors(projectNeighbors))
      setSuggestions(buildSuggestionsFromList(suggestionList))
    } catch (error) {
      setLastScore(null)
      setLastComment(
        error instanceof Error
          ? error.message
          : 'Something went wrong. Please try again.',
      )
    } finally {
      setIsScoring(false)
    }
  }

  const character = getCharacterById(selectedCharacterId)

  return (
    <div className="app">
      <div className="app__layout">
        <SidebarTabs
          tabs={tabs}
          activeTabId={activeTabId}
          onTabChange={setActiveTabId}
          renderProps={{
            lastIdeaText,
            selectedCharacterId,
            onSelectCharacter: setSelectedCharacterId,
            isScoring,
            projects,
            suggestions,
          }}
        />
        <main className="main">
          <MainRater
            character={character}
            ideaDescription={ideaDescription}
            onDescriptionChange={setIdeaDescription}
            onSubmit={handleSubmit}
            isScoring={isScoring}
            lastScore={lastScore}
            lastComment={lastComment}
          />
        </main>
      </div>
    </div>
  )
}

export default App
