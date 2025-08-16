export interface Listing {
  id: string
  address: string
  price: number
  bedrooms: number
  bathrooms: number
  area: number
  type: string
  status: "active" | "pending" | "sold"
  images: string[]
  description: string
  features: string[]
  contactInfo: {
    agent: string
    phone: string
    email: string
  }
}

export const listings: Listing[] = [
  {
    id: "l1",
    address: "רחוב הרצל 123, תל אביב",
    price: 2850000,
    bedrooms: 3,
    bathrooms: 2,
    area: 85,
    type: "דירה",
    status: "active",
    images: ["/placeholder-home.jpg"],
    description: "דירה מקסימה במרכז תל אביב עם נוף לים",
    features: ["מעלית", "חניה", "מרפסת", "משופצת"],
    contactInfo: {
      agent: "יוסי כהן",
      phone: "050-1234567",
      email: "yossi@example.com"
    }
  },
  {
    id: "l2",
    address: "שדרות רוטשילד 45, תל אביב",
    price: 4200000,
    bedrooms: 4,
    bathrooms: 3,
    area: 120,
    type: "דירה",
    status: "pending",
    images: ["/placeholder-home.jpg"],
    description: "דירת פנטהאוס מפוארת עם מרפסת גדולה",
    features: ["מעלית", "חניה", "מרפסת גדולה", "חדר עבודה"],
    contactInfo: {
      agent: "דנה לוי",
      phone: "052-7654321",
      email: "dana@example.com"
    }
  }
]
