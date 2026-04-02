/**
 * Config — Secure settings management via PropertiesService.
 *
 * All configuration (API key, base URL, campaign context) is stored in
 * Script Properties — NEVER hardcoded in the codebase.
 */

var PROP_API_KEY          = 'TTEC_API_KEY';
var PROP_BASE_URL         = 'TTEC_BASE_URL';
var PROP_CAMPAIGN_CONTEXT = 'TTEC_CAMPAIGN_CONTEXT';

/**
 * Retrieve all settings from Script Properties.
 *
 * @returns {Object} { apiKey, baseUrl, campaignContext }
 */
function getSettings() {
  var props = PropertiesService.getScriptProperties();
  return {
    apiKey:          props.getProperty(PROP_API_KEY) || '',
    baseUrl:         props.getProperty(PROP_BASE_URL) || '',
    campaignContext: props.getProperty(PROP_CAMPAIGN_CONTEXT) || '',
  };
}

/**
 * Save all settings to Script Properties.
 * Called from the settings-dialog.html via google.script.run.
 *
 * @param {Object} settings - { apiKey, baseUrl, campaignContext }
 */
function saveSettings(settings) {
  var props = PropertiesService.getScriptProperties();
  props.setProperty(PROP_API_KEY, settings.apiKey || '');
  props.setProperty(PROP_BASE_URL, settings.baseUrl || '');
  props.setProperty(PROP_CAMPAIGN_CONTEXT, settings.campaignContext || '');
}

/** @returns {string} The configured API base URL. */
function getBaseUrl() {
  return PropertiesService.getScriptProperties().getProperty(PROP_BASE_URL) || '';
}

/** @returns {string} The configured API key. */
function getApiKey() {
  return PropertiesService.getScriptProperties().getProperty(PROP_API_KEY) || '';
}

/** @returns {string} The configured campaign/product focus. */
function getCampaignContext() {
  return PropertiesService.getScriptProperties().getProperty(PROP_CAMPAIGN_CONTEXT) || '';
}
