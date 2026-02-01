# Idea Rater Frontend

A single-page React + TypeScript app that matches the provided whiteboard mock. It includes:

- A character avatar that rates your idea.
- A speech bubble with a comment + numeric score.
- An idea input + submit button.
- A data-driven sidebar with three tabs (Projects, Idea Suggestions, Customization).
- Mock API calls with simulated latency.

## Getting Started

Install dependencies:

1. `npm install`

Start the dev server:

2. `npm run dev`

Build for production:

3. `npm run build`

Preview the production build:

4. `npm run preview`

## Project Notes

- Tabs are driven by the config array in [src/data/tabs.ts](src/data/tabs.ts).
- Mock API functions live in [src/api/mock.ts](src/api/mock.ts).
- Character catalog lives in [src/data/characters.ts](src/data/characters.ts).
