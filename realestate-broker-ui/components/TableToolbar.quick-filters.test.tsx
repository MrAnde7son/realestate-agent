import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, within } from "@testing-library/react";
import TableToolbar from "./TableToolbar";

vi.mock("@/hooks/useAnalytics", () => ({
  useAnalytics: () => ({
    trackFeatureUsage: vi.fn(),
    trackSearch: vi.fn(),
  }),
}));

type FiltersConfig = NonNullable<Parameters<typeof TableToolbar>[0]["filters"]>;

const createFilters = (): FiltersConfig => ({
  city: {
    value: "all",
    onChange: vi.fn(),
    options: ["תל אביב"],
  },
  type: {
    value: "all",
    onChange: vi.fn(),
    options: ["דירה", "בית"],
  },
  priceMin: {
    value: undefined,
    onChange: vi.fn(),
  },
  priceMax: {
    value: undefined,
    onChange: vi.fn(),
  },
  areaMin: {
    value: undefined,
    onChange: vi.fn(),
  },
  areaMax: {
    value: undefined,
    onChange: vi.fn(),
  },
  rentalSale: {
    value: "all",
    onChange: vi.fn(),
    options: [
      { value: "rental", label: "השכרה" },
      { value: "sale", label: "מכירה" },
    ],
  },
  userAssets: {
    value: "all",
    onChange: vi.fn(),
    options: [
      { value: "mine", label: "נכסים שלי" },
      { value: "others", label: "נכסים של אחרים" },
    ],
  },
});

const baseColumns = [
  {
    id: "address",
    header: "Address",
    visible: true,
    toggle: vi.fn(),
  },
];

const renderToolbar = (overrides: Partial<Parameters<typeof TableToolbar>[0]> = {}, filtersOverride?: FiltersConfig) => {
  const filters = filtersOverride ?? createFilters();

  const props: Parameters<typeof TableToolbar>[0] = {
    searchValue: "",
    onSearchChange: vi.fn(),
    filters,
    columns: baseColumns,
    onResetColumns: vi.fn(),
    onExportSelected: vi.fn(),
    onExportAll: vi.fn(),
    selectedCount: 0,
    totalCount: 0,
    viewMode: "table",
    onViewModeChange: vi.fn(),
    onRefresh: vi.fn(),
    loading: false,
    additionalFilters: [],
    onAdditionalFilterChange: vi.fn(),
    bulkActions: [],
    ...overrides,
  };

  render(<TableToolbar {...props} />);

  return {
    filters,
    props,
  };
};

const openDropdownMenu = (trigger: HTMLElement) => {
  trigger.focus();
  fireEvent.keyDown(trigger, { key: "Enter" });
  fireEvent.keyUp(trigger, { key: "Enter" });
};

