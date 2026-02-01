import type { FC } from 'react'
import { characters } from '../data/characters'
import CharacterAvatar from '../components/CharacterAvatar'

type CustomizationTabProps = {
  selectedCharacterId: string
  onSelectCharacter: (id: string) => void
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
              <CharacterAvatar character={character} size="md" />
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
