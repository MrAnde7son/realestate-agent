import axios from 'axios';
import { CKAN_BASE_URL, DEFAULT_TIMEOUT, SEARCH_TIMEOUT, USER_AGENT } from '../config/constants.js';

/**
 * יוצר בקשת HTTP מותאמת אישית ל-CKAN API
 * @param {string} endpoint - נקודת הקצה (package_list, package_show, datastore_search)
 * @param {Object} params - פרמטרים לשאילתה
 * @param {number} timeout - זמן המתנה מקסימלי
 * @returns {Promise<Object>} תגובת CKAN
 */
export async function ckanRequest(endpoint, params = {}, timeout = DEFAULT_TIMEOUT) {
  try {
    const url = `${CKAN_BASE_URL}/${endpoint}`;
    
    console.error(`🌐 API Call: ${url}`);
    console.error(`📝 Params:`, JSON.stringify(params, null, 2));

    // הוספת לוג של ה-URL המלא שנשלח
    const testUrl = new URL(url);
    Object.keys(params).forEach(key => {
      testUrl.searchParams.append(key, params[key]);
    });
    console.error(`🔗 Full URL: ${testUrl.toString()}`);

    const response = await axios.get(url, {
      params,
      timeout,
      headers: {
        'User-Agent': USER_AGENT
      }
    });

    // בדיקת תקינות תגובת CKAN
    if (!response.data || !response.data.success) {
      throw new Error('CKAN API returned unsuccessful response');
    }

    return response.data;
  } catch (error) {
    // טיפול משופר בשגיאות
    if (error.code === 'ECONNABORTED') {
      throw new Error(`Request timeout after ${timeout}ms`);
    }
    
    if (error.response) {
      throw new Error(`CKAN API error (${error.response.status}): ${error.response.statusText}`);
    }
    
    if (error.request) {
      throw new Error('Unable to reach data.gov.il API - check internet connection');
    }
    
    throw error;
  }
}

/**
 * בקשת רשימת datasets
 */
export async function getDatasetsList() {
  return ckanRequest('package_list');
}

/**
 * בקשת פרטי dataset ו-resources
 */
export async function getDatasetInfo(datasetId, includeTracking = false) {
  const params = { id: datasetId };
  if (includeTracking) {
    params.include_tracking = 'true';
  }
  return ckanRequest('package_show', params);
}

/**
 * חיפוש records במשאב
 */
export async function searchRecords(resourceId, searchParams = {}) {
  const params = { 
    resource_id: resourceId,
    ...searchParams 
  };
  
  // הכנת פרמטרים מיוחדים
  if (params.filters && typeof params.filters === 'object') {
    params.filters = JSON.stringify(params.filters);
  }
  
  if (params.fields && Array.isArray(params.fields)) {
    params.fields = params.fields.join(',');
  }
  
  if (params.sort && Array.isArray(params.sort)) {
    params.sort = params.sort.join(',');
  }
  
  if (params.include_total) {
    params.include_total = 'true';
  }
  
  return ckanRequest('datastore_search', params, SEARCH_TIMEOUT);
}