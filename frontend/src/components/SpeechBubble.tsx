import type { FC } from 'react'

type SpeechBubbleProps = {
  comment: string
  score: number | null
  isThinking: boolean
  animateKey: string
}

const SpeechBubble: FC<SpeechBubbleProps> = ({
  comment,
  score,
  isThinking,
  animateKey,
}) => {
  return (
    <div key={animateKey} className="speech-bubble bubble--animate">
      <div className="speech-bubble__text">
        {isThinking ? 'Thinking…' : comment}
      </div>
      {score !== null && (
        <div className="speech-bubble__score" aria-label={`Score ${score} out of 100`}>
          {score}/100
        </div>
      )}
    </div>
  )
}

export default SpeechBubble
