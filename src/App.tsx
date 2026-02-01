import { useState } from 'react'
import MainRater from './components/MainRater'
import SidebarTabs from './components/SidebarTabs'
import { scoreIdea } from './api/mock'
import { getCharacterById } from './data/characters'
import { tabs } from './data/tabs'

function App() {
  const [activeTabId, setActiveTabId] = useState(tabs[0]?.id ?? 'projects')
  const [selectedCharacterId, setSelectedCharacterId] = useState(
    'monacle-man',
  )
  const [ideaText, setIdeaText] = useState('')
  const [lastIdeaText, setLastIdeaText] = useState('')
  const [lastScore, setLastScore] = useState<number | null>(null)
  const [lastComment, setLastComment] = useState('Tell me your idea.')
  const [isScoring, setIsScoring] = useState(false)

  const handleSubmit = async () => {
    if (!ideaText.trim() || isScoring) {
      return
    }

    setIsScoring(true)
    try {
      const result = await scoreIdea(ideaText, selectedCharacterId)
      setLastScore(result.score)
      setLastComment(result.comment)
      setLastIdeaText(ideaText)
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
          }}
        />
        <main className="main">
          <MainRater
            character={character}
            ideaText={ideaText}
            onIdeaChange={setIdeaText}
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
