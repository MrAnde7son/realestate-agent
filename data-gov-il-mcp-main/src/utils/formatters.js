/**
 * פונקציות עיצוב ופורמט לתשובות MCP
 */

/**
 * יוצר תגובת MCP עם תוכן מפורמט
 * @param {Array} contentBlocks - רשימת בלוקי תוכן
 * @returns {Object} תגובת MCP מעוצבת
 */
export function createMcpResponse(contentBlocks) {
  return {
    content: contentBlocks.map(block => ({
      type: "text",
      text: block
    }))
  };
}

/**
 * יוצר תגובת שגיאה מפורמטת
 * @param {string} operation - הפעולה שנכשלה
 * @param {Error} error - השגיאה
 * @param {Array} suggestions - הצעות לפתרון
 * @returns {Object} תגובת שגיאה מפורמטת
 */
export function createErrorResponse(operation, error, suggestions = []) {
  const suggestionText = suggestions.length > 0 
    ? `\n\n💡 Try:\n${suggestions.map(s => `• ${s}`).join('\n')}`
    : '';
    
  return createMcpResponse([
    `❌ Error in ${operation}: ${error.message}${suggestionText}`
  ]);
}

/**
 * מפרמט רשימת datasets עם סטטיסטיקות ואזהרות
 * @param {Array} datasets - רשימת datasets
 * @param {Array} popularOnes - רשימת datasets פופולריים
 * @returns {Array} בלוקי תוכן מפורמטים
 */
export function formatDatasetsList(datasets, popularOnes = []) {
  const mainContent = [
    `⚠️ EXPENSIVE OPERATION: Retrieved ALL ${datasets.length} datasets from data.gov.il`,
    '',
    '🔥 Popular datasets to try:',
    ...popularOnes.map(d => `• ${d}`),
    '',
    '📋 All datasets:',
    JSON.stringify(datasets, null, 2)
  ].join('\n');

  const guidanceContent = [
    '⚠️ PERFORMANCE WARNING:',
    '• This operation fetches ALL datasets from the government API (expensive!)',
    '• For searching specific topics, use find_datasets instead',
    '• Only use list_all_datasets when you need the complete list',
    '',
    '💡 RECOMMENDED WORKFLOW:',
    '• 🔍 START with find_datasets to search by keywords',
    '• 📋 Use list_resources on interesting datasets', 
    '• 🎯 Use search_records to get actual data',
    '',
    '📝 DATASET TIPS:',
    '• Look for datasets related to: budgets, demographics, transportation, municipalities',
    '• Common Hebrew keywords: תקציב (budget), אוכלוסיה (population), תחבורה (transport)',
    '• Next step: Use list_resources with interesting dataset names',
    '• Pro tip: Many datasets have English equivalents (look for \'_en\' suffix)'
  ].join('\n');

  return [mainContent, guidanceContent];
}

/**
 * מפרמט מידע על resources של dataset
 * @param {string} datasetName - שם הdataset
 * @param {Array} resources - רשימת resources
 * @param {Array} exampleIds - דוגמאות resource IDs
 * @returns {Array} בלוקי תוכן מפורמטים
 */
export function formatResourcesList(datasetName, resources, exampleIds = {}) {
  const activeResources = resources.filter(r => r.datastore_active);
  
  const mainContent = [
    `📁 Dataset: ${datasetName}`,
    '',
    `🎯 ${activeResources.length}/${resources.length} resources are searchable with datastore`,
    '',
    '📊 Resources:',
    JSON.stringify(resources, null, 2)
  ].join('\n');

  const exampleText = Object.keys(exampleIds).length > 0
    ? `\n• Example working resources: ${Object.entries(exampleIds).map(([name, id]) => `${name} (${id})`).join(', ')}`
    : '';

  const guidanceContent = [
    '💡 NEXT STEPS:',
    '• Copy a resource_id from datastore_active=true resources',
    '• Use search_records with that resource_id',
    '• Look for CSV/XLSX formats - they\'re usually most complete',
    '• Hebrew resources often have English equivalents',
    exampleText,
    '',
    '🔍 SEARCH TIPS:',
    '• Fields vary by dataset - check the data structure first',
    '• Common fields: Name, City, Address, Date, Amount',
    '• Use include_tracking=true to see update frequency'
  ].join('\n');

  return [mainContent, guidanceContent];
}

/**
 * מפרמט תוצאות חיפוש
 * @param {Object} result - תוצאות החיפוש מ-CKAN
 * @returns {Array} בלוקי תוכן מפורמטים
 */
export function formatSearchResults(result) {
  const resultCount = result.records ? result.records.length : 0;
  const totalHint = result.total ? ` (${result.total} total matches)` : '';

  const mainContent = [
    `🎯 Found ${resultCount} records${totalHint}`,
    '',
    '📊 Results:',
    JSON.stringify(result, null, 2)
  ].join('\n');

  const optimizationContent = [
    '💡 SEARCH OPTIMIZATION:',
    '',
    '🔍 QUERY PATTERNS THAT WORK WELL:',
    '• Cities: "תל אביב", "ירושלים", "חיפה"',
    '• Banks: "בנק לאומי", "בנק הפועלים", "דיסקונט"',
    '• General: Use Hebrew for Israeli data, English for international',
    '',
    '⚡ PERFORMANCE TIPS:',
    '• Use \'fields\' parameter to get only needed columns',
    '• Use \'limit\' 5-20 for quick exploration',
    '• Use \'filters\' for exact matches (faster than \'q\')',
    '• Include \'include_total\' for pagination planning',
    '',
    '📈 ANALYSIS SUGGESTIONS:',
    '• For statistics: use \'distinct\' to count unique values',
    '• For large datasets: start with small limit, then increase',
    '• For geographic data: filter by City/Region first',
    '• For financial data: sort by Amount/Date fields',
    '',
    '🎪 SEMANTIC CONTEXTS FOR THIS TOOL:',
    '• Government transparency and open data analysis',
    '• Municipal budget tracking and spending analysis', 
    '• Business intelligence on Israeli market data',
    '• Demographics and population studies',
    '• Infrastructure and transportation planning',
    '• Financial services mapping and analysis'
  ].join('\n');

  return [mainContent, optimizationContent];
}