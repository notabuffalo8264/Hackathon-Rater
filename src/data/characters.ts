export type AvatarType = 'emoji' | 'svg' | 'image'

export type Character = {
  id: string
  name: string
  description: string
  avatarType: AvatarType
  avatar: string
}

export const characters: Character[] = [
  {
    id: 'monacle-man',
    name: 'Monacle Man',
    description: 'A refined critic with a sharp eye for ideas.',
    avatarType: 'emoji',
    avatar: '🧐',
  },
  {
    id: 'sniffer-dog',
    name: 'Sniffer Dog',
    description: 'Sniffs out promising concepts and hidden flaws.',
    avatarType: 'emoji',
    avatar: '🐶',
  },
  {
    id: 'wizard-orb',
    name: 'Wizard Orb',
    description: 'Sees the future of your idea with mystical clarity.',
    avatarType: 'emoji',
    avatar: '🔮',
  },
]

export const getCharacterById = (id: string) =>
  characters.find((character) => character.id === id) ?? characters[0]
