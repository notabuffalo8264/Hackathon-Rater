import { useEffect, useRef, type FC } from 'react'
import type { Character } from '../data/characters'
import CharacterAvatar from './CharacterAvatar'
import SpeechBubble from './SpeechBubble'

type MainRaterProps = {
  character: Character
  ideaDescription: string
  onDescriptionChange: (value: string) => void
  onSubmit: () => void
  isScoring: boolean
  lastScore: number | null
  lastComment: string
}

const MainRater: FC<MainRaterProps> = ({
  character,
  ideaDescription,
  onDescriptionChange,
  onSubmit,
  isScoring,
  lastScore,
  lastComment,
}) => {
  const inputRef = useRef<HTMLTextAreaElement | null>(null)

  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  return (
    <section className="main-rater" aria-label="Idea rating">
      <div className="avatar-stage">
        <div className="avatar-wrapper">
          <CharacterAvatar
            character={character}
            state={lastScore === null ? 'idle' : 'active'}
          />
        </div>
        <SpeechBubble
          comment={lastComment}
          score={lastScore}
          isThinking={isScoring}
        />
      </div>

      <form
        className="idea-form"
        onSubmit={(event) => {
          event.preventDefault()
          onSubmit()
        }}
      >
        <textarea
          ref={inputRef}
          className="idea-input idea-input--description"
          placeholder="Describe your idea…"
          value={ideaDescription}
          onChange={(event) => onDescriptionChange(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
              event.preventDefault()
              onSubmit()
            }
          }}
          disabled={isScoring}
          aria-label="Idea description"
          rows={1}
        />
        <button
          className="idea-submit"
          type="submit"
          disabled={isScoring || ideaDescription.trim().length === 0}
        >
          {isScoring ? 'Scoring…' : 'Submit'}
        </button>
      </form>
      <p className="helper-text">Share your idea and get instant feedback.</p>
    </section>
  )
}

export default MainRater
