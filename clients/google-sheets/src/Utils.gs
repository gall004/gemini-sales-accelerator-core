/**
 * Utils — Shared utility functions.
 *
 * Toast notifications, safe type coercion, and formatting helpers
 * used across the add-on.
 */

/**
 * Show a toast notification in the spreadsheet.
 *
 * @param {string} message - The notification message.
 * @param {string} [title] - Optional title for the toast.
 */
function showToast(message, title) {
  SpreadsheetApp.getActiveSpreadsheet().toast(message, title || 'TTEC Digital', 5);
}

/**
 * Safely coerce a value to a trimmed string, or return null.
 *
 * @param {*} value - The input value.
 * @returns {string|null} Trimmed string or null if empty/undefined.
 */
function safeString(value) {
  if (value === null || value === undefined || value === '') {
    return null;
  }
  return String(value).trim();
}

/**
 * Safely coerce a value to a number, or return null.
 * Strips currency symbols, commas, and whitespace before parsing.
 *
 * @param {*} value - The input value.
 * @returns {number|null} Parsed number or null if not numeric.
 */
function safeNumber(value) {
  if (value === null || value === undefined || value === '') {
    return null;
  }
  if (typeof value === 'number') {
    return value;
  }
  var cleaned = String(value).replace(/[$,\s]/g, '');
  var parsed = Number(cleaned);
  return isNaN(parsed) ? null : parsed;
}
