// @vitest-environment jsdom
import React from "react"
import { render, screen } from "@testing-library/react"
import { describe, it, expect } from "vitest"
import { AlertDialog, AlertDialogContent, AlertDialogDescription, AlertDialogTitle } from "./alert-dialog"

describe("AlertDialog", () => {
  it("centers the dialog content on the viewport", () => {
    render(
      <AlertDialog open>
        <AlertDialogContent>
          <AlertDialogTitle>Confirm delete</AlertDialogTitle>
          <AlertDialogDescription>
            Deleting an asset cannot be undone.
          </AlertDialogDescription>
        </AlertDialogContent>
      </AlertDialog>
    )

    const dialog = screen.getByRole("alertdialog")

    expect(dialog.className).toContain("left-1/2")
    expect(dialog.className).toContain("-translate-x-1/2")
  })
})
