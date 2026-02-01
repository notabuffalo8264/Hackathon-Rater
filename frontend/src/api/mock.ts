import { characters } from '../data/characters'

export type Project = {
  id: string
  title: string
  summary: string
  similarity: number
  tags: string[]
  url?: string
  repoUrl?: string
  demoUrl?: string
  devpostUrl?: string
  startedDate?: string
}

export type Suggestion = {
  id: string
  text: string
  isBeta?: boolean
}

export type CheckRequest = {
  title: string
  description?: string
  tags?: string[]
  k?: number
}

export type Neighbor = {
  id: string
  title: string
  snippet: string
  url?: string | null
  tagline?: string | null
  description?: string | null
  started_date?: string | null
  built_with_tags?: string[] | null
  hackathon_name?: string | null
  repo_url?: string | null
  demo_url?: string | null
  winner?: boolean | null
  award_texts?: string[] | null
  creators?: Array<{ name?: string; profile_url?: string }> | null
  similarity: number
  semantic_similarity?: number | null
  rare_overlap?: number | null
}

export type CheckResponse = {
  score_all: number
  score_recent: number
  label_all: string
  label_recent: string
  trend_label: string
  trend_note: string
  neighbors_all: Neighbor[]
  neighbors_recent: Neighbor[]
  suggestions: string[]
}

export type ScoreResponse = {
  score_all: number
  score_recent: number
  label_all: string
  label_recent: string
  trend_label: string
  trend_note: string
}

export type StatsResponse = {
  total_projects: number
  recent_projects: number
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

const characterCommentPools: Record<string, typeof commentPools> = {
  'monacle-man': {
    harsh: [
      'Dear me. That needs refinement.',
      'A rough draft at best.',
      'We must elevate this.',
    ],
    skeptical: [
      'An interesting notion… albeit unpolished.',
      'The intent is visible; the execution is not.',
      'Let us improve the form.',
    ],
    neutral: [
      'Quite serviceable, with room to grow.',
      'Mixed, yet promising.',
      'A respectable start.',
    ],
    positive: [
      'Commendable. This could mature nicely.',
      'A strong foundation, indeed.',
      'Well‑considered and tasteful.',
    ],
    excited: [
      'Splendid. This is truly refined.',
      'Exceptional polish. Bravo.',
      'A bold, elegant proposal.',
    ],
  },
  'sniffer-dog': {
    harsh: [
      '*sniff* Hmm… not good.',
      'This trail goes nowhere.',
      'Needs a new scent.',
    ],
    skeptical: [
      '*sniff sniff* maybe…',
      'I’m not sold yet.',
      'Let’s follow the trail further.',
    ],
    neutral: [
      'Not bad. I smell potential.',
      'A decent scent to chase.',
      'There’s something here.',
    ],
    positive: [
      'Oh yes. Promising scent!',
      'This one’s worth chasing.',
      'Nice trail. Keep going.',
    ],
    excited: [
      'Big scent! This is exciting.',
      'I’m all in—run with it!',
      'Top‑tier trail. Let’s go!',
    ],
  },
  'wizard-orb': {
    harsh: [
      'The orb frowns upon this path.',
      'Dark omens… rethink the spell.',
      'The magic is not yet formed.',
    ],
    skeptical: [
      'The mist is unclear.',
      'I sense promise, but it wavers.',
      'We must strengthen the incantation.',
    ],
    neutral: [
      'A steady glow. There is potential.',
      'The signs are mixed, yet hopeful.',
      'A fair beginning.',
    ],
    positive: [
      'The orb brightens—well done!',
      'Strong magic in this idea.',
      'The future leans favorable.',
    ],
    excited: [
      'The orb blazes! A powerful vision.',
      'Destiny smiles upon this.',
      'Magnificent—cast it forward!',
    ],
  },
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

  const poolSource = characterCommentPools[characterId] ?? commentPools
  const pool = poolSource[poolKey]
  const selection = pool[Math.floor(Math.random() * pool.length)]

  return selection
}

export const promptForCharacter = (characterId: string) => {
  const prompts: Record<string, string[]> = {
    'monacle-man': [
      'Do share your idea, if you please.',
      'Present your concept, if you will.',
      'I await your proposal.',
    ],
    'sniffer-dog': [
      'Sniff sniff… what’s your idea?',
      'Let me smell the concept!',
      'Share the idea—I’ll follow the trail.',
    ],
    'wizard-orb': [
      'Reveal your idea, and we shall see.',
      'Speak your concept into the orb.',
      'Let us glimpse your vision.',
    ],
  }

  const pool = prompts[characterId] ?? ['Tell me your idea.']
  return pool[Math.floor(Math.random() * pool.length)]
}

const API_BASE = import.meta.env.VITE_API_BASE ?? '/api'

const postCheck = async (payload: CheckRequest): Promise<CheckResponse> => {
  const response = await fetch(`${API_BASE}/check`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    const message = await response.text()
    throw new Error(message || 'Failed to score idea.')
  }

  return (await response.json()) as CheckResponse
}

const getJson = async <T>(path: string): Promise<T> => {
  const response = await fetch(`${API_BASE}${path}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  })

  if (!response.ok) {
    const message = await response.text()
    throw new Error(message || 'Failed to load data.')
  }

  return (await response.json()) as T
}

export const postIdea = async (description: string) =>
  postCheck({
    title: '',
    description,
    tags: [],
  })

export const fetchScore = async (): Promise<ScoreResponse> =>
  getJson<ScoreResponse>('/score')

export const fetchStats = async (): Promise<StatsResponse> =>
  getJson<StatsResponse>('/stats')

export const fetchProjects = async (): Promise<Neighbor[]> =>
  getJson<Neighbor[]>('/projects')

export const fetchSuggestions = async (): Promise<string[]> =>
  getJson<string[]>('/suggestions')

export const buildProjectsFromNeighbors = (neighbors: Neighbor[]): Project[] =>
  neighbors.map((neighbor, index) => ({
    id: neighbor.id ?? `${index}`,
    title: neighbor.title,
    summary: neighbor.tagline || neighbor.snippet,
    similarity: neighbor.similarity,
    tags: neighbor.built_with_tags ?? [],
    url: neighbor.repo_url ?? neighbor.demo_url ?? neighbor.url ?? undefined,
    repoUrl: neighbor.repo_url ?? undefined,
    demoUrl: neighbor.demo_url ?? undefined,
    devpostUrl:
      neighbor.url && neighbor.url.includes('devpost.com')
        ? neighbor.url
        : undefined,
    startedDate: neighbor.started_date ?? undefined,
  }))

const BETA_PREFIX = '[BETA] '

export const buildSuggestionsFromList = (suggestions: string[]): Suggestion[] =>
  suggestions.map((text, index) => {
    const isBeta = text.startsWith(BETA_PREFIX)
    const cleanText = isBeta ? text.slice(BETA_PREFIX.length) : text
    return {
      id: `${index}-${cleanText.slice(0, 24)}`,
      text: cleanText,
      isBeta,
    }
  })

export const getCharacterName = (id: string) =>
  characters.find((character) => character.id === id)?.name ?? 'Unknown'
