/**
 * כלי list_available_tags - מציג נושאים זמינים לפי קטגוריות
 */

import { z } from 'zod';
import { TAGS_DATA, getTagsByCategory, searchTags, getPopularTags, getTagSuggestions } from '../config/tags.js';
import { createMcpResponse } from '../utils/formatters.js';

/**
 * מפרמט רשימת נושאים לפי קטגוריה
 * @param {string} category - קטגוריה או null לכל הקטגוריות
 * @param {boolean} showCounts - האם להציג מספרי datasets
 * @returns {Array} בלוקי תוכן מפורמטים
 */
function formatTagsResponse(category = null, showCounts = true) {
  if (category && TAGS_DATA.categories[category]) {
    // קטגוריה ספציפית
    const categoryData = TAGS_DATA.categories[category];
    const tags = categoryData.tags;
    
    const mainContent = [
      `🏷️ נושאים בקטגוריה: ${categoryData.hebrew} (${category})`,
      '',
      `📊 ${tags.length} נושאים זמינים:`,
      ...tags.map(t => showCounts ? `• ${t.tag} (${t.count} datasets)` : `• ${t.tag}`)
    ].join('\n');

    const usageContent = [
      '💡 שימוש:',
      `• find_datasets("${tags[0]?.tag}")`,
      `• find_datasets("${tags[0]?.tag}", sort="newest")`,
      '',
      '🔍 דוגמאות מעשיות:',
      ...tags.slice(0, 3).map(t => `• find_datasets("${t.tag}") → ${t.count} datasets`),
      '',
      '📋 כל הקטגוריות: list_available_tags()'
    ].join('\n');

    return [mainContent, usageContent];
  }

  // כל הקטגוריות
  const mainContent = [
    '🏷️ נושאים DATA.GOV.IL - מסודרים לפי קטגוריות',
    '',
    `📊 סה"כ: ${TAGS_DATA.metadata.total_tags} נושאים`,
    `🔄 עודכן: ${TAGS_DATA.metadata.last_updated}`,
    '',
    '📂 קטגוריות זמינות:'
  ];

  Object.entries(TAGS_DATA.categories).forEach(([key, data]) => {
    const tagCount = data.tags.length;
    const topTag = data.tags[0];
    mainContent.push(`• ${data.hebrew} (${key}): ${tagCount} נושאים, הפופולרי: "${topTag?.tag}" (${topTag?.count})`);
  });

  const guidanceContent = [
    '🎯 TOP 10 נושאים פופולריים:',
    ...TAGS_DATA.popular_tags.top_10.map(t => `• ${t.tag} (${t.count} datasets)`),
    '',
    '🔍 חיפוש לפי קטגוריה:',
    '• list_available_tags(category="transportation") → נושאי תחבורה',
    '• list_available_tags(category="environment") → נושאי סביבה',
    '• list_available_tags(category="government") → נושאי ממשל',
    '',
    '💡 שימוש מעשי:',
    '• find_datasets("תחבורה") → datasets בתחום התחבורה',
    '• find_datasets("סביבה") → datasets בתחום הסביבה',
    '• find_datasets("בנק") → datasets הקשורים לבנקאות',
    '',
    '🎪 הצעות לחקירה:',
    '• פיננסי: אוצר וכלכלה, תקציב, בנק ישראל',
    '• תחבורה: תחבורה, תחבורה ציבורית, משרד התחבורה',  
    '• סביבה: סביבה, מים, הגנת הסביבה',
    '• בריאות: בריאות, בריאות ורווחה, משרד הבריאות'
  ].join('\n');

  return [mainContent.join('\n'), guidanceContent];
}

/**
 * רישום הכלי במערכת MCP
 * @param {McpServer} mcp - שרת MCP
 */
