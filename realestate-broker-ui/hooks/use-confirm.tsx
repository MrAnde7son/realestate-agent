"use client"

import React, { useState, useCallback, createContext, useContext } from "react"

const DEFAULT_CONFIRM_TEXT = "אישור"
const DEFAULT_CANCEL_TEXT = "ביטול"

interface ConfirmOptions {
  title: string
  description?: string
  confirmText?: string
  cancelText?: string
  variant?: "default" | "destructive"
}

interface ConfirmState extends ConfirmOptions {
  isOpen: boolean
  onConfirm?: () => void
  onCancel?: () => void
}

interface ConfirmContextType {
  confirm: (options: ConfirmOptions) => Promise<boolean>
  close: () => void
  state: ConfirmState
}

const ConfirmContext = createContext<ConfirmContextType | undefined>(undefined)

const INITIAL_STATE: ConfirmState = {
  isOpen: false,
  title: "",
  description: "",
  confirmText: DEFAULT_CONFIRM_TEXT,
  cancelText: DEFAULT_CANCEL_TEXT,
  variant: "default",
}

export function ConfirmProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<ConfirmState>(INITIAL_STATE)

  const confirm = useCallback((options: ConfirmOptions): Promise<boolean> => {
    return new Promise((resolve) => {
      setState({
        ...INITIAL_STATE,
        ...options,
        confirmText: options.confirmText ?? DEFAULT_CONFIRM_TEXT,
        cancelText: options.cancelText ?? DEFAULT_CANCEL_TEXT,
        variant: options.variant ?? "default",
        isOpen: true,
        onConfirm: () => {
          setState(current => ({ ...current, isOpen: false }))
          resolve(true)
        },
        onCancel: () => {
          setState(current => ({ ...current, isOpen: false }))
          resolve(false)
        },
      })
    })
  }, [])

  const close = useCallback(() => {
    setState(prev => ({ ...prev, isOpen: false }))
  }, [])

  return (
    <ConfirmContext.Provider value={{ confirm, close, state }}>
      {children}
    </ConfirmContext.Provider>
  )
}

export function useConfirm() {
  const context = useContext(ConfirmContext)
  if (context === undefined) {
    throw new Error('useConfirm must be used within a ConfirmProvider')
  }
  return context
}
