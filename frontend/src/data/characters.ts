export type AvatarType = 'emoji' | 'svg' | 'image'

export type Character = {
  id: string
  name: string
  description: string
  avatarType: AvatarType
  avatar: string
  avatarIdle?: string
  avatarActive?: string
}

import monacleManIdle from '../assets/avatars/MonacleMan1.png'
import monacleManActive from '../assets/avatars/MonacleMan2.png'
import snifferDogIdle from '../assets/avatars/SnifferDog1.png'
import snifferDogActive from '../assets/avatars/SnifferDog2.png'
import wizardOrbIdle from '../assets/avatars/WizardOrb1.png'
import wizardOrbActive from '../assets/avatars/WizardOrb2.png'

export const characters: Character[] = [
  {
    id: 'monacle-man',
    name: 'Monacle Man',
    description: 'A refined critic with a sharp eye for ideas.',
    avatarType: 'image',
    avatar: monacleManIdle,
    avatarIdle: monacleManIdle,
    avatarActive: monacleManActive,
  },
  {
    id: 'sniffer-dog',
    name: 'Sniffer Dog',
    description: 'Sniffs out promising concepts and hidden flaws.',
    avatarType: 'image',
    avatar: snifferDogIdle,
    avatarIdle: snifferDogIdle,
    avatarActive: snifferDogActive,
  },
  {
    id: 'wizard-orb',
    name: 'Wizard Orb',
    description: 'Sees the future of your idea with mystical clarity.',
    avatarType: 'image',
    avatar: wizardOrbIdle,
    avatarIdle: wizardOrbIdle,
    avatarActive: wizardOrbActive,
  },
]

export const getCharacterById = (id: string) =>
  characters.find((character) => character.id === id) ?? characters[0]
