import { BookOpen, MessageSquareText, Sparkles, X } from 'lucide-react'
import { useState } from 'react'

const STORAGE_KEY = 'onboarding_tour_dismissed'

const STEPS = [
  {
    icon: <MessageSquareText size={18} />,
    title: 'Ask anything about your college',
    text: 'Attendance rules, exam dates, scholarships, hostel procedures, placements — just type your question.',
  },
  {
    icon: <Sparkles size={18} />,
    title: 'Answers are grounded, not guessed',
    text: "The assistant only answers from official uploaded documents, and says so clearly when it can't find something.",
  },
  {
    icon: <BookOpen size={18} />,
    title: 'Every answer cites its source',
    text: 'Check the "Sources" box under each answer to see exactly which document and page it came from.',
  },
]

export default function OnboardingTour() {
  const [dismissed, setDismissed] = useState(() => localStorage.getItem(STORAGE_KEY) === 'true')

  if (dismissed) return null

  function dismiss() {
    localStorage.setItem(STORAGE_KEY, 'true')
    setDismissed(true)
  }

  return (
    <div
      className="card"
      style={{
        marginBottom: 20,
        background: 'var(--gradient-brand)',
        color: '#fff',
        border: 'none',
        position: 'relative',
      }}
    >
      <button
        onClick={dismiss}
        className="icon-btn"
        style={{ position: 'absolute', top: 14, right: 14, color: 'rgba(255,255,255,0.85)' }}
        aria-label="Dismiss"
      >
        <X size={16} />
      </button>
      <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
        {STEPS.map((step) => (
          <div key={step.title} style={{ flex: '1 1 200px', display: 'flex', gap: 10 }}>
            <div
              style={{
                width: 32,
                height: 32,
                borderRadius: 9,
                background: 'rgba(255,255,255,0.18)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
              }}
            >
              {step.icon}
            </div>
            <div>
              <div style={{ fontWeight: 700, fontSize: 13.5, marginBottom: 3 }}>{step.title}</div>
              <div style={{ fontSize: 12.5, opacity: 0.92, lineHeight: 1.45 }}>{step.text}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}