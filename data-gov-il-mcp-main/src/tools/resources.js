/**
 * כלי list_resources - מביא resources עבור dataset ספציפי
 */

import { z } from 'zod';
import { getDatasetInfo } from '../utils/api.js';
import { formatResourcesList, createErrorResponse } from '../utils/formatters.js';
import { EXAMPLE_RESOURCE_IDS } from '../config/constants.js';
import { TROUBLESHOOTING } from '../lib/guidance.js';

/**
 * רישום הכלי במערכת MCP
 * @param {McpServer} mcp - שרת MCP
 */
export function registerListResourcesTool(mcp) {
  mcp.tool(
    "list_resources",
    { 
      dataset: z.string().describe("Dataset ID or name (e.g., 'branches', 'jerusalem-municipality-budget')"),
      include_tracking: z.boolean().optional().describe("Include version tracking and update history")
    },
    async ({ dataset, include_tracking }) => {
      try {
        console.error(`🔍 Fetching resources for dataset: ${dataset}...`);
        
        const response = await getDatasetInfo(dataset, include_tracking);
        const resources = response.result.resources;
        
        console.error(`✅ Retrieved ${resources.length} resources for dataset '${dataset}'`);
        
        const contentBlocks = formatResourcesList(
          dataset, 
          resources, 
          EXAMPLE_RESOURCE_IDS
        );
        
        return {
          content: contentBlocks.map(block => ({
            type: "text",
            text: block
          }))
        };
        
      } catch (error) {
        console.error(`❌ Error in list_resources for dataset ${dataset}:`, error.message);
        
        return createErrorResponse(
          `list_resources for dataset '${dataset}'`,
          error,
          TROUBLESHOOTING.datasets
        );
      }
    }
  );
}