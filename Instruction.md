# directions.txt — Build a JS Frontend from the Whiteboard Mock
Goal: Create ONLY the frontend (no backend). Implement a single-page web UI matching the mock:
- Center: a changeable “person” (character/avatar) who rates your ideas.
- Below center: an idea input box + submit button.
- From the person: a speech bubble showing (1) an expression/short comment based on score and (2) the numeric score to the upper right of the "person".
- Left side: a vertical panel with tabs (3 working tabs now) that is EASY to extend with more tabs later.
- Each tab has scrollable content area.

## Tech / Constraints
- Use React + TypeScript + Vite (preferred), OR plain React JS if needed. Keep dependencies minimal.
- Styling: CSS modules or plain CSS. Use Flexbox/Grid. Must be responsive.
- No backend calls required; create mock “API” functions returning Promises with fake data.
- All state lives in the frontend.
- Tabs must be data-driven from a config array so adding a new tab is just adding a new object.

## App Layout Requirements
Overall layout:
- Full height viewport (100vh).
- Left: a fixed-width sidebar (e.g., 320px) containing:
  - Tab headers (stacked vertically, clickable).
  - Tab content area below headers that scrolls independently.
- Right/main area takes the remaining width:
  - Centered character panel (avatar + speech bubble).
  - Idea input box directly below the character.
  - Optional: small helper text.

Responsive behavior:
- On narrow screens (< 900px): sidebar collapses to top (horizontal tabs) or becomes a drawer; choose one approach and implement.
- Main character always remains prominent.

## Core Components (Suggested)
1) App
   - Holds global state: activeTabId, selectedCharacterId, ideaText, lastScore, lastComment, loading flags
   - Renders <SidebarTabs /> and <MainRater />

2) SidebarTabs
   - Props: tabs[], activeTabId, onTabChange
   - Renders tab buttons from config array
   - Renders active tab content in a scrollable container

3) TabContent components
   - ProjectsTab: list of “similar projects” (from mock API)
   - SuggestionsTab: list of idea improvement suggestions (from mock API)
   - CustomizationTab: character picker + preview + optional settings

4) MainRater
   - Shows selected character (avatar/illustration)
   - SpeechBubble anchored to character
   - IdeaInput box below with Submit button
   - On submit: calls mock scoring function, updates score & comment, triggers sidebar refresh (optional)

5) SpeechBubble
   - Displays comment + score
   - “Tail” points to character
   - Should animate subtly on new rating (e.g., fade/slide)

6) CharacterAvatar
   - Renders character visual; start with simple SVGs/emoji or local placeholder images
   - Must update when user changes character in CustomizationTab

## Data Model / State
### Characters
Create a character catalog array in /src/data/characters.ts:
- id: string
- name: string (e.g., "Monacle Man", "Sniffer Dog", "Wizard Orb")
- description: string
- avatarType: "emoji" | "svg" | "image"
- avatar: string (emoji char OR SVG path OR image URL)

Initial character options (from whiteboard notes):
- Monacle Man
- Sniffer Dog
- Wizard Orb

### Tabs (Must be easily extendable)
Create in /src/data/tabs.ts:
tabs = [
  { id: "projects", label: "Projects", render: <ProjectsTab /> },
  { id: "suggestions", label: "Idea Suggestions", render: <SuggestionsTab /> },
  { id: "customize", label: "Customization", render: <CustomizationTab /> },
]
Implementation note: the tabs should be driven by this array; adding a new tab should not require code changes elsewhere.

### Rating output
When user submits an idea:
- score: integer 0..100 (comes from backend)
- comment: short phrase based on score (have a list of these with a range where they migh show up (1-100) then a random one will show up based on the pool of phrases based on the current rating)
- expression: optional (e.g., emoji or label)
Speech bubble should show:
- A short comment line (expression/comment)
- The numeric score, e.g., "57/100"

## Mock APIs (No Backend)
Create /src/api/mock.ts with Promise-based functions:
- scoreIdea(ideaText: string, characterId: string): Promise<{ score: number; comment: string }>
- fetchSimilarProjects(ideaText: string): Promise<Project[]>
- fetchIdeaSuggestions(ideaText: string): Promise<Suggestion[]>

Use setTimeout to simulate latency (300–700ms).
Use deterministic scoring for stability (e.g., hash ideaText to 0..100).
Return mock lists that look realistic:
Project: { id, title, summary, similarity (0..1), tags[] }
Suggestion: { id, text, impact ("low"|"med"|"high") }

