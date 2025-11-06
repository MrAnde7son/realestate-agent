"use client"

import * as React from "react"
import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card"
import { MessageCircle, X, Send, Loader2, Trash2, Copy, Check, ThumbsUp, ThumbsDown, Maximize2, Minimize2 } from "lucide-react"
import { cn } from "@/lib/utils"
import { useAuth } from "@/lib/auth-context"

interface Message {
  role: "user" | "assistant"
  content: string
  timestamp: Date
  feedback?: "positive" | "negative" | null
  messageId?: string
}

export function AgentChat() {
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
        throw new Error(errorData.error || "Failed to get response")
      }

      const data = await response.json()
      const assistantMessage: Message = {
        role: "assistant",
        content: data.response || "מצטער, לא הצלחתי לקבל תשובה.",
        timestamp: new Date(),
        messageId: generateMessageId(),
        feedback: null
      }

      setMessages((prev) => [...prev, assistantMessage])
    } catch (error) {
      const errorMessage: Message = {
        role: "assistant",
        content: `שגיאה: ${error instanceof Error ? error.message : "שגיאה לא ידועה"}`,
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

  if (!user) {
    return null
  }

  return (
    <>
      {/* Floating button */}
      {!isOpen && (
        <Button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 z-50 h-14 w-14 rounded-full shadow-lg hover:shadow-xl transition-all"
          size="icon"
          aria-label="פתח עוזר בינה מלאכותית"
        >
          <MessageCircle className="h-6 w-6" />
        </Button>
      )}

      {/* Chat window */}
      {isOpen && (
        <div
          className={cn(
            "fixed z-50 flex flex-col shadow-2xl rounded-lg border bg-background overflow-hidden transition-all",
            isFullscreen
              ? "inset-4 rounded-lg"
              : "bottom-6 right-6 w-[calc(100vw-3rem)] sm:w-96 h-[600px]"
          )}
        >
          <Card className="flex flex-col h-full border-0 shadow-none">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3 border-b">
              <CardTitle className="text-lg font-semibold">עוזר בינה מלאכותית</CardTitle>
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
            <CardContent className="flex-1 flex flex-col p-0 overflow-hidden">
              <div className="flex-1 overflow-y-auto p-4">
                <div className="space-y-4">
                  {messages.map((message, index) => (
                    <div
                      key={index}
                      className={cn(
                        "flex",
                        message.role === "user" ? "justify-end" : "justify-start"
                      )}
                    >
                      <div
                        className={cn(
                          "max-w-[80%] rounded-lg px-4 py-2 text-sm relative group",
                          message.role === "user"
                            ? "bg-primary text-primary-foreground"
                            : "bg-muted text-muted-foreground"
                        )}
                      >
                        <p className="whitespace-pre-wrap">{message.content}</p>
                        {message.role === "assistant" && (
                          <div className="flex items-center gap-1 mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => handleCopyMessage(message.content, index)}
                              className="h-6 w-6"
                              aria-label="העתק הודעה"
                              title="העתק הודעה"
                            >
                              {copiedIndex === index ? (
                                <Check className="h-3 w-3 text-green-600" />
                              ) : (
                                <Copy className="h-3 w-3" />
                              )}
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => handleFeedback(index, "positive")}
                              className={cn(
                                "h-6 w-6",
                                message.feedback === "positive" && "bg-green-100 dark:bg-green-900"
                              )}
                              aria-label="תגובה חיובית"
                              title="תגובה חיובית"
                            >
                              <ThumbsUp className={cn(
                                "h-3 w-3",
                                message.feedback === "positive" && "text-green-600 fill-green-600"
                              )} />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => handleFeedback(index, "negative")}
                              className={cn(
                                "h-6 w-6",
                                message.feedback === "negative" && "bg-red-100 dark:bg-red-900"
                              )}
                              aria-label="תגובה שלילית"
                              title="תגובה שלילית"
                            >
                              <ThumbsDown className={cn(
                                "h-3 w-3",
                                message.feedback === "negative" && "text-red-600 fill-red-600"
                              )} />
                            </Button>
                          </div>
                        )}
                        <p className="text-xs opacity-70 mt-1">
                          {message.timestamp.toLocaleTimeString("he-IL", {
                            hour: "2-digit",
                            minute: "2-digit"
                          })}
                        </p>
                      </div>
                    </div>
                  ))}
                  {isLoading && (
                    <div className="flex justify-start">
                      <div className="bg-muted text-muted-foreground rounded-lg px-4 py-2">
                        <Loader2 className="h-4 w-4 animate-spin" />
                      </div>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </div>
              </div>
              <div className="border-t p-3">
                <div className="flex gap-2">
                  <Textarea
                    ref={textareaRef}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="הקלד הודעה..."
                    className="min-h-[44px] max-h-[120px] resize-none"
                    dir="rtl"
                    disabled={isLoading}
                  />
                  <Button
                    onClick={handleSend}
                    disabled={!input.trim() || isLoading}
                    size="icon"
                    className="h-[44px] w-[44px] shrink-0"
                    aria-label="שלח"
                  >
                    {isLoading ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Send className="h-4 w-4" />
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

