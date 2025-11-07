/**
 * AgentChat Component
 * 
 * A chat interface for interacting with the AI real estate agent.
 * 
 * @example
 * // Basic usage with defaults
 * <AgentChat />
 * 
 * @example
 * // With custom recommendations
 * <AgentChat 
 *   recommendedQuestions={[
 *     "מה השווי של הנכס?",
 *     "מה ההיסטוריה של העסקאות?"
 *   ]}
 * />
 * 
 * @example
 * // With API-based recommendations
 * <AgentChat 
 *   fetchRecommendationsFromAPI={true}
 *   emptyStatePrompt="שאל כל שאלה"
 * />
 * 
 * To enable API-based recommendations, create an API route at:
 * /api/agent/recommendations that returns: { recommendations: string[] }
 */

"use client"

import * as React from "react"
import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card"
import { MessageCircle, X, Loader2, Trash2, Copy, Check, ThumbsUp, ThumbsDown, Maximize2, Minimize2, Sparkles, ArrowRight } from "lucide-react"
import { cn } from "@/lib/utils"
import { useAuth } from "@/lib/auth-context"

interface Message {
  role: "user" | "assistant"
  content: string
  timestamp: Date
  feedback?: "positive" | "negative" | null
  messageId?: string
  suggestions?: string[]
}

interface Suggestion {
  text: string
  selected?: boolean
}

// Default recommended questions - can be overridden via props or API
// To customize globally, modify this constant
const DEFAULT_RECOMMENDED_QUESTIONS = [
  "מה השווי של הנכס הזה?",
  "מה ההיסטוריה של העסקאות באזור?",
  "איזה סיכונים יש בנכס הזה?"
]

interface AgentChatProps {
  /** Custom recommended questions to show in empty state. If not provided, will use defaults or fetch from API */
  recommendedQuestions?: string[]
  /** Whether to fetch recommendations from API. Defaults to false */
  fetchRecommendationsFromAPI?: boolean
  /** Custom prompt text for empty state */
  emptyStatePrompt?: string
}

// AI Icon Component with Teal Gradient
const AIIcon = ({ className, size = "default" }: { className?: string; size?: "default" | "large" }) => {
  const iconSize = size === "large" ? "w-16 h-16" : "w-10 h-10"
  const sparkleSize = size === "large" ? "w-8 h-8" : "w-5 h-5"
  
  return (
    <div className={cn("relative flex items-center justify-center", className, iconSize)}>
      <div 
        className={cn("relative rounded-full shadow-lg flex items-center justify-center", iconSize)}
        style={{
          background: 'linear-gradient(to bottom right, var(--brand-teal), var(--brand-teal-light), var(--brand-teal-dark))'
        }}
      >
        <Sparkles className={cn("text-white", sparkleSize)} />
        {size === "large" && (
          <Sparkles className="absolute top-1 right-1 w-3 h-3 text-white opacity-60" />
        )}
        <div 
          className="absolute inset-0 rounded-full opacity-75 animate-pulse"
          style={{
            background: 'linear-gradient(to bottom right, var(--brand-teal), var(--brand-teal-light), var(--brand-teal-dark))'
          }}
        />
      </div>
    </div>
  )
}

