/**
 * Utility functions for converting technical errors to user-friendly messages in Hebrew
 */

/**
 * Converts technical error messages to user-friendly Hebrew messages
 * 
 * @param error - Error object, string, or ApiResponse with error
 * @returns User-friendly error message in Hebrew
 */
export function getUserFriendlyError(error: Error | string | { error?: string; status?: number } | unknown): string {
  // Handle ApiResponse objects
  if (error && typeof error === 'object' && 'error' in error) {
    const apiError = error as { error?: string; status?: number };
    if (apiError.error) {
      return getUserFriendlyError(apiError.error);
    }
    if (apiError.status) {
      return getUserFriendlyError(new Error(`HTTP ${apiError.status}`));
    }
  }

  // Convert to string for processing
  let errorMessage = '';
  let statusCode: number | null = null;

  if (error instanceof Error) {
    errorMessage = error.message;
    // Try to extract status code from error message
    const statusMatch = errorMessage.match(/\b(40[0-9]|50[0-9])\b/);
    if (statusMatch) {
      statusCode = parseInt(statusMatch[0], 10);
    }
  } else if (typeof error === 'string') {
    errorMessage = error;
    const statusMatch = errorMessage.match(/\b(40[0-9]|50[0-9])\b/);
    if (statusMatch) {
      statusCode = parseInt(statusMatch[0], 10);
    }
  } else {
    return 'אירעה שגיאה. אנא נסה שוב.';
  }

  const lowerMessage = errorMessage.toLowerCase();

  // Handle HTTP status codes
  if (statusCode) {
    switch (statusCode) {
      case 401:
        return 'פג תוקף ההתחברות. אנא התחבר שוב.';
      case 403:
        return 'אין לך הרשאה לבצע פעולה זו.';
      case 404:
        return 'המשאב המבוקש לא נמצא.';
      case 429:
        return 'השירות עמוס כרגע. אנא נסה שוב בעוד כמה דקות.';
      case 500:
      case 502:
      case 503:
      case 504:
        return 'שגיאת שרת. אנא נסה שוב בעוד כמה רגעים.';
      case 400:
        return 'בקשה לא תקינה. אנא בדוק את הנתונים ונסה שוב.';
      default:
        if (statusCode >= 500) {
          return 'שגיאת שרת. אנא נסה שוב בעוד כמה רגעים.';
        }
        if (statusCode >= 400) {
          return 'אירעה שגיאה. אנא נסה שוב.';
        }
    }
  }

  // Handle network errors
  if (
    lowerMessage.includes('network') ||
    lowerMessage.includes('fetch') ||
    lowerMessage.includes('failed to fetch') ||
    lowerMessage.includes('networkerror') ||
    lowerMessage.includes('network request failed')
  ) {
    return 'בעיית חיבור לאינטרנט. אנא בדוק את החיבור שלך.';
  }

  // Handle timeout errors
  if (
    lowerMessage.includes('timeout') ||
    lowerMessage.includes('timed out') ||
    lowerMessage.includes('aborted')
  ) {
    return 'הבקשה ארכה יותר מדי זמן. אנא נסה שוב.';
  }

  // Handle authentication errors
  if (
    lowerMessage.includes('authentication') ||
    lowerMessage.includes('unauthorized') ||
    lowerMessage.includes('session expired') ||
    lowerMessage.includes('token')
  ) {
    return 'פג תוקף ההתחברות. אנא התחבר שוב.';
  }

  // Handle rate limit errors
  if (lowerMessage.includes('rate limit') || lowerMessage.includes('too many requests')) {
    return 'השירות עמוס כרגע. אנא נסה שוב בעוד כמה דקות.';
  }

  // Handle parse errors
  if (lowerMessage.includes('parse') || lowerMessage.includes('json')) {
    return 'שגיאה בעיבוד הנתונים. אנא נסה שוב.';
  }

  // Default fallback
  return 'אירעה שגיאה. אנא נסה שוב.';
}

/**
 * Gets a user-friendly error message from an ApiResponse error
 * 
 * @param response - ApiResponse object with error
 * @returns User-friendly error message in Hebrew
 */
export function getApiError(response: { error?: string; status?: number }): string {
  return getUserFriendlyError(response);
}

