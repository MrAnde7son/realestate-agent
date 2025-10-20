/**
 * @vitest-environment jsdom
 */

import { render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";

import type { CSSProperties } from "react";

import { Sheet, SheetContent, SheetDescription, SheetTitle } from "@/components/ui/sheet";

const renderSheet = (side?: "left" | "right", style?: CSSProperties) => {
  render(
    <div dir="rtl">
      <Sheet open>
        <SheetContent
          side={side}
          data-testid={`sheet-${side ?? "default"}`}
          style={style}
        >
          <SheetTitle className="sr-only">כותרת</SheetTitle>
          <SheetDescription className="sr-only">תיאור</SheetDescription>
          תוכן
        </SheetContent>
      </Sheet>
    </div>
  );
};

describe("SheetContent physical positioning", () => {
  it("keeps right-sided sheet anchored to the viewport's right edge in RTL", async () => {
    renderSheet("right");

    const sheet = await waitFor(() => screen.getByTestId("sheet-right"));
    expect(sheet).toHaveClass("right-0");
    expect(sheet).toHaveClass("rtl:right-0");
    expect(sheet).toHaveClass("rtl:left-auto");
    expect(sheet).not.toHaveClass("end-0");
    expect(sheet).toHaveStyle({ right: "0px", left: "auto" });
  });

  it("keeps left-sided sheet anchored to the viewport's left edge in RTL", async () => {
    renderSheet("left");

    const sheet = await waitFor(() => screen.getByTestId("sheet-left"));
    expect(sheet).toHaveClass("left-0");
    expect(sheet).toHaveClass("rtl:left-0");
    expect(sheet).toHaveClass("rtl:right-auto");
    expect(sheet).not.toHaveClass("start-0");
    expect(sheet).toHaveStyle({ left: "0px", right: "auto" });
  });

  it("respects explicit style overrides while keeping the opposite edge auto", async () => {
    renderSheet("right", { right: "1.5rem" });

    const sheet = await waitFor(() => screen.getByTestId("sheet-right"));
    expect(sheet).toHaveStyle({ right: "1.5rem", left: "auto" });
  });
});
