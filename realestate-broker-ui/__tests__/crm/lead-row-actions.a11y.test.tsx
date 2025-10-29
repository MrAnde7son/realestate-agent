import { render, screen } from "@testing-library/react";
import { LeadRowActions } from "@/components/crm/lead-row-actions";
import type { Lead } from "@/lib/api/crm";

const baseLead: Lead = {
  id: 1,
  contact: {
    id: 10,
    name: "לקוח בדיקה",
    phone: "050-0000000",
    email: "test@example.com",
    equity: null,
    city: "תל אביב",
    streets: "דיזנגוף",
    asset_type: "דירה",
    area_min: null,
    area_max: null,
    floor: "3",
    notes: "",
    tags: [],
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  contact_id: 10,
  asset_id: 20,
  asset_id_read: 20,
  asset_address: "רחוב הבדיקה 1",
  asset_price: 1200000,
  asset_rooms: 4,
  asset_area: 95,
  status: "new",
  notes: [],
  last_activity_at: new Date().toISOString(),
  created_at: new Date().toISOString(),
};

describe("LeadRowActions accessibility", () => {
  it("labels icon-only actions", () => {
    render(
      <LeadRowActions
        lead={baseLead}
        onUpdate={() => {}}
        onDelete={() => {}}
        onShowTasks={() => {}}
      />
    );

    expect(screen.getByLabelText("עדכן סטטוס ליד")).toBeInTheDocument();
    expect(screen.getByLabelText("הוסף הערה לליד")).toBeInTheDocument();
    expect(screen.getByLabelText("הצג משימות לליד")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "שלח דוח ללקוח" })).toBeInTheDocument();
    expect(screen.getByLabelText("מחק ליד")).toBeInTheDocument();
  });

  it("communicates when sending a report is unavailable", () => {
    const leadWithoutEmail: Lead = {
      ...baseLead,
      contact: { ...baseLead.contact, email: "" },
    };

    render(
      <LeadRowActions
        lead={leadWithoutEmail}
        onUpdate={() => {}}
        onDelete={() => {}}
      />
    );

    const disabledButton = screen.getByRole("button", {
      name: "לא ניתן לשלוח דוח - אין כתובת אימייל",
    });
    expect(disabledButton).toBeDisabled();
  });
});
