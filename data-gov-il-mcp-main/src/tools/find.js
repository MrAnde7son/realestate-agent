/**
 * כלי find_datasets - חיפוש חכם במאגר datasets עם מיון 
 */

import { z } from 'zod';
import { ckanRequest } from '../utils/api.js';
import { createErrorResponse } from '../utils/formatters.js';
import { POPULAR_DATASETS } from '../config/constants.js';
import { RECOMMENDED_WORKFLOW } from '../lib/guidance.js';
import { TAGS_DATA } from '../config/tags.js';

/**
 * מחפש תגיות לפי מונח ומחזיר הצעות לחיפוש
 * @param {string} inputTag - מונח לחיפוש
 * @returns {Array} תגיות תואמות לשימוש בquery
 */
function getTagSuggestions(inputTag) {
  if (!inputTag) return [];
  
  const allTags = Object.values(TAGS_DATA.categories)
    .flatMap(category => category.tags.map(t => t.tag));
  
  const lowerInput = inputTag.toLowerCase();
  
  // חיפוש התאמות חלקיות
  const suggestions = allTags.filter(tag => 
    tag.toLowerCase().includes(lowerInput) || 
    lowerInput.includes(tag.toLowerCase())
  );
  
  return suggestions.slice(0, 3);
}

/**
 * מיפוי של אפשרויות מיון לפרמטרי API
 */
const SORT_OPTIONS = {
  'newest': 'metadata_created desc',           
  'relevance': 'score desc,metadata_modified desc',   
  'popular': 'views_recent desc',              
  'updated': 'metadata_modified desc'          
};

/**
 * מפרמט תוצאות החיפוש מ-package_search
 * @param {Object} result - תוצאות מ-CKAN package_search
 * @param {string} query - מונח החיפוש המקורי
 * @param {string} sort - סדר המיון שנבחר
 * @returns {Array} בלוקי תוכן מפורמטים
 */
function formatFindResults(result, query, sort) {
  const datasets = result.results || [];
  const datasetNames = datasets.map(d => d.name || d.id);
  const totalCount = result.count || datasets.length;
  
  // בניית תיאור החיפוש
  const queryParts = [];
  if (query) queryParts.push(`"${query}"`);
  if (sort) queryParts.push(`sorted by: ${sort}`);
  
  const searchDescription = queryParts.length > 0 ? ` for ${queryParts.join(', ')}` : '';
  
  const mainContent = [
    `🔍 Found ${datasetNames.length} datasets${searchDescription} (${totalCount} total matches)`,
    '',
    datasetNames.length > 0 ? '📋 Matching datasets:' : '❌ No datasets found',
    datasetNames.length > 0 ? JSON.stringify(datasetNames, null, 2) : ''
  ].filter(line => line !== '').join('\n');

  let guidanceContent;
  
  if (datasetNames.length === 0) {
    guidanceContent = [
      '💡 SEARCH TIPS:',
      '• Try broader terms: "budget" instead of "municipal budget"',
      '• Use both Hebrew and English: "תקציב budget"',
      '• Try different sorting: newest, relevance, popular, updated',
      '• Use list_available_tags() to discover relevant topic keywords',
      '• Try searching with tag names: find_datasets("תחבורה"), find_datasets("סביבה")',
      '• Check popular datasets:',
      ...POPULAR_DATASETS.map(d => `  • ${d}`),
      '',
      '🔄 You can also use list_all_datasets to see everything (expensive)'
    ].join('\n');
  } else {
    guidanceContent = [
      '💡 NEXT STEPS:',
      '• Use list_resources with any interesting dataset name',
      '• Example: list_resources with dataset="branches"',
      '',
      '🚀 RECOMMENDED WORKFLOW:',
      ...RECOMMENDED_WORKFLOW.slice(1), // להשמיט את הכותרת
      '',
      '🔍 SEARCH BY TOPIC EXAMPLES:',
      '• find_datasets("תקציב", sort="newest") → newest budget datasets',
      '• find_datasets("תחבורה", sort="popular") → popular transportation datasets',
      '• find_datasets("בריאות", sort="updated") → recently updated health datasets',
      '• find_datasets("סביבה") → environment datasets',
      '',
      '💡 TIP: Use list_available_tags() to discover topic keywords for searching!'
    ].join('\n');
  }

  return [mainContent, guidanceContent];
}

