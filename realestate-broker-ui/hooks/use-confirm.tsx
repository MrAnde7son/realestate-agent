"use client"

import { useState, useCallback, createContext, useContext } from "react"

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

export function ConfirmProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<ConfirmState>({
    isOpen: false,
    title: "",
    description: "",
    confirmText: "אישור",
    cancelText: "ביטול",
    variant: "default",
  })

  const confirm = useCallback((options: ConfirmOptions): Promise<boolean> => {
    return new Promise((resolve) => {
      setState({
        ...options,
        isOpen: true,
        onConfirm: () => {
          setState(prev => ({ ...prev, isOpen: false }))
          resolve(true)
        },
        onCancel: () => {
          setState(prev => ({ ...prev, isOpen: false }))
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
