// קבועים גלובליים לשרת MCP
export const CKAN_BASE_URL = "https://data.gov.il/api/3/action";

export const DEFAULT_TIMEOUT = 10000;
export const SEARCH_TIMEOUT = 15000;

export const USER_AGENT = 'MCP-DataGovIL-Client/2.0.0';

export const DEFAULT_LIMITS = {
  list: 10,
  search: 100,
  max: 1000
};

export const POPULAR_DATASETS = [
  'branches', 
  'jerusalem-municipality-budget', 
  'mechir-lamishtaken', 
  'traffic-counts', 
  'population-and-recipients-of-benefits-under-settlement-2012'
];

// ארגונים פופולריים (הוספה לתמיכה בכלי הארגונים החדש)
export const POPULAR_ORGANIZATIONS = [
  'ministry-of-health',
  'tel-aviv-yafo',
  'jerusalem',
  'cbs',
  'ministry-of-finance'
];

// נושאים פופולריים לחיפוש (לשימוש כקמילות מפתח)
export const POPULAR_TOPICS = [
  'אוצר וכלכלה',
  'סביבה', 
  'משרד התחבורה',
  'תחבורה',
  'GIS',
  'אוכלוסיה',
  'מים',
  'תקציב'
];

// קטגוריות נושאים זמינות
export const TOPIC_CATEGORIES = [
  'government',
  'transportation', 
  'environment',
  'health_welfare',
  'education',
  'demographics',
  'technology',
  'economy',
  'agriculture',
  'tourism',
  'organizations'
];

// דוגמאות resource IDs שבדקנו שעובדים (לתיעוד ובדיקות)
export const EXAMPLE_RESOURCE_IDS = {
  bankBranches: '2202bada-4baf-45f5-aa61-8c5bad9646d3',
  airStations: '782cfb94-ebbd-4f41-aba2-80c298457a58', 
  contaminatedLand: '54aa9ff1-2d89-4899-bb57-bf2a749ff4b3'
};

/**
 * מילות מפתח נפוצות בעברית ואנגלית
 */
export const COMMON_KEYWORDS = {
  hebrew: [
    'תקציב (budget)',
    'אוכלוסיה (population)',
    'תחבורה (transport)',
    'בריאות (health)',
    'חינוך (education)',
    'סביבה (environment)'
  ],
  
  english: [
    'budget', 'population', 'transport',
    'health', 'education', 'environment',
    'municipality', 'government', 'public'
  ]
};

/**
 * דוגמאות חיפוש עבור find_datasets (מעודכן לחיפוש לפי נושא)
 */
export const FIND_EXAMPLES = [
  'find_datasets("תחבורה") → transportation datasets',
  'find_datasets("תקציב עירייה") → municipal budgets',
  'find_datasets("בנק") → banking related datasets', 
  'find_datasets("traffic") → transportation data',
  'find_datasets("health בריאות") → health datasets',
  'find_datasets("סביבה") → environment datasets',
  'find_datasets("אוכלוסיה") → demographics datasets'
];