/**
 * רישום הכלי במערכת MCP
 * @param {McpServer} mcp - שרת MCP
 */
export function registerFindDatasetsTool(mcp) {
  mcp.tool(
    "find_datasets",
    {
      query: z.string().describe(
        "Search terms (Hebrew/English). Use topic names from list_available_tags(). Examples: 'תקציב', 'תחבורה', 'סביבה', 'budget', 'transportation'"
      ),
      sort: z.enum(['newest', 'relevance', 'popular', 'updated']).optional().describe(
        "Sort results by: 'newest' (creation date), 'relevance' (best match), 'popular' (most viewed), 'updated' (recently modified)"
      )
    },
    async ({ query, sort }) => {
      try {
        // בניית תיאור החיפוש לוג
        const searchParts = [];
        if (query) searchParts.push(`query: "${query}"`);
        if (sort) searchParts.push(`sort: ${sort}`);
        
        const searchDescription = searchParts.length > 0 ? ` (${searchParts.join(', ')})` : '';
        console.error(`🔍 Searching datasets${searchDescription}...`);
        
        // בדיקה שיש query
        if (!query || !query.trim()) {
          return createErrorResponse(
            'find_datasets',
            new Error('Search query required'),
            [
              'Provide a search term to find relevant datasets',
              'Examples: find_datasets("תקציב"), find_datasets("transportation")',
              'Use list_available_tags() to discover topic keywords',
              'Try: find_datasets("תחבורה"), find_datasets("סביבה"), find_datasets("בריאות")',
              'Use list_all_datasets if you need to see everything (expensive)'
            ]
          );
        }
        
        // בניית פרמטרי החיפוש
        const params = {
          q: query.trim()
        };
        
        // הוספת sort אם קיים
        if (sort && SORT_OPTIONS[sort]) {
          params.sort = SORT_OPTIONS[sort];
        }
        
        // בדיקה אם המונח הוא תג מוכר (לטיפים)
        const allTags = Object.values(TAGS_DATA.categories)
          .flatMap(category => category.tags.map(t => t.tag));
        
        const isKnownTag = allTags.includes(query.trim());
        if (isKnownTag) {
          console.error(`✨ Searching with recognized topic: "${query.trim()}"`);
        }
        
        // קריאה ל-package_search API
        const response = await ckanRequest('package_search', params);
        const result = response.result;
        
        // אם אין תוצאות, נציע תגיות דומות
        if (result.results.length === 0) {
          const suggestions = getTagSuggestions(query.trim());
          
          const noResultsError = createErrorResponse(
            'find_datasets',
            new Error(`No results found for "${query.trim()}"`),
            [
              'Try broader search terms',
              'Use both Hebrew and English: "תקציב budget"',
              suggestions.length > 0 ? `Try similar topics: ${suggestions.join(', ')}` : 'Use list_available_tags() to discover available topics',
              'Use search_tags("keyword") to find relevant topic names',
              'Check spelling and try different variations'
            ]
          );
          
          return noResultsError;
        }
        
        const foundCount = result.results ? result.results.length : 0;
        console.error(`✅ Found ${foundCount} datasets${searchDescription}`);
        
        const contentBlocks = formatFindResults(result, query, sort);
        
        return {
          content: contentBlocks.map(block => ({
            type: "text",
            text: block
          }))
        };
        
      } catch (error) {
        console.error(`❌ Error in find_datasets:`, error.message);
        
        return createErrorResponse(
          'find_datasets',
          error,
          [
            'Try a different search term',
            'Check if the sort option is valid (newest, relevance, popular, updated)',
            'Use list_available_tags() to discover valid topic keywords',
            'Try searching for: תחבורה, סביבה, תקציב, בריאות',
            'Check your internet connection', 
            'The government API might be temporarily unavailable'
          ]
        );
      }
    }
  );
}