import type { FC } from 'react'
import type { Character } from '../data/characters'

type CharacterAvatarProps = {
  character: Character
  size?: 'sm' | 'md' | 'lg'
  state?: 'idle' | 'active'
}

const CharacterAvatar: FC<CharacterAvatarProps> = ({
  character,
  size = 'lg',
  state = 'idle',
}) => {
  const className = `avatar avatar--${size}`

  if (character.avatarType === 'image') {
    const src =
      state === 'active'
        ? character.avatarActive ?? character.avatar
        : character.avatarIdle ?? character.avatar
    return (
      <img
        className={className}
        src={src}
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
