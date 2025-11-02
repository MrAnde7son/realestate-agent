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
  adType: {
    value: "all",
    onChange: vi.fn(),
    options: [
      { value: "private", label: "פרטי" },
      { value: "broker", label: "מתווך" },
    ],
  },
  userAssets: {
    value: "all",
    onChange: vi.fn(),
    options: [
      { value: "mine", label: "נכסים שלי" },
      { value: "watchlist", label: "ברשימת המעקב שלי" },
      { value: "others", label: "נכסים של אחרים" },
    ],
  },
  commercial: {
    value: "all",
    onChange: vi.fn(),
    options: [
      { value: "residential", label: "מגורים" },
      { value: "commercial", label: "מסחרי" },
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

const getQuickFilterButton = (label: string) =>
  screen.getByRole("button", { name: (name) => name?.includes(label) ?? false });

describe("TableToolbar quick filters", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the quick filter buttons", () => {
    renderToolbar();

    expect(getQuickFilterButton("הנכסים שלי")).toBeInTheDocument();
    expect(getQuickFilterButton("סוג עיסקה")).toBeInTheDocument();
    expect(getQuickFilterButton("סוג מפרסם")).toBeInTheDocument();
    expect(getQuickFilterButton("ייעוד נכס")).toBeInTheDocument();
    expect(getQuickFilterButton("מחיר")).toBeInTheDocument();
    expect(getQuickFilterButton("שטח")).toBeInTheDocument();
    expect(getQuickFilterButton("סוג נכס")).toBeInTheDocument();
  });

  it("keeps the my assets toggle as the first quick filter", () => {
    renderToolbar();

    const container = screen.getByTestId("quick-filters-container");
    const buttons = within(container).getAllByRole("button");

    expect(buttons[0]).toHaveAccessibleName(/הנכסים שלי/);
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

  it("organizes the full filters into guided sections", () => {
    const additionalFilters = [
      {
        key: "neighborhood",
        label: "שכונה",
        type: "select" as const,
        value: "all",
        options: [
          { value: "all", label: "כל השכונות" },
          { value: "center", label: "מרכז" },
        ],
      },
      {
        key: "rooms",
        label: "חדרים",
        type: "select" as const,
        value: "all",
        options: [
          { value: "all", label: "כל החדרים" },
          { value: "3", label: "3 חדרים" },
        ],
      },
      {
        key: "source",
        label: "מקור",
        type: "select" as const,
        value: "all",
        options: [
          { value: "all", label: "כל המקורות" },
          { value: "yad2", label: "יד2" },
        ],
      },
      {
        key: "notes",
        label: "הערות",
        type: "text" as const,
        value: "",
        placeholder: "הקלד הערה",
      },
    ];

    renderToolbar({ additionalFilters });

    fireEvent.click(screen.getByRole("button", { name: "סינון" }));

    const primaryToggle = screen.getByRole("button", { name: "מיקום ותקציב" });
    expect(primaryToggle).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByText("עיר")).toBeInTheDocument();
    expect(screen.getByLabelText("מחיר מינימלי")).toBeInTheDocument();
    expect(screen.getByText("שכונה")).toBeInTheDocument();

    const propertyToggle = screen.getByRole("button", { name: "מאפייני נכס" });
    expect(propertyToggle).toHaveAttribute("aria-expanded", "false");
    fireEvent.click(propertyToggle);
    expect(propertyToggle).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByText("חדרים")).toBeInTheDocument();

    const transactionToggle = screen.getByRole("button", { name: "סטטוס ומקור" });
    fireEvent.click(transactionToggle);
    expect(transactionToggle).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByText("מקור")).toBeInTheDocument();

    const advancedToggle = screen.getByRole("button", { name: "סינון מתקדם" });
    expect(advancedToggle).toHaveAttribute("aria-expanded", "false");
    fireEvent.click(advancedToggle);
    expect(advancedToggle).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByPlaceholderText("הקלד הערה")).toBeInTheDocument();
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

  it("selects the 'my assets' option from the ownership quick filter", () => {
    const { props } = renderToolbar();

    const trigger = getQuickFilterButton("הנכסים שלי");
    openDropdownMenu(trigger);

    const option = screen.getByRole("menuitemradio", { name: "נכסים שלי" });
    fireEvent.click(option);

    expect(props.onAdditionalFilterChange).toHaveBeenCalledWith("userAssets", "mine");
  });

  it("allows filtering by watchlist from the ownership quick filter", () => {
    const { props } = renderToolbar();

    const trigger = getQuickFilterButton("הנכסים שלי");
    openDropdownMenu(trigger);

    const option = screen.getByRole("menuitemradio", { name: "ברשימת המעקב שלי" });
    fireEvent.click(option);

    expect(props.onAdditionalFilterChange).toHaveBeenCalledWith("userAssets", "watchlist");
  });

  it("allows choosing rental or sale directly", () => {
    const { props } = renderToolbar();

    const trigger = getQuickFilterButton("סוג עיסקה");
    openDropdownMenu(trigger);
    const rentalOption = screen.getByRole("menuitemradio", { name: "השכרה" });
    fireEvent.click(rentalOption);

    expect(props.onAdditionalFilterChange).toHaveBeenCalledWith("rentalSale", "rental");
  });

  it("allows choosing advertiser type directly", () => {
    const { props } = renderToolbar();

    const trigger = getQuickFilterButton("סוג מפרסם");
    openDropdownMenu(trigger);
    const privateOption = screen.getByRole("menuitemradio", { name: "פרטי" });
    fireEvent.click(privateOption);

    expect(props.onAdditionalFilterChange).toHaveBeenCalledWith("adType", "private");
  });

  it("updates price range from the quick filter popover", () => {
    const filters = createFilters();

    renderToolbar({}, filters);

    fireEvent.click(getQuickFilterButton("מחיר"));

    fireEvent.change(screen.getByLabelText("מחיר מינימלי"), { target: { value: "1200000" } });
    expect(filters.priceMin.onChange).toHaveBeenCalledWith(1200000);

    fireEvent.change(screen.getByLabelText("מחיר מקסימלי"), { target: { value: "3200000" } });
    expect(filters.priceMax.onChange).toHaveBeenCalledWith(3200000);
  });

  it("places the price popover below the trigger without covering nearby controls", () => {
    renderToolbar();

    fireEvent.click(getQuickFilterButton("מחיר"));

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

    fireEvent.click(getQuickFilterButton("שטח"));

    fireEvent.change(screen.getByLabelText("שטח מינימלי"), { target: { value: "80" } });
    expect(filters.areaMin.onChange).toHaveBeenCalledWith(80);

    fireEvent.change(screen.getByLabelText("שטח מקסימלי"), { target: { value: "120" } });
    expect(filters.areaMax.onChange).toHaveBeenCalledWith(120);
  });

  it("places the area popover below the trigger without covering nearby controls", () => {
    renderToolbar();

    fireEvent.click(getQuickFilterButton("שטח"));

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

    const trigger = getQuickFilterButton("סוג נכס");
    openDropdownMenu(trigger);
    fireEvent.click(screen.getByRole("menuitemradio", { name: "דירה" }));

    expect(filters.type.onChange).toHaveBeenCalledWith("דירה");
  });

  it("prefetches the map view when the toggle is hovered or focused", () => {
    const onPrefetchViewMode = vi.fn();
    renderToolbar({ onPrefetchViewMode });

    const mapButton = screen.getByRole("button", { name: "תצוגת מפה" });

    fireEvent.mouseEnter(mapButton);
    expect(onPrefetchViewMode).toHaveBeenCalledWith("map");

    onPrefetchViewMode.mockClear();
    fireEvent.focus(mapButton);
    expect(onPrefetchViewMode).toHaveBeenCalledWith("map");
  });
});
