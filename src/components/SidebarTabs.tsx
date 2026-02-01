import type { FC } from 'react'
import type { TabConfig, TabRenderProps } from '../data/tabs.ts'

type SidebarTabsProps = {
  tabs: TabConfig[]
  activeTabId: string
  onTabChange: (tabId: string) => void
  renderProps: TabRenderProps
}

const SidebarTabs: FC<SidebarTabsProps> = ({
  tabs,
  activeTabId,
  onTabChange,
  renderProps,
}) => {
  const activeTab = tabs.find((tab) => tab.id === activeTabId) ?? tabs[0]
  const ActiveComponent = activeTab?.Component

  return (
    <aside className="sidebar" aria-label="Idea insights">
      <div className="tablist" role="tablist" aria-orientation="vertical">
        {tabs.map((tab) => {
          const isActive = tab.id === activeTab?.id
          return (
            <button
              key={tab.id}
              type="button"
              role="tab"
              aria-selected={isActive}
              aria-controls={`panel-${tab.id}`}
              id={`tab-${tab.id}`}
              className={`tab-button ${isActive ? 'is-active' : ''}`}
              onClick={() => onTabChange(tab.id)}
            >
              {tab.label}
            </button>
          )
        })}
      </div>
      <div className="tab-panels">
        {activeTab && ActiveComponent && (
          <div
            className="tab-panel"
            role="tabpanel"
            id={`panel-${activeTab.id}`}
            aria-labelledby={`tab-${activeTab.id}`}
          >
            <ActiveComponent {...renderProps} />
          </div>
        )}
      </div>
    </aside>
  )
}

export default SidebarTabs