describe("TableToolbar quick filters", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the quick filter buttons", () => {
    renderToolbar();

    expect(screen.getByRole("button", { name: "הנכסים שלי" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "סוג עיסקה" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "מחיר" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "שטח" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "סוג נכס" })).toBeInTheDocument();
  });

  it("keeps the my assets toggle as the first quick filter", () => {
    renderToolbar();

    const container = screen.getByTestId("quick-filters-container");
    const buttons = within(container).getAllByRole("button");

    expect(buttons[0]).toHaveAccessibleName("הנכסים שלי");
  });

  it("places the full filters trigger directly after the quick filters", () => {
    renderToolbar();

    const container = screen.getByTestId("quick-filters-container");
    const filterButton = within(container).getByRole("button", { name: "סינון" });

    expect(filterButton).toBeInTheDocument();
    expect(filterButton.className).toContain("rounded-full");
  });

  it("arranges quick filters in a responsive wrapping row on small screens", () => {
    renderToolbar();

    const container = screen.getByTestId("quick-filters-container");

    expect(container).toHaveClass("flex-wrap");
    expect(container).toHaveClass("w-full");
  });

  it("keeps toolbar actions grouped in a wrapping container", () => {
    renderToolbar();

    const container = screen.getByTestId("toolbar-actions-container");

    expect(container).toHaveClass("flex-wrap");
    expect(container).toHaveClass("w-full");
  });

  it("renders rounded view mode toggle buttons", () => {
    renderToolbar();

    const tableToggle = screen.getByLabelText("תצוגת טבלה");
    const cardsToggle = screen.getByLabelText("תצוגת כרטיסים");
    const mapToggle = screen.getByLabelText("תצוגת מפה");

    expect(tableToggle.className).toContain("rounded-full");
    expect(cardsToggle.className).toContain("rounded-full");
    expect(mapToggle.className).toContain("rounded-full");
  });

  it("toggles the my assets quick filter", () => {
    const { props } = renderToolbar();

    fireEvent.click(screen.getByRole("button", { name: "הנכסים שלי" }));

    expect(props.onAdditionalFilterChange).toHaveBeenCalledWith("userAssets", "mine");
  });

  it("allows choosing rental or sale directly", () => {
    const { props } = renderToolbar();

    const trigger = screen.getByRole("button", { name: "סוג עיסקה" });
    openDropdownMenu(trigger);
    const rentalOption = screen.getByRole("menuitemradio", { name: "השכרה" });
    fireEvent.click(rentalOption);

    expect(props.onAdditionalFilterChange).toHaveBeenCalledWith("rentalSale", "rental");
  });

  it("updates price range from the quick filter popover", () => {
    const filters = createFilters();

    renderToolbar({}, filters);

    fireEvent.click(screen.getByRole("button", { name: "מחיר" }));

    fireEvent.change(screen.getByLabelText("מחיר מינימלי"), { target: { value: "1200000" } });
    expect(filters.priceMin.onChange).toHaveBeenCalledWith(1200000);

    fireEvent.change(screen.getByLabelText("מחיר מקסימלי"), { target: { value: "3200000" } });
    expect(filters.priceMax.onChange).toHaveBeenCalledWith(3200000);
  });

  it("places the price popover below the trigger without covering nearby controls", () => {
    renderToolbar();

    fireEvent.click(screen.getByRole("button", { name: "מחיר" }));

    const popover = screen.getByLabelText("מחיר מינימלי").closest("[data-state]");

    expect(popover).not.toBeNull();

    const element = popover as HTMLElement;

    expect(element).toHaveAttribute("data-side", "bottom");
    expect(element).toHaveAttribute("data-align", "end");
    expect(element).toHaveClass("max-w-sm");
    expect(element).toHaveClass("bg-background");
  });

  it("updates area range from the quick filter popover", () => {
    const filters = createFilters();

    renderToolbar({}, filters);

    fireEvent.click(screen.getByRole("button", { name: "שטח" }));

    fireEvent.change(screen.getByLabelText("שטח מינימלי"), { target: { value: "80" } });
    expect(filters.areaMin.onChange).toHaveBeenCalledWith(80);

    fireEvent.change(screen.getByLabelText("שטח מקסימלי"), { target: { value: "120" } });
    expect(filters.areaMax.onChange).toHaveBeenCalledWith(120);
  });

  it("places the area popover below the trigger without covering nearby controls", () => {
    renderToolbar();

    fireEvent.click(screen.getByRole("button", { name: "שטח" }));

    const popover = screen.getByLabelText("שטח מינימלי").closest("[data-state]");

    expect(popover).not.toBeNull();

    const element = popover as HTMLElement;

    expect(element).toHaveAttribute("data-side", "bottom");
    expect(element).toHaveAttribute("data-align", "end");
    expect(element).toHaveClass("max-w-sm");
    expect(element).toHaveClass("bg-background");
  });

  it("supports quick type selection", () => {
    const filters = createFilters();

    renderToolbar({}, filters);

    const trigger = screen.getByRole("button", { name: "סוג נכס" });
    openDropdownMenu(trigger);
    fireEvent.click(screen.getByRole("menuitemradio", { name: "דירה" }));

    expect(filters.type.onChange).toHaveBeenCalledWith("דירה");
  });
});
