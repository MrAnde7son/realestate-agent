DEFAULT_REPORT_SECTIONS = [
    'summary',
    'permits',
    'plans',
    'planning',
    'environment',
    'comparables',
    'mortgage',
    'appendix',
]

SECTION_TITLES_HE = {
    'summary': 'סיכום',
    'permits': 'היתרים',
    'plans': 'תוכניות',
    'planning': 'תכנון הנכס',
    'environment': 'סביבה',
    'comparables': 'השוואות',
    'mortgage': 'תרחישי משכנתא',
    'appendix': 'נספח',
}

# Plan configuration
PLAN_LIMITS = {
    'free': {
        'asset_limit': 1,
        'report_limit': 1,
        'alert_limit': 0,
        'advanced_analytics': False,
        'data_export': False,
        'api_access': False,
        'priority_support': False,
        'custom_reports': False,
    },
    'basic': {
        'asset_limit': 10,
        'report_limit': 25,
        'alert_limit': 25,
        'advanced_analytics': False,
        'data_export': True,
        'api_access': False,
        'priority_support': False,
        'custom_reports': True,
    },
    'pro': {
        'asset_limit': -1,  # Unlimited
        'report_limit': -1,  # Unlimited
        'alert_limit': -1,  # Unlimited
        'advanced_analytics': True,
        'data_export': True,
        'api_access': True,
        'priority_support': True,
        'custom_reports': True,
    },
}

PLAN_DISPLAY_NAMES = {
    'free': 'פרטי',
    'basic': 'בסיסי',
    'pro': 'עיסקי',
}

PLAN_DESCRIPTIONS = {
    'free': 'דוח חד פעמי למשקיע פרטי',
    'basic': 'מנוי חודשי למשקיע פעיל עם חבילת דוחות מתקדמת',
    'pro': 'פתרון עסקי לצוותים מקצועיים עם יכולות ללא הגבלה',
}