export function registerTagsTool(mcp) {
  mcp.tool(
    "list_available_tags",
    {
      category: z.enum([
        'government', 'transportation', 'environment', 'health_welfare', 
        'education', 'demographics', 'technology', 'economy', 'agriculture', 
        'tourism', 'organizations'
      ]).optional().describe("Filter by specific category. Examples: 'transportation', 'environment', 'government'"),
      
      show_counts: z.boolean().default(true).describe("Show dataset counts for each topic"),
      
      format: z.enum(['overview', 'detailed', 'suggestions']).default('overview').describe(
        "Response format: 'overview' (all categories), 'detailed' (specific category), 'suggestions' (themed recommendations)"
      )
    },
    async ({ category, show_counts, format }) => {
      try {
        console.error(`🏷️ Listing available topics (category: ${category || 'all'}, format: ${format})...`);

        let contentBlocks;

        if (format === 'suggestions') {
          // הצעות מותאמות אישית
          const mainContent = [
            '💡 הצעות נושאים לפי תחומי עניין:',
            '',
            '💰 פיננסי/כלכלי:',
            ...getTagSuggestions('financial').map(tag => `• find_datasets("${tag}")`),
            '',
            '🚗 תחבורה:',
            ...getTagSuggestions('transportation').map(tag => `• find_datasets("${tag}")`),
            '',
            '🌱 סביבה:',
            ...getTagSuggestions('environmental').map(tag => `• find_datasets("${tag}")`),
            '',
            '🏥 בריאות:',
            ...getTagSuggestions('health').map(tag => `• find_datasets("${tag}")`),
            '',
            '🗺️ גיאוגרפי/מיפוי:',
            ...getTagSuggestions('geographic').map(tag => `• find_datasets("${tag}")`),
            '',
            '👥 דמוגרפי:',
            ...getTagSuggestions('demographic').map(tag => `• find_datasets("${tag}")`)
          ].join('\n');

          const usageContent = [
            '🎯 איך להשתמש:',
            '1. בחר תחום עניין מהרשימה למעלה',
            '2. העתק את הפקודה find_datasets',
            '3. אפשר גם להוסיף מיון: find_datasets("נושא", sort="newest")',
            '',
            '📊 לרשימה מלאה: list_available_tags()',
            '🔍 לקטגוריה ספציפית: list_available_tags(category="transportation")'
          ].join('\n');

          contentBlocks = [mainContent, usageContent];
        } else {
          contentBlocks = formatTagsResponse(category, show_counts);
        }

        console.error(`✅ Listed topics successfully (${category || 'all categories'})`);

        return {
          content: contentBlocks.map(block => ({
            type: "text",
            text: block
          }))
        };

      } catch (error) {
        console.error('❌ Error in list_available_tags:', error.message);
        
        return createMcpResponse([
          `❌ Error listing topics: ${error.message}`,
          '',
          '💡 Try:',
          '• list_available_tags() → all categories',
          '• list_available_tags(category="transportation") → specific category',
          '• list_available_tags(format="suggestions") → themed suggestions'
        ]);
      }
    }
  );
}

/**
 * כלי עזר נוסף - חיפוש נושאים לפי מילת מפתח
 */
export function registerSearchTagsTool(mcp) {
  mcp.tool(
    "search_tags",
    {
      keyword: z.string().describe("Search keyword in Hebrew or English. Examples: 'בנק', 'transport', 'סביבה'")
    },
    async ({ keyword }) => {
      try {
        console.error(`🔍 Searching topics for keyword: "${keyword}"...`);

        const results = searchTags(keyword);
        
        if (results.length === 0) {
          return createMcpResponse([
            `🔍 לא נמצאו נושאים עבור "${keyword}"`,
            '',
            '💡 נסה:',
            '• מילים כלליות יותר',
            '• list_available_tags() לראות את כל הנושאים',
            '• list_available_tags(format="suggestions") להצעות לפי תחום'
          ]);
        }

        const mainContent = [
          `🔍 נמצאו ${results.length} נושאים עבור "${keyword}":`,
          '',
          ...results.map(r => `• ${r.tag} (${r.count} datasets) - ${r.category}`)
        ].join('\n');

        const usageContent = [
          '💡 שימוש:',
          ...results.slice(0, 3).map(r => `• find_datasets("${r.tag}")`),
          '',
          '🔗 חיפוש משולב:',
          `• find_datasets("${keyword} ${results[0]?.tag}") → חיפוש משולב`,
          `• find_datasets("${results[0]?.tag}", sort="newest") → עם מיון`
        ].join('\n');

        console.error(`✅ Found ${results.length} matching topics`);

        return {
          content: [mainContent, usageContent].map(block => ({
            type: "text",
            text: block
          }))
        };

      } catch (error) {
        console.error('❌ Error in search_tags:', error.message);
        
        return createMcpResponse([
          `❌ Error searching topics: ${error.message}`,
          '',
          '💡 Try: list_available_tags() to see all available topics'
        ]);
      }
    }
  );
}