export function AgentChat({ 
  recommendedQuestions,
  fetchRecommendationsFromAPI = false,
  emptyStatePrompt = "שאל כל שאלה על הנכסים שלך"
}: AgentChatProps = {}) {
  const [isOpen, setIsOpen] = useState(false)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "שלום! אני העוזר החכם שלך. איך אני יכול לעזור לך היום?",
      timestamp: new Date()
    }
  ])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null)
  const [suggestions, setSuggestions] = useState<Suggestion[]>([])
  const [recommendedQuestionsState, setRecommendedQuestionsState] = useState<string[]>(
    recommendedQuestions || DEFAULT_RECOMMENDED_QUESTIONS
  )
  const [isLoadingRecommendations, setIsLoadingRecommendations] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const { user } = useAuth()
  
  // Generate unique ID for each message
  const generateMessageId = () => {
    return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto"
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`
    }
  }, [input])

  // Fetch recommendations from API if enabled
  useEffect(() => {
    const fetchRecommendations = async () => {
      if (!fetchRecommendationsFromAPI || !user || recommendedQuestions) return
      
      setIsLoadingRecommendations(true)
      try {
        const response = await fetch("/api/agent/recommendations", {
          method: "GET",
          headers: {
            "Content-Type": "application/json"
          }
        })
        
        if (response.ok) {
          const data = await response.json()
          if (data.recommendations && Array.isArray(data.recommendations)) {
            setRecommendedQuestionsState(data.recommendations)
          }
        }
      } catch (error) {
        console.error("Failed to fetch recommendations:", error)
        // Fallback to defaults on error
        setRecommendedQuestionsState(DEFAULT_RECOMMENDED_QUESTIONS)
      } finally {
        setIsLoadingRecommendations(false)
      }
    }

    if (isOpen && messages.length === 1) {
      fetchRecommendations()
    }
  }, [isOpen, fetchRecommendationsFromAPI, user, recommendedQuestions])

  // Update recommended questions when prop changes
  useEffect(() => {
    if (recommendedQuestions) {
      setRecommendedQuestionsState(recommendedQuestions)
    }
  }, [recommendedQuestions])

  const handleSend = async () => {
    if (!input.trim() || isLoading || !user) return

    const userMessage: Message = {
      role: "user",
      content: input.trim(),
      timestamp: new Date()
    }

    setMessages((prev) => [...prev, userMessage])
    setInput("")
    setIsLoading(true)

    try {
      // Prepare chat history (exclude the welcome message)
      const chatHistory = messages
        .slice(1) // Skip welcome message
        .map((msg) => ({
          role: msg.role,
          content: msg.content
        }))

      const response = await fetch("/api/agent/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          message: userMessage.content,
          chat_history: chatHistory
        })
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.error || "אירעה שגיאה בעת קבלת התשובה. אנא נסה שוב מאוחר יותר.")
      }

      const data = await response.json()
      const assistantMessage: Message = {
        role: "assistant",
        content: data.response || "מצטער, לא הצלחתי לקבל תשובה.",
        timestamp: new Date(),
        messageId: generateMessageId(),
        feedback: null,
        suggestions: data.suggestions || []
      }

      setMessages((prev) => [...prev, assistantMessage])
      
      // Set suggestions for the new message
      if (data.suggestions && data.suggestions.length > 0) {
        setSuggestions(data.suggestions.map((text: string) => ({ text, selected: false })))
      } else {
        setSuggestions([])
      }
    } catch (error) {
      const errorMessage: Message = {
        role: "assistant",
        content: error instanceof Error ? error.message : "אירעה שגיאה בעת קבלת התשובה. אנא נסה שוב מאוחר יותר.",
        timestamp: new Date(),
        messageId: generateMessageId(),
        feedback: null
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleClearChat = () => {
    setMessages([
      {
        role: "assistant",
        content: "שלום! אני העוזר החכם שלך. איך אני יכול לעזור לך היום?",
        timestamp: new Date()
      }
    ])
  }

  const handleCopyMessage = async (content: string, index: number) => {
    try {
      await navigator.clipboard.writeText(content)
      setCopiedIndex(index)
      setTimeout(() => setCopiedIndex(null), 2000)
    } catch (error) {
      console.error("Failed to copy message:", error)
    }
  }

  const handleFeedback = async (messageIndex: number, feedback: "positive" | "negative") => {
    const message = messages[messageIndex]
    if (!message || message.role !== "assistant" || !message.messageId) return

    // Optimistically update UI
    setMessages((prev) =>
      prev.map((msg, idx) =>
        idx === messageIndex ? { ...msg, feedback } : msg
      )
    )

    try {
      await fetch("/api/agent/feedback", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          message_id: message.messageId,
          feedback,
          message_content: message.content,
          user_message: messageIndex > 0 ? messages[messageIndex - 1]?.content : null
        })
      })
    } catch (error) {
      console.error("Failed to submit feedback:", error)
      // Revert on error
      setMessages((prev) =>
        prev.map((msg, idx) =>
          idx === messageIndex ? { ...msg, feedback: null } : msg
        )
      )
    }
  }

  const handleSuggestionSend = (suggestionText: string) => {
    setInput(suggestionText)
    setTimeout(() => {
      handleSend()
    }, 100)
  }

  if (!user) {
    return null
  }

  return (
    <>
      {/* Floating button */}
      {!isOpen && (
        <Button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 z-50 h-14 w-14 rounded-full shadow-lg hover:shadow-xl transition-all hover:scale-105"
          style={{
            background: 'linear-gradient(to bottom right, var(--brand-teal), var(--brand-teal-dark))'
          }}
          size="icon"
          aria-label="פתח עוזר בינה מלאכותית"
        >
          <MessageCircle className="h-6 w-6 text-white" />
        </Button>
      )}

      {/* Chat window */}
      {isOpen && (
        <div
          className={cn(
            "fixed z-50 flex flex-col shadow-2xl rounded-xl bg-gradient-to-b from-background to-muted/20 overflow-hidden transition-all backdrop-blur-sm",
            isFullscreen
              ? "inset-4 rounded-xl"
              : "bottom-6 right-6 w-[calc(100vw-3rem)] sm:w-96 h-[600px]"
          )}
        >
          <Card className="flex flex-col h-full border-0 shadow-none bg-transparent">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4 pt-4 px-4 bg-background/80 backdrop-blur-sm">
              <div className="flex items-center gap-3">
                <AIIcon />
                <CardTitle className="text-lg font-semibold">עוזר בינה מלאכותית</CardTitle>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setIsFullscreen(!isFullscreen)}
                  className="h-8 w-8"
                  aria-label={isFullscreen ? "צמצם" : "הרחב למסך מלא"}
                  title={isFullscreen ? "צמצם" : "הרחב למסך מלא"}
                >
                  {isFullscreen ? (
                    <Minimize2 className="h-4 w-4" />
                  ) : (
                    <Maximize2 className="h-4 w-4" />
                  )}
                </Button>
                {messages.length > 1 && (
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={handleClearChat}
                    className="h-8 w-8"
                    aria-label="נקה היסטוריית שיחה"
                    title="נקה היסטוריית שיחה"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                )}
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setIsOpen(false)}
                  className="h-8 w-8"
                  aria-label="סגור"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col p-0 overflow-hidden bg-gradient-to-b from-background via-background to-muted/10">
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {/* Empty state with recommendations */}
                {messages.length === 1 && !isLoading && (
                  <div className="flex flex-col items-center justify-center h-full -mt-8">
                    {/* Central AI Icon */}
                    <div className="mb-6">
                      <AIIcon size="large" />
                    </div>
                    
                    {/* Prompt Text */}
                    <p className="text-foreground text-base font-medium mb-6 text-center">
                      {emptyStatePrompt}
                    </p>
                    
                    {/* Recommendation Buttons - Right aligned, stacked vertically */}
                    {isLoadingRecommendations ? (
                      <div className="flex items-center gap-2 text-muted-foreground">
                        <Loader2 className="h-4 w-4 animate-spin" />
                        <span className="text-sm">טוען המלצות...</span>
                      </div>
                    ) : recommendedQuestionsState.length > 0 ? (
                      <div className="w-full max-w-md flex flex-col items-end gap-3 px-4">
                        {recommendedQuestionsState.map((question, idx) => (
                          <button
                            key={idx}
                            onClick={() => handleSuggestionSend(question)}
                            className="w-full max-w-sm px-4 py-3 rounded-lg text-sm font-medium bg-muted text-foreground border border-border hover:bg-muted/80 hover:border-brand-teal/50 transition-all shadow-sm text-right"
                          >
                            {question}
                          </button>
                        ))}
                      </div>
                    ) : null}
                  </div>
                )}
                
                {messages.length > 1 && messages.slice(1).map((message, idx) => {
                  const actualIndex = idx + 1 // Account for skipped welcome message
                  return (
                  <div
                    key={actualIndex}
                    className={cn(
                      "flex items-start gap-2",
                      message.role === "user" ? "justify-end" : "justify-start"
                    )}
                  >
                    {message.role === "assistant" && (
                      <AIIcon className="shrink-0 mt-1" />
                    )}
                    <div
                      className={cn(
                        "max-w-[80%] rounded-xl px-4 py-3 text-sm relative group shadow-sm",
                        message.role === "user"
                          ? "bg-brand-teal text-white rounded-br-sm"
                          : "bg-muted text-foreground border border-border/60 rounded-bl-sm"
                      )}
                    >
                      <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>
                      {message.role === "assistant" && (
                        <div className="flex items-center gap-1 mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleCopyMessage(message.content, actualIndex)}
                            className="h-6 w-6 hover:bg-muted"
                            aria-label="העתק הודעה"
                            title="העתק הודעה"
                          >
                            {copiedIndex === actualIndex ? (
                              <Check className="h-3 w-3 text-brand-teal" />
                            ) : (
                              <Copy className="h-3 w-3 text-muted-foreground" />
                            )}
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleFeedback(actualIndex, "positive")}
                            className={cn(
                              "h-6 w-6 hover:bg-muted",
                              message.feedback === "positive" && "bg-success text-success-foreground"
                            )}
                            aria-label="תגובה חיובית"
                            title="תגובה חיובית"
                          >
                            <ThumbsUp className={cn(
                              "h-3 w-3",
                              message.feedback === "positive" ? "text-teal-600 fill-teal-600" : "text-muted-foreground"
                            )} />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleFeedback(actualIndex, "negative")}
                            className={cn(
                              "h-6 w-6 hover:bg-muted",
                              message.feedback === "negative" && "bg-red-100 dark:bg-red-900"
                            )}
                            aria-label="תגובה שלילית"
                            title="תגובה שלילית"
                          >
                            <ThumbsDown className={cn(
                              "h-3 w-3",
                              message.feedback === "negative" ? "text-red-600 fill-red-600" : "text-muted-foreground"
                            )} />
                          </Button>
                        </div>
                      )}
                    </div>
                  </div>
                  )
                })}
                
                {/* Suggestions after AI response */}
                {suggestions.length > 0 && messages.length > 1 && (
                  <div className="flex flex-col items-end gap-3 px-2">
                    {suggestions.map((suggestion, idx) => (
                      <button
                        key={idx}
                        onClick={() => handleSuggestionSend(suggestion.text)}
                        className={cn(
                          "w-full max-w-sm px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 text-right shadow-sm",
                          suggestion.selected
                            ? "text-white shadow-md"
                            : "bg-muted text-foreground border border-border hover:bg-muted/80 hover:border-brand-teal/50"
                        )}
                        style={suggestion.selected ? {
                          background: 'linear-gradient(to bottom right, var(--brand-teal), var(--brand-teal-light), var(--brand-teal-dark))'
                        } : undefined}
                      >
                        {suggestion.text}
                      </button>
                    ))}
                  </div>
                )}

                {isLoading && (
                  <div className="flex items-start gap-2 justify-start">
                    <AIIcon className="shrink-0 mt-1" />
                    <div className="bg-muted border border-border/60 rounded-xl rounded-bl-sm px-4 py-3 shadow-sm">
                      <div className="flex items-center gap-2 text-muted-foreground">
                        <Loader2 className="h-4 w-4 animate-spin" />
                        <span className="text-sm">מנתח נתונים, אנא המתן...</span>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
              <div className="border-t bg-background/80 backdrop-blur-sm p-4">
                
                <div className="flex gap-2 items-end">
                  <div className="flex-1 relative">
                    <Textarea
                      ref={textareaRef}
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      onKeyDown={handleKeyDown}
                      placeholder="שאל, כתוב או חפש משהו..."
                      className="min-h-[44px] max-h-[120px] resize-none rounded-xl border-border bg-background pr-12"
                      dir="rtl"
                      disabled={isLoading}
                    />
                  </div>
                  <Button
                    onClick={handleSend}
                    disabled={!input.trim() || isLoading}
                    size="icon"
                    className="h-[44px] w-[44px] shrink-0 rounded-full shadow-md hover:shadow-lg transition-all disabled:opacity-50"
                    style={{
                      background: 'linear-gradient(to bottom right, var(--brand-teal), var(--brand-teal-dark))'
                    }}
                    aria-label="שלח"
                  >
                    {isLoading ? (
                      <Loader2 className="h-4 w-4 animate-spin text-white" />
                    ) : (
                      <ArrowRight className="h-4 w-4 text-white" />
                    )}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </>
  )
}

