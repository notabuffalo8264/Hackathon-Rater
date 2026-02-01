import type { FC } from 'react'
import { characters } from '../data/characters'
import CharacterAvatar from '../components/CharacterAvatar'
import type { Project, Suggestion } from '../api/mock'

type CustomizationTabProps = {
  lastIdeaText: string
  selectedCharacterId: string
  onSelectCharacter: (id: string) => void
  isScoring: boolean
  projects: Project[]
  totalProjects: number | null
  suggestions: Suggestion[]
}

const CustomizationTab: FC<CustomizationTabProps> = ({
  selectedCharacterId,
  onSelectCharacter,
}) => {
  return (
    <div className="card-list">
      {characters.map((character) => {
        const isSelected = character.id === selectedCharacterId
        return (
          <button
            key={character.id}
            type="button"
            className={`card card--selectable ${isSelected ? 'is-selected' : ''}`}
            onClick={() => onSelectCharacter(character.id)}
            aria-pressed={isSelected}
          >
            <div className="card__header">
              <CharacterAvatar character={character} size="md" state="idle" />
              <div>
                <h3>{character.name}</h3>
                <p className="card__summary">{character.description}</p>
              </div>
            </div>
          </button>
        )
      })}
    </div>
  )
}

export default CustomizationTab
