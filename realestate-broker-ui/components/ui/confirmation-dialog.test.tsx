import React from 'react'
import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { ConfirmationDialog } from './confirmation-dialog'
import { ConfirmProvider, useConfirm } from '@/hooks/use-confirm'

function TriggerButton({
  title,
  variant,
  description = 'אשרו את הפעולה',
}: {
  title: string
  variant?: 'default' | 'destructive'
  description?: string
}) {
  const { confirm } = useConfirm()

  return (
    <button
      type="button"
      onClick={() => {
        void confirm({ title, variant, description })
      }}
    >
      פתח {title}
    </button>
  )
}

describe('ConfirmationDialog', () => {
  it('renders default copy when confirm options are omitted', async () => {
    render(
      <ConfirmProvider>
        <TriggerButton title="אישור" />
        <ConfirmationDialog />
      </ConfirmProvider>
    )

    fireEvent.click(screen.getByRole('button', { name: /פתח אישור/ }))

    expect(await screen.findByRole('heading', { name: 'אישור' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'אישור' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'ביטול' })).toBeInTheDocument()
  })

  it('applies destructive styling when variant is destructive', async () => {
    render(
      <ConfirmProvider>
        <TriggerButton title="מחיקה" variant="destructive" />
        <ConfirmationDialog />
      </ConfirmProvider>
    )

    fireEvent.click(screen.getByRole('button', { name: /פתח מחיקה/ }))

    const confirmButton = await screen.findByRole('button', { name: 'אישור' })
    expect(confirmButton).toHaveClass('bg-destructive')
  })
})
