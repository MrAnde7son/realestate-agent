/**
 * תגיות DATA.GOV.IL - מאורגנות לפי קטגוריות
 */

export const TAGS_DATA = {
  metadata: {
    source: "data.gov.il",
    total_tags: 50,
    last_updated: "2025-01-28",
    note: "Numbers indicate dataset count per tag"
  },
  
  popular_tags: {
    top_10: [
      { tag: "אוצר וכלכלה", count: 102, category: "government" },
      { tag: "סביבה", count: 78, category: "environment" },
      { tag: "משרד התחבורה", count: 74, category: "organization" },
      { tag: "חצב", count: 69, category: "organization" },
      { tag: "תחבורה", count: 69, category: "transportation" },
      { tag: "ממג", count: 67, category: "organization" },
      { tag: "GIS", count: 63, category: "technology" },
      { tag: "אוכלוסיה", count: 59, category: "demographics" },
      { tag: "מים", count: 50, category: "environment" },
      { tag: "תקציב", count: 50, category: "finance" }
    ]
  },

  categories: {
    government: {
      hebrew: "ממשל",
      tags: [
        { tag: "אוצר וכלכלה", count: 102 },
        { tag: "תקציב", count: 50 },
        { tag: "תקציב וביצוע", count: 14 },
        { tag: "שינויים בתקציב", count: 12 },
        { tag: "תכנון", count: 16 },
        { tag: "משפט", count: 13 },
        { tag: "דת", count: 12 }
      ]
    },
    
    transportation: {
      hebrew: "תחבורה",
      tags: [
        { tag: "תחבורה", count: 69 },
        { tag: "תחבורה ציבורית", count: 31 },
        { tag: "כלי רכב", count: 27 },
        { tag: "רכב", count: 27 },
        { tag: "רכבת", count: 15 },
        { tag: "אוטובוסים", count: 12 },
        { tag: "רכבת כבדה", count: 11 },
        { tag: "דרכים", count: 10 },
        { tag: "שאלות תאוריה", count: 13 },
        { tag: "מבחן נהיגה עיוני", count: 12 }
      ]
    },

    environment: {
      hebrew: "סביבה",
      tags: [
        { tag: "סביבה", count: 78 },
        { tag: "מים", count: 50 },
        { tag: "water", count: 44 },
        { tag: "הגנת הסביבה", count: 14 },
        { tag: "זיהום אוויר", count: 12 },
        { tag: "פליטות", count: 11 },
        { tag: "פסולת", count: 10 },
        { tag: "הידרומטריה", count: 10 },
        { tag: "borehole", count: 10 }
      ]
    },

    health_welfare: {
      hebrew: "בריאות ורווחה",
      tags: [
        { tag: "בריאות ורווחה", count: 38 },
        { tag: "בריאות", count: 20 }
      ]
    },

    education: {
      hebrew: "חינוך",
      tags: [
        { tag: "חינוך", count: 28 },
        { tag: "חינוך ותרבות", count: 17 },
        { tag: "מדע", count: 12 }
      ]
    },

    demographics: {
      hebrew: "דמוגרפיה",
      tags: [
        { tag: "אוכלוסיה", count: 59 },
        { tag: "עולים חדשים", count: 13 },
        { tag: "עלייה", count: 10 }
      ]
    },

    technology: {
      hebrew: "טכנולוגיה",
      tags: [
        { tag: "GIS", count: 63 },
        { tag: "gis", count: 15 }
      ]
    },

    economy: {
      hebrew: "כלכלה",
      tags: [
        { tag: "כלכלה", count: 11 }
      ]
    },

    agriculture: {
      hebrew: "חקלאות",
      tags: [
        { tag: "חקלאות", count: 14 }
      ]
    },

    tourism: {
      hebrew: "תיירות",
      tags: [
        { tag: "תיירות", count: 15 }
      ]
    },

    organizations: {
      hebrew: "ארגונים",
      tags: [
        { tag: "משרד התחבורה", count: 74 },
        { tag: "חצב", count: 69, full_name: "החברה הממשלתית לביטוח בריאות" },
        { tag: "ממג", count: 67, full_name: "מרכז מיפוי ישראל" },
        { tag: "רשות המים", count: 48 },
        { tag: "משרד המשפטים", count: 46 },
        { tag: "משרד הבריאות", count: 16 },
        { tag: "בנק ישראל", count: 15 },
        { tag: "המרכז למיפוי ישראל", count: 15 },
        { tag: "משרד התקשורת", count: 13 },
        { tag: "משרד התיירות", count: 11 },
        { tag: "מינהל התכנון", count: 10 }
      ]
    }
  },

  duplicates: {
    note: "Tags that represent the same concept",
    gis: ["GIS", "gis"],
    water: ["מים", "water"],
    mapping: ["ממג", "המרכז למיפוי ישראל"]
  },

  search_suggestions: {
    by_theme: {
      financial: ["אוצר וכלכלה", "תקציב", "כלכלה", "בנק ישראל"],
      transportation: ["תחבורה", "תחבורה ציבורית", "משרד התחבורה"],
      environmental: ["סביבה", "מים", "הגנת הסביבה"],
      health: ["בריאות", "בריאות ורווחה", "משרד הבריאות"],
      geographic: ["GIS", "ממג", "המרכז למיפוי ישראל"],
      demographic: ["אוכלוסיה", "עלייה", "עולים חדשים"]
    }
  }
};

/**
 * מקבל קטגוריה ומחזיר את התגיות שלה
 */
export function getTagsByCategory(category) {
  return TAGS_DATA.categories[category]?.tags || [];
}

/**
 * מחפש תגיות לפי מילת מפתח
 */
export function searchTags(keyword) {
  const results = [];
  const lowerKeyword = keyword.toLowerCase();
  
  Object.values(TAGS_DATA.categories).forEach(category => {
    category.tags.forEach(tagObj => {
      if (tagObj.tag.toLowerCase().includes(lowerKeyword)) {
        results.push({
          ...tagObj,
          category: category.hebrew
        });
      }
    });
  });
  
  return results.sort((a, b) => b.count - a.count);
}

/**
 * מחזיר תגיות פופולריות
 */
export function getPopularTags(limit = 10) {
  return TAGS_DATA.popular_tags.top_10.slice(0, limit);
}

/**
 * מחזיר הצעות תגיות לפי תחום
 */
export function getTagSuggestions(theme) {
  return TAGS_DATA.search_suggestions.by_theme[theme] || [];
}