On initial load (no idea submitted yet):
- Speech bubble should show a neutral prompt: “Tell me your idea.”
- Tabs can show empty states: “Submit an idea to see results.”

## Scoring-to-Comment Mapping
Implement a function commentForScore(score):
- 0–19: harsh/concerned tone (but not offensive)
  Example: “Oof. We need a new angle.”
- 20–39: skeptical
  Example: “Interesting… but it’s rough.”
- 40–59: neutral/mixed
  Example: “Not bad. There’s potential.”
- 60–79: positive
  Example: “Nice. This could work!”
- 80–100: excited
  Example: “This is 🔥. Run with it.”
- You can add more

Also optionally vary by character:
- Monacle Man: “Hmm…” “Quite intriguing…”
- Sniffer Dog: “*sniff sniff* promising!”
- Wizard Orb: “The orb foresees… success!”

## Tab Behavior
- There is always exactly one active tab.
- Default active tab is the first tab in the config array ("projects").
- Clicking a tab:
  - Deactivates previous tab
  - Activates clicked tab
- Each tab content area must be independently scrollable:
  - The tab header list stays fixed
  - The content container uses overflow-y: auto and height: calc(100vh - headerHeight)

## UI Details (Match Whiteboard)
Main area:
- Character centered with enough whitespace.
- Speech bubble on upper-right of the character head, with a tail pointing toward them.
- Idea input box below: wide rounded rectangle.
  - Includes placeholder text: “Type your idea…”
  - Submit button to the right OR below (responsive).
- While loading score: show “Thinking…” in bubble and disable submit.

Sidebar:
- Tab headers on top, visible at all times.
- Content below changes with active tab.
- Projects tab content:
  - List cards with title + summary + similarity bar/chip
- Suggestions tab content:
  - Bulleted or card list; each suggestion has an “impact” badge
- Customization tab content:
  - Character selection as cards or radio list with avatar preview
  - Selecting updates the main character immediately
  - (Optional) a “voice tone” slider or toggle, but keep minimal

## Accessibility / UX
- Keyboard navigation:
  - Tabs reachable via Tab key; Enter/Space activates.
  - Idea input focused on page load (optional).
- ARIA:
  - Tabs: role="tablist", each tab role="tab", panel role="tabpanel"
- Colors/contrast:
  - Clear active tab highlight
  - Bubble text readable
- Empty states:
  - Friendly messages when no idea yet

## File/Folder Structure
Create:
- /src/main.tsx
- /src/App.tsx
- /src/components/SidebarTabs.tsx
- /src/components/MainRater.tsx
- /src/components/SpeechBubble.tsx
- /src/components/CharacterAvatar.tsx
- /src/tabs/ProjectsTab.tsx
- /src/tabs/SuggestionsTab.tsx
- /src/tabs/CustomizationTab.tsx
- /src/data/characters.ts
- /src/data/tabs.ts
- /src/api/mock.ts
- /src/styles/app.css (or modules)

## Implementation Notes
- Keep “activeTabId” in App state.
- Keep “selectedCharacterId” in App state.
- Keep “ideaText” and “lastIdeaText”:
  - lastIdeaText is what the tabs use to fetch mock data.
  - Tabs should refresh their mock data whenever lastIdeaText changes.
- Use React hooks:
  - useEffect to load projects/suggestions when lastIdeaText updates.
- Avoid heavy state libraries.

## Acceptance Checklist
- [ ] App renders a sidebar with 3 tabs; default open tab is “Projects”.
- [ ] Clicking tabs switches active tab; only one open at a time.
- [ ] Each tab content scrolls when overflowing.
- [ ] Main area shows character + speech bubble + idea input.
- [ ] Character can be changed in Customization tab; main avatar updates immediately.
- [ ] Submitting idea updates score + comment in speech bubble.
- [ ] Projects tab shows mock “similar projects” for the submitted idea.
- [ ] Suggestions tab shows mock suggestions for the submitted idea.
- [ ] No backend required; all data via mock Promise functions.
- [ ] Adding a new tab requires only adding one object to tabs config.

## Visual Polish Targets (Optional)
- Subtle bubble pop animation on new score.
- Similarity displayed as a small progress bar.
- Active tab has a left border highlight.
- Use consistent rounded corners.

Deliverable: a working Vite+React frontend project implementing the above exactly.
