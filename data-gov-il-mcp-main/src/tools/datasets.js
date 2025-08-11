/**
 * כלי list_all_datasets - מביא רשימת כל הdatasets (יקר!)
 */

import { getDatasetsList } from '../utils/api.js';
import { formatDatasetsList, createErrorResponse } from '../utils/formatters.js';
import { POPULAR_DATASETS } from '../config/constants.js';
import { TROUBLESHOOTING } from '../lib/guidance.js';

/**
 * רישום הכלי במערכת MCP
 * @param {McpServer} mcp - שרת MCP
 */
export function registerListAllDatasetsTool(mcp) {
  mcp.tool("list_all_datasets", {}, async () => {
    try {
      console.error('⚠️ EXPENSIVE: Fetching ALL datasets list from data.gov.il...');
      
      const response = await getDatasetsList();
      const datasets = response.result;
      
      console.error(`✅ Retrieved ${datasets.length} datasets (consider using find_datasets for search)`);
      
      const contentBlocks = formatDatasetsList(datasets, POPULAR_DATASETS);
      
      return {
        content: contentBlocks.map(block => ({
          type: "text",
          text: block
        }))
      };
      
    } catch (error) {
      console.error('❌ Error in list_all_datasets:', error.message);
      
      return createErrorResponse(
        'list_all_datasets',
        error,
        TROUBLESHOOTING.api
      );
    }
  });
}