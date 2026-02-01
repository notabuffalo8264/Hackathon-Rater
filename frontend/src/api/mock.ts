import { characters } from '../data/characters'

export type Project = {
  id: string
  title: string
  summary: string
  similarity: number
  tags: string[]
  url?: string
}

export type Suggestion = {
  id: string
  text: string
  impact: 'low' | 'med' | 'high'
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

export const fetchProjects = async (): Promise<Neighbor[]> =>
  getJson<Neighbor[]>('/projects')

export const fetchSuggestions = async (): Promise<string[]> =>
  getJson<string[]>('/suggestions')

const impacts: Suggestion['impact'][] = ['low', 'med', 'high']

export const buildProjectsFromNeighbors = (neighbors: Neighbor[]): Project[] =>
  neighbors.map((neighbor, index) => ({
    id: neighbor.id ?? `${index}`,
    title: neighbor.title,
    summary: neighbor.tagline || neighbor.snippet,
    similarity: neighbor.similarity,
    tags: neighbor.built_with_tags ?? [],
    url: neighbor.repo_url ?? neighbor.demo_url ?? neighbor.url ?? undefined,
  }))

export const buildSuggestionsFromList = (suggestions: string[]): Suggestion[] =>
  suggestions.map((text, index) => ({
    id: `${index}-${text.slice(0, 24)}`,
    text,
    impact: impacts[index % impacts.length],
  }))

export const getCharacterName = (id: string) =>
  characters.find((character) => character.id === id)?.name ?? 'Unknown'
