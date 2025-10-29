import { render, screen } from "@testing-library/react";
import DocumentCategory from "@/components/DocumentCategory";
import { afterAll, afterEach, beforeAll, vi } from "vitest";

describe("DocumentCategory accessibility", () => {
  const originalOpen = window.open;
  let mockedOpen: ReturnType<typeof vi.fn>;

  beforeAll(() => {
    mockedOpen = vi.fn();
    window.open = mockedOpen as unknown as typeof window.open;
  });

  afterEach(() => {
    mockedOpen.mockClear();
  });

  afterAll(() => {
    window.open = originalOpen;
  });

  it("labels download and external link buttons", () => {
    render(
      <DocumentCategory
        category="מסמכים"
        documents={[
          {
            id: 1,
            title: "נסח טאבו",
            description: "תיאור",
            document_type: "tabu",
            status: "approved",
            filename: "tabu.pdf",
            file_url: "https://example.com/tabu.pdf",
            external_url: "https://example.com",
            external_id: "EXT-1",
            source: "user_upload",
            document_date: new Date().toISOString(),
            uploaded_at: new Date().toISOString(),
            uploaded_by: "בדיקה",
            is_downloadable: true,
          },
        ]}
      />
    );

    expect(screen.getByLabelText("הורד מסמך")).toBeInTheDocument();
    expect(screen.getByLabelText("פתח מסמך בחלון חדש")).toBeInTheDocument();
  });
});
