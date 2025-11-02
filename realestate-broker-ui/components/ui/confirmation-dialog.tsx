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
  const confirmVariant = state.variant === "destructive" ? "destructive" : "default"
  const confirmText = state.confirmText ?? "אישור"
  const cancelText = state.cancelText ?? "ביטול"
  const description = state.description?.toString().trim()
  const hasDescription = Boolean(description)

  return (
    <AlertDialog open={state.isOpen} onOpenChange={close}>
      <AlertDialogContent className="sm:max-w-md w-[95vw] mx-auto">
        <AlertDialogHeader>
          <AlertDialogTitle>{state.title}</AlertDialogTitle>
          {hasDescription ? (
            <AlertDialogDescription>{description}</AlertDialogDescription>
          ) : (
            <AlertDialogDescription className="sr-only">
              {confirmVariant === "destructive"
                ? "אשרו את הפעולה כדי להשלים אותה או בטלו לשמירה על הנתונים הקיימים."
                : "אשרו את הפעולה כדי להמשיך או בחרו ביטול כדי להישאר במסך הנוכחי."}
            </AlertDialogDescription>
          )}
        </AlertDialogHeader>
        <AlertDialogFooter className="flex-col sm:flex-row gap-2 sm:gap-0">
          <AlertDialogCancel
            onClick={state.onCancel}
            className="w-full sm:w-auto order-2 sm:order-1"
          >
            {cancelText}
          </AlertDialogCancel>
          <AlertDialogAction
            onClick={state.onConfirm}
            variant={confirmVariant}
            className="w-full sm:w-auto order-1 sm:order-2"
          >
            {confirmText}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
