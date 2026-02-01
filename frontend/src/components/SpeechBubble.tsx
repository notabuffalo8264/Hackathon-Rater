import type { FC } from 'react'

type SpeechBubbleProps = {
  comment: string
  score: number | null
  isThinking: boolean
}

const SpeechBubble: FC<SpeechBubbleProps> = ({
  comment,
  score,
  isThinking,
}) => {
  return (
    <div className="speech-bubble">
      <div className="speech-bubble__text">{comment}</div>
      {score !== null && (
        <div className="speech-bubble__score" aria-label={`Score ${score} out of 100`}>
          {score}/100
        </div>
      )}
    </div>
  )
}

export default SpeechBubble
