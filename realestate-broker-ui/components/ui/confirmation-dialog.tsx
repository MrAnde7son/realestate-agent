"use client"

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { useConfirm } from "@/hooks/use-confirm"

export function ConfirmationDialog() {
  const { state, close } = useConfirm()

  return (
    <AlertDialog open={state.isOpen} onOpenChange={close}>
      <AlertDialogContent className="sm:max-w-md w-[95vw] mx-auto">
        <AlertDialogHeader>
          <AlertDialogTitle className="text-right">{state.title}</AlertDialogTitle>
          {state.description && (
            <AlertDialogDescription className="text-right">
              {state.description}
            </AlertDialogDescription>
          )}
        </AlertDialogHeader>
        <AlertDialogFooter className="flex-col sm:flex-row gap-2 sm:gap-0">
          <AlertDialogCancel 
            onClick={state.onCancel}
            className="w-full sm:w-auto order-2 sm:order-1"
          >
            {state.cancelText}
          </AlertDialogCancel>
          <AlertDialogAction
            onClick={state.onConfirm}
            className={`w-full sm:w-auto order-1 sm:order-2 ${
              state.variant === "destructive" 
                ? "bg-red-600 hover:bg-red-700 text-white" 
                : "bg-blue-600 hover:bg-blue-700 text-white"
            }`}
          >
            {state.confirmText}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
