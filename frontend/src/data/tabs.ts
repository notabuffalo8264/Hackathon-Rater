import type { ComponentType } from 'react'
import ProjectsTab from '../tabs/ProjectsTab'
import SuggestionsTab from '../tabs/SuggestionsTab'
import CustomizationTab from '../tabs/CustomizationTab'
import type { Project, Suggestion } from '../api/mock'

export type TabRenderProps = {
  lastIdeaText: string
  selectedCharacterId: string
  onSelectCharacter: (id: string) => void
  isScoring: boolean
  projects: Project[]
  suggestions: Suggestion[]
}

export type TabConfig = {
  id: string
  label: string
  Component: ComponentType<TabRenderProps>
}

export const tabs: TabConfig[] = [
  {
    id: 'projects',
    label: 'Projects',
    Component: ProjectsTab,
  },
  {
    id: 'suggestions',
    label: 'Idea Suggestions',
    Component: SuggestionsTab,
  },
  {
    id: 'customize',
    label: 'Customization',
    Component: CustomizationTab,
  },
]
