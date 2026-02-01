import type { FC } from 'react'
import type { Character } from '../data/characters'

type CharacterAvatarProps = {
  character: Character
  size?: 'sm' | 'md' | 'lg'
}

const CharacterAvatar: FC<CharacterAvatarProps> = ({
  character,
  size = 'lg',
}) => {
  const className = `avatar avatar--${size}`

  if (character.avatarType === 'image') {
    return (
      <img
        className={className}
        src={character.avatar}
        alt={character.name}
      />
    )
  }

  if (character.avatarType === 'svg') {
    return (
      <span
        className={className}
        aria-label={character.name}
        role="img"
        dangerouslySetInnerHTML={{ __html: character.avatar }}
      />
    )
  }

  return (
    <span className={className} aria-label={character.name} role="img">
      {character.avatar}
    </span>
  )
}

export default CharacterAvatar
