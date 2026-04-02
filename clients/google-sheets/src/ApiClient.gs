/**
 * API Client — HTTP communication with the Core API.
 *
 * Constructs and sends requests to the TTEC Digital Sales Accelerator
 * Core API. Reads API key and base URL from PropertiesService — never
 * hardcoded.
 */

/**
 * Send a briefing generation request to the Core API.
 *
 * @param {Object} payload - The request body matching BriefingGenerateRequest schema.
 * @returns {Object} Parsed API response or an error object.
 */
function generateBriefing(payload) {
  var settings = getSettings();

  if (!settings.baseUrl || !settings.apiKey) {
    return {
      error: true,
      message: 'API connection not configured. Go to TTEC Digital → ⚙️ Settings.',
    };
  }

  var url = settings.baseUrl.replace(/\/+$/, '') + '/api/v1/briefings/generate';

  var options = {
    method: 'post',
    contentType: 'application/json',
    headers: {
      'X-API-Key': settings.apiKey,
    },
    payload: JSON.stringify(payload),
    muteHttpExceptions: true,
  };

  try {
    var response = UrlFetchApp.fetch(url, options);
    var statusCode = response.getResponseCode();
    var body = response.getContentText();

    if (statusCode >= 200 && statusCode < 300) {
      return JSON.parse(body);
    }

    var errorDetail = 'Unknown error';
    try {
      var parsed = JSON.parse(body);
      errorDetail = parsed.detail || JSON.stringify(parsed);
    } catch (e) {
      errorDetail = body.substring(0, 500);
    }

    return {
      error: true,
      message: 'API returned ' + statusCode + ': ' + errorDetail,
    };
  } catch (e) {
    return {
      error: true,
      message: 'Connection failed: ' + e.message,
    };
  }
}
