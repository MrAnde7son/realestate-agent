/**
 * כלי list_organizations - ניהול וחיפוש ארגונים ממשלתיים
 */

import { z } from 'zod';
import { ckanRequest } from '../utils/api.js';
import { createErrorResponse } from '../utils/formatters.js';

/**
 * מפרמט רשימת ארגונים
 * @param {Array} organizations - רשימת ארגונים (שמות בלבד)
 * @returns {Array} בלוקי תוכן מפורמטים
 */
function formatOrganizationsList(organizations) {
  const orgCount = organizations.length;

  const mainContent = [
    `🏛️ Found ${orgCount} government organizations`,
    '',
    '📋 Organizations list:',
    JSON.stringify(organizations, null, 2)
  ].join('\n');

  const guidanceContent = [
    '💡 WORKING WITH ORGANIZATIONS:',
    '',
    '🔍 NEXT STEPS:',
    '• Use get_organization_info with organization name for details',
    '• Organization names are usually in English (lowercase)',
    '• Example: get_organization_info("ministry-of-health")',
    '',
    '📊 ANALYSIS OPTIONS:',
    '• Find datasets by organization using find_datasets',
    '• Filter search results by organization',
    '• Compare data coverage across ministries',
    '',
    '🏢 ORGANIZATION CATEGORIES:',
    '• Government Ministries (משרדי ממשלה)',
    '• Local Authorities (רשויות מקומיות)', 
    '• Public Companies (חברות ממשלתיות)',
    '• Regulatory Bodies (גופי פיקוח)',
    '',
    '🎯 COMMON USE CASES:',
    '• Research government transparency by ministry',
    '• Find all health-related datasets from Ministry of Health',
    '• Compare municipal data across different cities',
    '• Track data publication frequency by organization'
  ].join('\n');

  return [mainContent, guidanceContent];
}

/**
 * מפרמט מידע מפורט על ארגון
 * @param {Object} organization - נתוני הארגון
 * @returns {Array} בלוקי תוכן מפורמטים
 */
function formatOrganizationInfo(organization) {
  const basicInfo = [
    `🏛️ Organization: ${organization.title || organization.display_name || organization.name}`,
    '',
    `📝 Name: ${organization.name}`,
    `🌐 Type: ${organization.type || 'Government'}`,
    `📅 Created: ${organization.created ? new Date(organization.created).toLocaleDateString() : 'N/A'}`,
    `👥 Followers: ${organization.num_followers || 0}`,
    `⭐ State: ${organization.state || 'N/A'}`,
    '',
    `📄 Description:`,
    organization.description || organization.notes || 'No description available'
  ].join('\n');

  const technicalInfo = [
    '🔧 TECHNICAL INFO:',
    '',
    `📋 ID: ${organization.id}`,
    `🖼️ Image URL: ${organization.image_url || 'None'}`,
    `🔗 Image Display URL: ${organization.image_display_url || 'None'}`,
    `📊 Is Organization: ${organization.is_organization}`,
    `✅ Approval Status: ${organization.approval_status || 'N/A'}`,
    '',
    '👥 USERS:',
    organization.users && organization.users.length > 0 
      ? organization.users.map(user => `• ${user.display_name || user.name} (${user.capacity})`).join('\n')
      : '• No users information available',
    '',
    '🔗 EXTRAS:',
    organization.extras && organization.extras.length > 0
      ? organization.extras.map(extra => `• ${extra.key}: ${extra.value}`).join('\n')
      : '• No extra information available'
  ].join('\n');

  const usageGuidance = [
    '💡 EXPLORE THIS ORGANIZATION:',
    '',
    '🔍 FIND DATASETS:',
    `• find_datasets with organization-related keywords`,
    `• Search by organization domain or type`,
    '',
    '📊 ANALYZE DATA:',
    '• Use find_datasets to discover this organization\'s datasets',
    '• Look for patterns in data publication',
    '• Compare with other similar organizations',
    '',
    '🎯 RESEARCH OPPORTUNITIES:',
    '• Government transparency analysis',
    '• Data publication trends over time', 
    '• Cross-ministry data correlation',
    '• Public data accessibility assessment'
  ].join('\n');

  return [basicInfo, technicalInfo, usageGuidance];
}

/**
 * רישום הכלים במערכת MCP
 * @param {McpServer} mcp - שרת MCP
 */
export function registerOrganizationTools(mcp) {
  // כלי לרשימת כל הארגונים
  mcp.tool(
    "list_organizations",
    {},
    async () => {
      try {
        console.error('🏛️ Fetching organizations list from data.gov.il...');
        
        const response = await ckanRequest('organization_list');
        
        const organizations = response.result;
        console.error(`✅ Retrieved ${organizations.length} organizations`);
        
        const contentBlocks = formatOrganizationsList(organizations);
        
        return {
          content: contentBlocks.map(block => ({
            type: "text",
            text: block
          }))
        };
        
      } catch (error) {
        console.error('❌ Error in list_organizations:', error.message);
        
        return createErrorResponse(
          'list_organizations',
          error,
          [
            'Check your internet connection',
            'The government API might be temporarily unavailable',
            'Try again in a moment'
          ]
        );
      }
    }
  );

  // כלי למידע מפורט על ארגון ספציפי
  mcp.tool(
    "get_organization_info",
    {
      organization: z.string().describe("Organization name or ID. Examples: 'ministry-of-health', 'tel-aviv-yafo', 'cbs'. Use list_organizations to see all available organizations")
    },
    async ({ organization }) => {
      try {
        console.error(`🏛️ Getting detailed info for organization: ${organization}...`);
        
        const response = await ckanRequest('organization_show', { 
          id: organization
        });
        
        const orgInfo = response.result;
        console.error(`✅ Retrieved detailed info for organization '${organization}'`);
        
        const contentBlocks = formatOrganizationInfo(orgInfo);
        
        return {
          content: contentBlocks.map(block => ({
            type: "text",
            text: block
          }))
        };
        
      } catch (error) {
        console.error(`❌ Error in get_organization_info for organization ${organization}:`, error.message);
        
        return createErrorResponse(
          `get_organization_info for organization '${organization}'`,
          error,
          [
            'Check if organization name is correct',
            'Use list_organizations to see all available organizations', 
            'Organization names are usually in English and lowercase',
            'Try variations like "ministry-of-health" or "health"',
            'Some organizations may use Hebrew names'
          ]
        );
      }
    }
  );
}