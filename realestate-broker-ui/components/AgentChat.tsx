
"use client"

import * as React from "react"
import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card"
import { MessageCircle, X, Loader2, Trash2, Copy, Check, ThumbsUp, ThumbsDown, Maximize2, Minimize2, Sparkles, ArrowRight, Edit, RotateCw, FileText, AlertCircle } from "lucide-react"
import { cn } from "@/lib/utils"
import { useAuth } from "@/lib/auth-context"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import type { Components } from "react-markdown"

interface ToolCall {
  tool: string
  tool_hebrew: string
  input: string
  status: "running" | "completed" | "error"
  output?: string
}

interface Message {
  role: "user" | "assistant"
  content: string
  timestamp: Date
  feedback?: "positive" | "negative" | null
  messageId?: string
  suggestions?: string[]
  tool_calls?: ToolCall[]
  sources?: Array<{ title: string; url?: string; description?: string }>
  isError?: boolean
}

interface Suggestion {
  text: string
  selected?: boolean
}

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

// Code Block Component with Copy Button
const CodeBlock = ({ 
  children, 
  className 
}: { 
  children?: React.ReactNode
  className?: string 
}) => {
  const [copied, setCopied] = useState(false)
  const codeRef = useRef<HTMLPreElement>(null)

  const handleCopy = async () => {
    if (!codeRef.current) return
    
    const codeText = codeRef.current.textContent || ""
    try {
      await navigator.clipboard.writeText(codeText)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (error) {
      console.error("Failed to copy code:", error)
    }
  }

  const match = /language-(\w+)/.exec(className || "")
  const language = match ? match[1] : ""

  return (
    <div className="relative group my-4">
      <div className="flex items-center justify-between px-4 py-2 bg-muted/50 border-b border-border rounded-t-lg">
        {language && (
          <span className="text-xs text-muted-foreground font-mono">{language}</span>
        )}
        <Button
          variant="ghost"
          size="icon"
          onClick={handleCopy}
          className="h-6 w-6 ml-auto"
          aria-label="העתק קוד"
        >
          {copied ? (
            <Check className="h-3 w-3 text-green-600" />
          ) : (
            <Copy className="h-3 w-3 text-muted-foreground" />
          )}
        </Button>
      </div>
      <pre
        ref={codeRef}
        className={cn(
          "overflow-x-auto p-4 bg-muted rounded-b-lg text-sm font-mono",
          className
        )}
      >
        <code className={className}>{children}</code>
      </pre>
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
  const [currentToolCalls, setCurrentToolCalls] = useState<ToolCall[]>([])
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null)
  const [suggestions, setSuggestions] = useState<Suggestion[]>([])
  const [recommendedQuestionsState, setRecommendedQuestionsState] = useState<string[]>(
    recommendedQuestions ?? []
  )
  const [isLoadingRecommendations, setIsLoadingRecommendations] = useState(false)
  const [lastAssistantText, setLastAssistantText] = useState("")
  const [editingMessageIndex, setEditingMessageIndex] = useState<number | null>(null)
  const [editingContent, setEditingContent] = useState("")
  const [showSources, setShowSources] = useState<{ [key: number]: boolean }>({})
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const fabRef = useRef<HTMLButtonElement>(null)
  const { user } = useAuth()
  
  // Markdown components configuration
  const markdownComponents: Components = {
    code: ({ className, children, ...props }) => {
      const isInline = !className || !className.includes("language-")
      if (isInline) {
        return (
          <code className="px-1.5 py-0.5 bg-muted/70 rounded text-sm font-mono" {...props}>
            {children}
          </code>
        )
      }
      return (
        <CodeBlock className={className} {...props}>
          {children}
        </CodeBlock>
      )
    },
    pre: ({ children }) => {
      return <>{children}</>
    },
    p: ({ children }) => {
      return <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>
    },
    ul: ({ children }) => {
      return <ul className="list-disc list-inside mb-2 space-y-1 mr-4">{children}</ul>
    },
    ol: ({ children }) => {
      return <ol className="list-decimal list-inside mb-2 space-y-1 mr-4">{children}</ol>
    },
    li: ({ children }) => {
      return <li className="leading-relaxed">{children}</li>
    },
    a: ({ href, children }) => {
      return (
        <a
          href={href}
          target="_blank"
          rel="noopener noreferrer"
          className="text-brand-teal hover:underline"
        >
          {children}
        </a>
      )
    },
    h1: ({ children }) => {
      return <h1 className="text-xl font-bold mb-2 mt-4 first:mt-0">{children}</h1>
    },
    h2: ({ children }) => {
      return <h2 className="text-lg font-semibold mb-2 mt-3 first:mt-0">{children}</h2>
    },
    h3: ({ children }) => {
      return <h3 className="text-base font-semibold mb-2 mt-2 first:mt-0">{children}</h3>
    },
    blockquote: ({ children }) => {
      return (
        <blockquote className="border-r-4 border-brand-teal/50 pr-4 py-2 my-2 bg-muted/30 italic">
          {children}
        </blockquote>
      )
    },
    hr: () => {
      return <hr className="my-4 border-border" />
    },
    table: ({ children }) => {
      return (
        <div className="overflow-x-auto my-4">
          <table className="min-w-full border-collapse border border-border">
            {children}
          </table>
        </div>
      )
    },
    thead: ({ children }) => {
      return <thead className="bg-muted">{children}</thead>
    },
    tbody: ({ children }) => {
      return <tbody>{children}</tbody>
    },
    tr: ({ children }) => {
      return <tr className="border-b border-border">{children}</tr>
    },
    th: ({ children }) => {
      return <th className="border border-border px-4 py-2 text-right font-semibold">{children}</th>
    },
    td: ({ children }) => {
      return <td className="border border-border px-4 py-2 text-right">{children}</td>
    },
  }
  
  // Generate unique ID for each message
  const generateMessageId = () => {
    return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  // Format timestamp for display
  const formatTimestamp = (date: Date) => {
    const now = new Date()
    const messageDate = new Date(date)
    const diffInSeconds = Math.floor((now.getTime() - messageDate.getTime()) / 1000)
    
    // If less than a minute ago
    if (diffInSeconds < 60) {
      return "עכשיו"
    }
    
    // If less than an hour ago
    if (diffInSeconds < 3600) {
      const minutes = Math.floor(diffInSeconds / 60)
      return `לפני ${minutes} דקות`
    }
    
    // If today
    if (now.toDateString() === messageDate.toDateString()) {
      return messageDate.toLocaleTimeString("he-IL", {
        hour: "2-digit",
        minute: "2-digit"
      })
    }
    
    // If yesterday
    const yesterday = new Date(now)
    yesterday.setDate(yesterday.getDate() - 1)
    if (yesterday.toDateString() === messageDate.toDateString()) {
      return `אתמול ${messageDate.toLocaleTimeString("he-IL", {
        hour: "2-digit",
        minute: "2-digit"
      })}`
    }
    
    // Otherwise, show full date and time
    return messageDate.toLocaleString("he-IL", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    })
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

  // Focus management: focus textarea when opening chat
  useEffect(() => {
    if (isOpen) {
      requestAnimationFrame(() => {
        textareaRef.current?.focus()
      })
    }
  }, [isOpen])

  // Focus management: return focus to FAB when closing chat
  useEffect(() => {
    if (!isOpen && fabRef.current) {
      requestAnimationFrame(() => {
        fabRef.current?.focus()
      })
    }
  }, [isOpen])

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
          console.log("Recommendations API response:", data)
          if (data.recommendations && Array.isArray(data.recommendations)) {
            console.log("Setting recommendations from API:", data.recommendations)
            setRecommendedQuestionsState(data.recommendations)
          } else {
            console.warn("Recommendations API returned invalid data format:", data)
          }
        } else {
          // Response not OK - log the error (API should always return 200, so this is unexpected)
          const errorText = await response.text()
          console.error(`Recommendations API returned ${response.status}:`, errorText)
        }
      } catch (error) {
        console.error("Failed to fetch recommendations:", error)
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
    setCurrentToolCalls([]) // Reset tool calls for new request

    // Prepare chat history (exclude the welcome message)
    const chatHistory = messages
      .slice(1) // Skip welcome message
      .map((msg) => ({
        role: msg.role,
        content: msg.content
      }))

    // Create assistant message placeholder that will be updated as we stream
    const assistantMessageId = generateMessageId()
    const assistantMessage: Message = {
      role: "assistant",
      content: "",
      timestamp: new Date(),
      messageId: assistantMessageId,
      feedback: null,
      suggestions: [],
      tool_calls: [],
      sources: []
    }

    setMessages((prev) => [...prev, assistantMessage])
    setLastAssistantText("")

    try {
      // Use fetch with ReadableStream for SSE streaming (EventSource doesn't support POST)
      const response = await fetch("/api/agent/chat/stream", {
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

      if (!response.body) {
        throw new Error("No response body")
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ""
      let accumulatedContent = ""
      let finalToolCalls: any[] = []
      let finalSuggestions: string[] = []

      while (true) {
        const { done, value } = await reader.read()
        
        if (done) {
          break
        }

        // Decode chunk and add to buffer
        buffer += decoder.decode(value, { stream: true })
        
        // Process complete SSE messages (format: "data: {...}\n\n")
        // Split by double newline to get complete messages
        const messages = buffer.split("\n\n")
        buffer = messages.pop() || "" // Keep incomplete message in buffer

        for (const message of messages) {
          const lines = message.split("\n")
          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const jsonStr = line.slice(6) // Remove "data: " prefix
                const data = JSON.parse(jsonStr)
              
              switch (data.type) {
                case 'chunk':
                  // Append chunk to accumulated content
                  accumulatedContent += data.content || ""
                  setLastAssistantText(accumulatedContent)
                  // Update the assistant message in place
                  setMessages((prev) => prev.map((msg) => 
                    msg.messageId === assistantMessageId
                      ? { ...msg, content: accumulatedContent }
                      : msg
                  ))
                  break
                  
                case 'tool_call_start':
                  // Add tool call to current tool calls
                  console.log('Tool call start:', data.tool, data.tool_hebrew)
                  setCurrentToolCalls((prev) => {
                    const updated: ToolCall[] = [...prev, {
                      tool: data.tool,
                      tool_hebrew: data.tool_hebrew || data.tool,
                      status: "running" as const,
                      input: data.input
                    }]
                    console.log('Updated tool calls:', updated)
                    return updated
                  })
                  break
                  
                case 'tool_call_end':
                  // Update tool call status
                  setCurrentToolCalls((prev) => prev.map((tc) => 
                    tc.tool === data.tool
                      ? { ...tc, status: "completed", output: data.output }
                      : tc
                  ))
                  break
                  
                case 'tool_call_error':
                  // Update tool call with error
                  console.log('Tool call error received:', data.tool, data.error)
                  setCurrentToolCalls((prev) => prev.map((tc) => 
                    tc.tool === data.tool
                      ? { ...tc, status: "error", output: data.error }
                      : tc
                  ))
                  break
                  
                case 'complete':
                  // Final response received
                  accumulatedContent = data.response || accumulatedContent
                  finalToolCalls = data.tool_calls || []
                  
                  console.log('Complete event received:', {
                    responseLength: accumulatedContent.length,
                    toolCallsCount: finalToolCalls.length,
                    toolCalls: finalToolCalls,
                    toolCallsWithStatus: finalToolCalls.map((tc: any) => ({ tool: tc.tool, status: tc.status }))
                  })
                  
                  // Update final message
                  setMessages((prev) => prev.map((msg) => 
                    msg.messageId === assistantMessageId
                      ? { 
                          ...msg, 
                          content: accumulatedContent,
                          tool_calls: finalToolCalls,
                          suggestions: finalSuggestions
                        }
                      : msg
                  ))
                  setLastAssistantText(accumulatedContent)
                  
                  // Update tool calls state - ensure format matches what we expect
                  // Preserve error status - don't default to "completed" if status exists
                  const formattedToolCalls = finalToolCalls.map((tc: any) => ({
                    tool: tc.tool || tc.name,
                    tool_hebrew: tc.tool_hebrew || tc.tool || tc.name,
                    status: tc.status || "completed", // Only default if status is truly missing
                    input: tc.input,
                    output: tc.output
                  }))
                  setCurrentToolCalls(formattedToolCalls)
                  console.log('Formatted tool calls:', formattedToolCalls)
                  
                  // Set suggestions if available
                  if (finalSuggestions.length > 0) {
                    setSuggestions(finalSuggestions.map((text: string) => ({ text, selected: false })))
                  } else {
                    setSuggestions([])
                  }
                  
                  setIsLoading(false)
                  break
                  
                case 'error':
                  // Error occurred
                  const errorContent = data.error || "אירעה שגיאה בעת קבלת התשובה. אנא נסה שוב מאוחר יותר."
                  setMessages((prev) => prev.map((msg) => 
                    msg.messageId === assistantMessageId
                      ? { ...msg, content: errorContent, isError: true }
                      : msg
                  ))
                  setLastAssistantText(errorContent)
                  setIsLoading(false)
                  setCurrentToolCalls([]) // Clear tool calls on error
                  break
              }
            } catch (error) {
              console.error("Error parsing SSE event:", error)
            }
            }
          }
        }
      }

    } catch (error) {
      const errorMessage: Message = {
        role: "assistant",
        content: error instanceof Error ? error.message : "אירעה שגיאה בעת קבלת התשובה. אנא נסה שוב מאוחר יותר.",
        timestamp: new Date(),
        messageId: generateMessageId(),
        feedback: null,
        isError: true
      }
      setMessages((prev) => [...prev, errorMessage])
      setLastAssistantText(error instanceof Error ? error.message : "אירעה שגיאה בעת קבלת התשובה. אנא נסה שוב מאוחר יותר.")
      setIsLoading(false)
      setCurrentToolCalls([])
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

  const handleEditMessage = (messageIndex: number) => {
    const message = messages[messageIndex]
    if (!message || message.role !== "user") return
    
    setEditingMessageIndex(messageIndex)
    setEditingContent(message.content)
  }

  const handleCancelEdit = () => {
    setEditingMessageIndex(null)
    setEditingContent("")
  }

  const handleSaveEdit = async () => {
    if (!editingContent.trim() || editingMessageIndex === null || isLoading || !user) return
    
    const messageIndex = editingMessageIndex
    const editedContent = editingContent.trim()
    
    // Update the message content
    setMessages((prev) => {
      const updated = prev.map((msg, idx) =>
        idx === messageIndex ? { ...msg, content: editedContent } : msg
      )
      
      // Remove the assistant response that followed this user message (if exists)
      const nextMessageIndex = messageIndex + 1
      if (nextMessageIndex < updated.length && updated[nextMessageIndex].role === "assistant") {
        return updated.filter((_, idx) => idx !== nextMessageIndex)
      }
      return updated
    })
    
    // Reset editing state immediately
    setEditingMessageIndex(null)
    setEditingContent("")
    
    // Prepare updated chat history for API call
    setMessages((prev) => {
      const updatedMessages = prev.map((msg, idx) =>
        idx === messageIndex ? { ...msg, content: editedContent } : msg
      )
      const nextMessageIndex = messageIndex + 1
      const finalMessages = nextMessageIndex < updatedMessages.length && updatedMessages[nextMessageIndex].role === "assistant"
        ? updatedMessages.filter((_, idx) => idx !== nextMessageIndex)
        : updatedMessages
      
      // Send the request with updated chat history
      setIsLoading(true)
      setCurrentToolCalls([])
      
      const chatHistory = finalMessages
        .slice(1) // Skip welcome message
        .map((msg) => ({
          role: msg.role,
          content: msg.content
        }))
      
      fetch("/api/agent/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          message: editedContent,
          chat_history: chatHistory
        })
      })
        .then(async (response) => {
          if (!response.ok) {
            const errorData = await response.json().catch(() => ({}))
            throw new Error(errorData.error || "אירעה שגיאה בעת קבלת התשובה. אנא נסה שוב מאוחר יותר.")
          }
          return response.json()
        })
        .then((data) => {
          // Update tool calls state to show completed status
          if (data.tool_calls && data.tool_calls.length > 0) {
            setCurrentToolCalls(data.tool_calls)
          }
          
          const assistantMessage: Message = {
            role: "assistant",
            content: data.response || "מצטער, לא הצלחתי לקבל תשובה.",
            timestamp: new Date(),
            messageId: generateMessageId(),
            feedback: null,
            suggestions: data.suggestions || [],
            tool_calls: data.tool_calls || [],
            sources: data.sources || []
          }
          
          setMessages((prev) => [...prev, assistantMessage])
          setLastAssistantText(data.response || "מצטער, לא הצלחתי לקבל תשובה.")
          
          // Set suggestions for the new message
          if (data.suggestions && data.suggestions.length > 0) {
            setSuggestions(data.suggestions.map((text: string) => ({ text, selected: false })))
          } else {
            setSuggestions([])
          }
        })
        .catch((error) => {
          const errorMessage: Message = {
            role: "assistant",
            content: error instanceof Error ? error.message : "אירעה שגיאה בעת קבלת התשובה. אנא נסה שוב מאוחר יותר.",
            timestamp: new Date(),
            messageId: generateMessageId(),
            feedback: null,
            isError: true
          }
          setMessages((prev) => [...prev, errorMessage])
          setLastAssistantText(error instanceof Error ? error.message : "אירעה שגיאה בעת קבלת התשובה. אנא נסה שוב מאוחר יותר.")
        })
        .finally(() => {
          setIsLoading(false)
          setCurrentToolCalls([])
        })
      
      return finalMessages
    })
  }

  const handleRegenerate = async (assistantMessageIndex: number) => {
    if (isLoading || !user) return
    
    // Find the user message that precedes this assistant message
    let userMessageIndex = assistantMessageIndex - 1
    while (userMessageIndex >= 0 && messages[userMessageIndex].role !== "user") {
      userMessageIndex--
    }
    
    if (userMessageIndex < 0) return
    
    const userMessage = messages[userMessageIndex]
    
    // Remove the assistant response
    const updatedMessages = messages.filter((_, idx) => idx !== assistantMessageIndex)
    setMessages(updatedMessages)
    
    // Send the request immediately
    setIsLoading(true)
    setCurrentToolCalls([])
    
    const chatHistory = updatedMessages
      .slice(1) // Skip welcome message
      .map((msg) => ({
        role: msg.role,
        content: msg.content
      }))
    
    try {
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
      
      // Update tool calls state to show completed status
      if (data.tool_calls && data.tool_calls.length > 0) {
        setCurrentToolCalls(data.tool_calls)
      }
      
      const assistantMessage: Message = {
        role: "assistant",
        content: data.response || "מצטער, לא הצלחתי לקבל תשובה.",
        timestamp: new Date(),
        messageId: generateMessageId(),
        feedback: null,
        suggestions: data.suggestions || [],
        tool_calls: data.tool_calls || [],
        sources: data.sources || []
      }

      setMessages((prev) => [...prev, assistantMessage])
      setLastAssistantText(data.response || "מצטער, לא הצלחתי לקבל תשובה.")
      
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
        feedback: null,
        isError: true
      }
      setMessages((prev) => [...prev, errorMessage])
      setLastAssistantText(error instanceof Error ? error.message : "אירעה שגיאה בעת קבלת התשובה. אנא נסה שוב מאוחר יותר.")
    } finally {
      setIsLoading(false)
      setCurrentToolCalls([])
    }
  }

  const toggleSources = (messageIndex: number) => {
    setShowSources((prev) => ({
      ...prev,
      [messageIndex]: !prev[messageIndex]
    }))
  }

  return (
    <>
      {/* Floating button */}
      {!isOpen && (
        <Button
          ref={fabRef}
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
          {/* ARIA live region for screen readers */}
          <div aria-live="polite" className="sr-only">{lastAssistantText}</div>
          <Card className="flex flex-col h-full border-0 shadow-none bg-transparent">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4 pt-4 px-4 bg-background/80 backdrop-blur-sm">
              <div className="flex flex-col gap-1">
                <div className="flex items-center gap-3">
                  <AIIcon />
                  <CardTitle className="text-lg font-semibold">עוזר בינה מלאכותית</CardTitle>
                </div>
                <p className="text-xs text-muted-foreground mr-12">
                  העוזר עלול לטעות - אנא בדקו את המידע
                </p>
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
                    key={message.messageId || `msg-${actualIndex}`}
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
                          : message.isError
                          ? "bg-red-50 dark:bg-red-950/20 text-red-900 dark:text-red-200 border-2 border-red-500 rounded-bl-sm"
                          : "bg-muted text-foreground border border-border/60 rounded-bl-sm"
                      )}
                    >
                      {/* Editing UI for user messages */}
                      {message.role === "user" && editingMessageIndex === actualIndex ? (
                        <div className="space-y-2">
                          <Textarea
                            value={editingContent}
                            onChange={(e) => setEditingContent(e.target.value)}
                            className={cn(
                              "min-h-[60px] resize-none text-sm bg-white/10 border-white/20 text-white placeholder:text-white/60",
                              "focus:bg-white/15 focus:border-white/30"
                            )}
                            dir="rtl"
                            placeholder="ערוך את ההודעה..."
                            onKeyDown={(e) => {
                              if (e.key === "Enter" && !e.shiftKey) {
                                e.preventDefault()
                                handleSaveEdit()
                              }
                              if (e.key === "Escape") {
                                handleCancelEdit()
                              }
                            }}
                            autoFocus
                          />
                          <div className="flex items-center gap-2 justify-end">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={handleCancelEdit}
                              className="h-7 text-xs text-white/80 hover:text-white hover:bg-white/20"
                            >
                              ביטול
                            </Button>
                            <Button
                              size="sm"
                              onClick={handleSaveEdit}
                              disabled={!editingContent.trim()}
                              className="h-7 text-xs bg-white/20 hover:bg-white/30 text-white disabled:opacity-50"
                            >
                              שמור ושלח
                            </Button>
                          </div>
                        </div>
                      ) : (
                        <>
                          {message.role === "assistant" ? (
                            <>
                              {/* Error indicator */}
                              {message.isError && (
                                <div className="mb-3 flex items-center gap-2 text-sm text-red-600 dark:text-red-400 font-medium">
                                  <AlertCircle className="h-4 w-4 shrink-0" />
                                  <span>שגיאה</span>
                                </div>
                              )}
                              
                              {/* Loading indicator for streaming response */}
                              {isLoading && actualIndex === messages.length - 1 && !message.isError && (
                                <div className="mb-3 flex items-center gap-2 text-sm text-muted-foreground">
                                  <Loader2 className="h-4 w-4 animate-spin text-brand-teal shrink-0" />
                                  <span>מכין תשובה...</span>
                                </div>
                              )}
                              
                              {/* Show tool calls - check both currentToolCalls (for streaming) and message.tool_calls (for completed) */}
                              {(() => {
                                const toolCallsToShow = actualIndex === messages.length - 1 && currentToolCalls.length > 0
                                  ? currentToolCalls
                                  : (message.tool_calls || [])
                                return toolCallsToShow.length > 0 && !message.isError && (
                                  <div className="mb-3 pb-3">
                                    <p className="text-xs font-medium text-muted-foreground mb-2">מבצע פעולות:</p>
                                    <div className="space-y-1.5">
                                      {toolCallsToShow.map((toolCall, idx) => (
                                        <div key={`${toolCall.tool || idx}-${idx}`} className="flex items-center gap-2 text-xs">
                                          {toolCall.status === "running" ? (
                                            <Loader2 className="h-3 w-3 animate-spin text-brand-teal shrink-0" />
                                          ) : toolCall.status === "error" ? (
                                            <X className="h-3 w-3 text-red-600 shrink-0" />
                                          ) : toolCall.status === "completed" ? (
                                            <Check className="h-3 w-3 text-green-600 shrink-0" />
                                          ) : (
                                            <Loader2 className="h-3 w-3 animate-spin text-muted-foreground shrink-0" />
                                          )}
                                          <span className={cn(
                                            "text-muted-foreground",
                                            toolCall.status === "running" && "text-brand-teal font-medium",
                                            toolCall.status === "completed" && "text-green-600",
                                            toolCall.status === "error" && "text-red-600"
                                          )}>
                                            {toolCall.tool_hebrew || toolCall.tool}
                                          </span>
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                )
                              })()}
                              
                              <div className="markdown-content">
                                <ReactMarkdown
                                  remarkPlugins={[remarkGfm]}
                                  components={markdownComponents}
                                >
                                  {message.content || (isLoading && actualIndex === messages.length - 1 && currentToolCalls.length === 0 ? "מנתח נתונים, אנא המתן..." : "")}
                                </ReactMarkdown>
                              </div>
                            </>
                          ) : (
                            <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>
                          )}
                          
                          {/* Show sources for assistant messages */}
                          {message.role === "assistant" && message.sources && message.sources.length > 0 && showSources[actualIndex] && (
                            <div className="mt-3 pt-3 border-t border-border/40">
                              <p className="text-xs font-medium text-muted-foreground mb-2">מקורות:</p>
                              <div className="space-y-2">
                                {message.sources.map((source, sourceIdx) => (
                                  <div key={sourceIdx} className="text-xs">
                                    {source.url ? (
                                      <a
                                        href={source.url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-brand-teal hover:underline flex items-center gap-1"
                                      >
                                        <FileText className="h-3 w-3" />
                                        {source.title || source.url}
                                      </a>
                                    ) : (
                                      <div className="text-muted-foreground flex items-center gap-1">
                                        <FileText className="h-3 w-3" />
                                        {source.title}
                                      </div>
                                    )}
                                    {source.description && (
                                      <p className="text-muted-foreground/80 mt-1 mr-4 text-xs">
                                        {source.description}
                                      </p>
                                    )}
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                          
                          {/* Timestamp and Action Buttons */}
                          <div className="flex items-center justify-between mt-2 gap-2">
                            {/* Timestamp */}
                            <div className={cn(
                              "text-xs opacity-70",
                              message.role === "user" ? "text-white/80" : "text-muted-foreground"
                            )}>
                              {formatTimestamp(message.timestamp)}
                            </div>
                            
                            {/* Action Buttons */}
                            <div className="flex items-center gap-1">
                              {message.role === "user" ? (
                                <>
                                  <Button
                                    variant="ghost"
                                    size="icon"
                                    onClick={() => handleEditMessage(actualIndex)}
                                    className="h-6 w-6 hover:bg-white/20 text-white/80 hover:text-white"
                                    aria-label="ערוך ושלח מחדש"
                                    title="ערוך ושלח מחדש"
                                  >
                                    <Edit className="h-3 w-3" />
                                  </Button>
                                </>
                              ) : (
                                <>
                                  <Button
                                    variant="ghost"
                                    size="icon"
                                    onClick={() => handleRegenerate(actualIndex)}
                                    className="h-6 w-6 hover:bg-muted"
                                    aria-label="צור מחדש"
                                    title="צור מחדש"
                                    disabled={isLoading}
                                  >
                                    <RotateCw className="h-3 w-3 text-muted-foreground" />
                                  </Button>
                                  {message.sources && message.sources.length > 0 && (
                                    <Button
                                      variant="ghost"
                                      size="icon"
                                      onClick={() => toggleSources(actualIndex)}
                                      className={cn(
                                        "h-6 w-6 hover:bg-muted",
                                        showSources[actualIndex] && "bg-muted"
                                      )}
                                      aria-label="הצג מקורות"
                                      title="הצג מקורות"
                                    >
                                      <FileText className={cn(
                                        "h-3 w-3",
                                        showSources[actualIndex] ? "text-brand-teal" : "text-muted-foreground"
                                      )} />
                                    </Button>
                                  )}
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
                                </>
                              )}
                            </div>
                          </div>
                        </>
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

