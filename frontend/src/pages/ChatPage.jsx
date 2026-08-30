import { documentApi } from '../api/endpoints'
import { BookOpen, MessageCircle, Send, Sparkles, ThumbsDown, ThumbsUp } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { chatApi } from '../api/endpoints'
import { streamChatMessage } from '../api/streaming'

const SUGGESTIONS = [
  'What is the minimum attendance required?',
  'When do semester exams start?',
  'What documents are needed for the scholarship?',
  'What is the hostel admission procedure?',
]

export default function ChatPage() {
  const { conversationId } = useParams()
  const navigate = useNavigate()
  const [messages, setMessages] = useState([])
  const [sourcesByMessageId, setSourcesByMessageId] = useState({})
  const [feedbackByMessageId, setFeedbackByMessageId] = useState({})
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [streamingText, setStreamingText] = useState('')
  const [loadingConversation, setLoadingConversation] = useState(true)
  const bottomRef = useRef(null)
  const textareaRef = useRef(null)

  useEffect(() => {
    if (!conversationId) {
      setMessages([])
      setLoadingConversation(false)
      return
    }
    setLoadingConversation(true)
    chatApi
      .getConversation(conversationId)
      .then((res) => {
        setMessages(res.data.messages)
        const initialFeedback = {}
        res.data.messages.forEach((m) => {
          if (m.is_helpful !== null && m.is_helpful !== undefined) initialFeedback[m.id] = m.is_helpful
        })
        setFeedbackByMessageId(initialFeedback)
      })
      .catch(() => navigate('/chat'))
      .finally(() => setLoadingConversation(false))
  }, [conversationId])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, sending, streamingText])

  async function submitQuestion(content) {
    content = content.trim()
    if (!content) return

    let targetId = conversationId
    if (!targetId) {
      const res = await chatApi.createConversation(null)
      targetId = res.data.id
      navigate(`/chat/${targetId}`, { replace: true })
    }

    const userMessage = { id: `temp-${Date.now()}`, role: 'USER', content, created_at: new Date().toISOString() }
    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setSending(true)
    setStreamingText('')

    let latestSources = []
    let latestText = ''

    await streamChatMessage(targetId, content, {
      onSources: (sources) => {
        latestSources = sources
      },
      onToken: (text) => {
        latestText += text
        setStreamingText(latestText)
      },
      onDone: (messageId) => {
        setMessages((prev) => [
          ...prev,
          { id: messageId, role: 'ASSISTANT', content: latestText, created_at: new Date().toISOString() },
        ])
        setSourcesByMessageId((prev) => ({ ...prev, [messageId]: latestSources }))
        setStreamingText('')
        setSending(false)
      },
      onError: (message) => {
        setMessages((prev) => [
          ...prev,
          { id: `error-${Date.now()}`, role: 'ASSISTANT', content: message, created_at: new Date().toISOString() },
        ])
        setStreamingText('')
        setSending(false)
      },
    })
  }

  function handleSend(e) {
    e.preventDefault()
    submitQuestion(input)
  }

  function autoGrow(e) {
    const el = e.target
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 160) + 'px'
  }


  async function openSource(source) {
    try {
      const url = await documentApi.fetchFileObjectUrl(source.document_id)
      const pageUrl = source.page_number ? `${url}#page=${source.page_number}` : url
      window.open(pageUrl, '_blank')
    } catch (err) {
      alert('Could not open this document.')
    }
  }


  async function handleFeedback(messageId, isHelpful) {
    const previous = feedbackByMessageId[messageId]
    setFeedbackByMessageId((prev) => ({ ...prev, [messageId]: isHelpful }))
    try {
      await chatApi.rateFeedback(messageId, isHelpful)
    } catch {
      setFeedbackByMessageId((prev) => ({ ...prev, [messageId]: previous }))
    }
  }

  return (
    <div className="chat-wrapper">
      <div className="topbar">
        <h1>Chat</h1>
      </div>

      <div className="chat-messages">
        {!loadingConversation && messages.length === 0 && !sending && (
          <div className="chat-empty">
            <div className="empty-icon">
              <Sparkles size={24} />
            </div>
            <p>Ask about attendance, exams, scholarships, hostel rules, or placements</p>
            <p className="helper-text">Every answer is grounded in official college documents with sources cited.</p>
            <div className="suggestion-chips">
              {SUGGESTIONS.map((s) => (
                <button key={s} className="suggestion-chip" onClick={() => submitQuestion(s)}>
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m) => (
          <div key={m.id}>
            <div className={`message-row ${m.role === 'USER' ? 'user' : 'assistant'}`}>
              <div className="message-label">
                {m.role === 'USER' ? <MessageCircle size={12} /> : <Sparkles size={12} />}
                {m.role === 'USER' ? 'You' : 'Assistant'}
              </div>
              <div className="message-bubble">{m.content}</div>
            </div>

            {m.role === 'ASSISTANT' && !String(m.id).startsWith('error-') && (
              <div style={{ display: 'flex', gap: 4, marginTop: 4 }}>
                <button
                  className="icon-btn"
                  style={{ color: feedbackByMessageId[m.id] === true ? 'var(--success)' : undefined }}
                  onClick={() => handleFeedback(m.id, true)}
                  aria-label="Mark as helpful"
                  title="Helpful"
                >
                  <ThumbsUp size={14} />
                </button>
                <button
                  className="icon-btn"
                  style={{ color: feedbackByMessageId[m.id] === false ? 'var(--danger)' : undefined }}
                  onClick={() => handleFeedback(m.id, false)}
                  aria-label="Mark as not helpful"
                  title="Not helpful"
                >
                  <ThumbsDown size={14} />
                </button>
              </div>
            )}

            {sourcesByMessageId[m.id]?.length > 0 && (
              <div className="sources-box" style={{ marginTop: 6 }}>
                <div className="sources-title">
                  <BookOpen size={13} />
                  Sources
                </div>
                                <ul>
                  {sourcesByMessageId[m.id].map((s, i) => (
                    <li key={i}>
                      <button
                        onClick={() => openSource(s)}
                        style={{
                          background: 'none',
                          border: 'none',
                          padding: 0,
                          color: 'var(--primary)',
                          cursor: 'pointer',
                          textDecoration: 'underline',
                          fontSize: 'inherit',
                          fontFamily: 'inherit',
                        }}
                      >
                        {s.document_title}
                        {s.page_number ? ` — Page ${s.page_number}` : ''}
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ))}

        {sending && (
          <div className="message-row assistant">
            <div className="message-label">
              <Sparkles size={12} />
              Assistant
            </div>
            <div className="message-bubble">
              {streamingText || (
                <div className="typing-indicator">
                  <span />
                  <span />
                  <span />
                </div>
              )}
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <form className="chat-input-bar" onSubmit={handleSend}>
        <textarea
          ref={textareaRef}
          placeholder="Ask a question about college documents..."
          value={input}
          onChange={(e) => {
            setInput(e.target.value)
            autoGrow(e)
          }}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              handleSend(e)
            }
          }}
        />
        <button className="btn btn-primary" disabled={sending || !input.trim()} aria-label="Send message">
          {sending ? <span className="spinner" /> : <Send size={18} />}
        </button>
      </form>
    </div>
  )
}