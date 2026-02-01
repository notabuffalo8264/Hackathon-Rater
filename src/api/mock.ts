import { characters } from '../data/characters'

export type Project = {
  id: string
  title: string
  summary: string
  similarity: number
  tags: string[]
}

export type Suggestion = {
  id: string
  text: string
  impact: 'low' | 'med' | 'high'
}

const delay = (min = 300, max = 700) =>
  new Promise((resolve) => setTimeout(resolve, Math.random() * (max - min) + min))

const hashString = (value: string) => {
  let hash = 0
  for (let i = 0; i < value.length; i += 1) {
    hash = (hash * 31 + value.charCodeAt(i)) % 100000
  }
  return Math.abs(hash)
}

const commentPools = {
  harsh: [
    'Oof. We need a new angle.',
    'This needs a rethink.',
    'Concerned. Let’s iterate.',
  ],
  skeptical: [
    'Interesting… but it’s rough.',
    'I see the intent, not the polish.',
    'Let’s sand the edges.',
  ],
  neutral: [
    'Not bad. There’s potential.',
    'Mixed signals, but promising.',
    'A decent start. Keep going.',
  ],
  positive: [
    'Nice. This could work!',
    'Strong foundation here.',
    'I like where this is headed.',
  ],
  excited: [
    'This is 🔥. Run with it.',
    'Big energy. Ship it.',
    'Excellent. Keep the momentum.',
  ],
}

const characterFlavor: Record<string, string[]> = {
  'monacle-man': ['Hmm… quite intriguing.', 'Remarkably refined.', 'A bold proposal.'],
  'sniffer-dog': ['*sniff sniff* promising!', 'I smell potential.', 'This one has a scent.'],
  'wizard-orb': ['The orb foresees… success!', 'Mystic signs are strong.', 'The future glows.'],
}

export const commentForScore = (score: number, characterId: string) => {
  const poolKey =
    score <= 19
      ? 'harsh'
      : score <= 39
        ? 'skeptical'
        : score <= 59
          ? 'neutral'
          : score <= 79
            ? 'positive'
            : 'excited'

  const basePool = commentPools[poolKey]
  const flavorPool = characterFlavor[characterId]
  const pool = flavorPool?.length ? [...basePool, ...flavorPool] : basePool
  const selection = pool[score % pool.length]

  return selection
}

export const scoreIdea = async (ideaText: string, characterId: string) => {
  await delay()
  const seed = hashString(`${ideaText}:${characterId}`)
  const score = seed % 101
  const comment = commentForScore(score, characterId)

  return { score, comment }
}

export const fetchSimilarProjects = async (ideaText: string): Promise<Project[]> => {
  await delay()
  const seed = hashString(ideaText)
  const baseTitles = [
    'Idea Radar',
    'Concept Compass',
    'PitchPulse',
    'Vision Forge',
    'Market Echo',
  ]
  const baseTags = ['AI', 'SaaS', 'UX', 'Growth', 'Community', 'Analytics']

  return baseTitles.map((title, index) => {
    const similarity = Math.min(0.95, 0.35 + ((seed + index * 17) % 60) / 100)
    const tagOffset = (seed + index) % baseTags.length
    return {
      id: `${seed}-${index}`,
      title,
      summary: `A concept that overlaps with “${ideaText.slice(0, 40)}” in focus and audience.`,
      similarity,
      tags: [baseTags[tagOffset], baseTags[(tagOffset + 2) % baseTags.length]],
    }
  })
}

export const fetchIdeaSuggestions = async (
  ideaText: string,
): Promise<Suggestion[]> => {
  await delay()
  const seed = hashString(ideaText)
  const baseSuggestions = [
    'Clarify the target user and pain point.',
    'Add a clear success metric for launch.',
    'Tighten the core value proposition.',
    'Prototype a quick landing page test.',
    'Define the differentiator in one sentence.',
  ]
  const impacts: Suggestion['impact'][] = ['low', 'med', 'high']

  return baseSuggestions.map((text, index) => ({
    id: `${seed}-s-${index}`,
    text: `${text}${ideaText ? ' (based on your idea)' : ''}`,
    impact: impacts[(seed + index) % impacts.length],
  }))
}

export const getCharacterName = (id: string) =>
  characters.find((character) => character.id === id)?.name ?? 'Unknown'
