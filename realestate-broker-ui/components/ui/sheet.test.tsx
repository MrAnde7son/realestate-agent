/**
 * @vitest-environment jsdom
 */

import { render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";

import { Sheet, SheetContent } from "@/components/ui/sheet";

const renderSheet = (side?: "left" | "right") => {
  render(
    <div dir="rtl">
      <Sheet open>
        <SheetContent side={side} data-testid={`sheet-${side ?? "default"}`}>
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
  });

  it("keeps left-sided sheet anchored to the viewport's left edge in RTL", async () => {
    renderSheet("left");

    const sheet = await waitFor(() => screen.getByTestId("sheet-left"));
    expect(sheet).toHaveClass("left-0");
    expect(sheet).toHaveClass("rtl:left-0");
    expect(sheet).toHaveClass("rtl:right-auto");
    expect(sheet).not.toHaveClass("start-0");
  });
});
