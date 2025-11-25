import { fireEvent, render, screen } from "@testing-library/react";
import ImageGallery from "@/components/ImageGallery";

describe("ImageGallery accessibility", () => {
  it("exposes aria labels for fullscreen controls", async () => {
    render(
      <ImageGallery images={["/one.jpg", "/two.jpg", "/three.jpg"]} />
    );

    fireEvent.click(screen.getByAltText("תמונה 1"));

    expect(
      await screen.findByLabelText("סגור תצוגת תמונות")
    ).toBeInTheDocument();
    expect(screen.queryByLabelText(/Close/i)).not.toBeInTheDocument();
    expect(
      screen.getByLabelText("הצג תמונה קודמת")
    ).toBeInTheDocument();
    expect(screen.getByLabelText("הצג תמונה הבאה")).toBeInTheDocument();
  });
});
