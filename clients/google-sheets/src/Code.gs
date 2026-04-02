/**
 * TTEC Digital — AI Sales Accelerator Client
 *
 * Entry point for the Google Sheets add-on. Registers the custom menu
 * and orchestrates the briefing generation flow.
 *
 * This file is a thin orchestration layer — business logic lives in
 * ApiClient.gs, SheetReader.gs, and Config.gs.
 */

/**
 * Creates the TTEC Digital menu when the spreadsheet opens.
 * Uses a simple trigger — no additional authorization required.
 */
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('TTEC Digital')
    .addItem('Generate AI Briefing', 'onGenerateBriefing')
    .addSeparator()
    .addItem('⚙️ Settings', 'showSettingsDialog')
    .addToUi();
}

/**
 * Main briefing generation handler. Reads the selected row,
 * validates the data, and opens the sidebar with results.
 */
function onGenerateBriefing() {
  var rowData = readSelectedRow();

  if (!rowData) {
    showToast('Please select a data row (not the header).', '⚠️ No Row Selected');
    return;
  }

  if (!rowData.companyName || rowData.companyName.trim() === '') {
    showToast('The selected row has no Company Name.', '⚠️ Missing Data');
    return;
  }

  var settings = getSettings();
  if (!settings.baseUrl || !settings.apiKey) {
    showToast(
      'Please configure your API connection in TTEC Digital → ⚙️ Settings.',
      '⚠️ Not Configured'
    );
    return;
  }

  var sidebar = HtmlService.createHtmlOutputFromFile('views/briefing-sidebar')
    .setTitle('AI Sales Accelerator')
    .setWidth(420);
  SpreadsheetApp.getUi().showSidebar(sidebar);
}

/**
 * Opens the Settings dialog for API configuration.
 */
function showSettingsDialog() {
  var html = HtmlService.createHtmlOutputFromFile('views/settings-dialog')
    .setWidth(440)
    .setHeight(340);
  SpreadsheetApp.getUi().showModalDialog(html, 'TTEC Digital — Settings');
}

/**
 * Server-side function called by the sidebar to fetch the briefing.
 * Invoked via google.script.run from the client-side HTML.
 *
 * @returns {Object} The API response payload or an error object.
 */
function fetchBriefingForSidebar() {
  var rowData = readSelectedRow();
  if (!rowData || !rowData.companyName) {
    return { error: true, message: 'No company data found in the selected row.' };
  }

  var payload = buildApiPayload(rowData);
  return generateBriefing(payload);
}

/**
 * Server-side function called by the sidebar to force-refresh
 * the briefing (bypasses cache).
 *
 * @returns {Object} The API response payload or an error object.
 */
function forceRefreshBriefing() {
  var rowData = readSelectedRow();
  if (!rowData || !rowData.companyName) {
    return { error: true, message: 'No company data found in the selected row.' };
  }

  var payload = buildApiPayload(rowData);
  payload.force_refresh = true;
  return generateBriefing(payload);
}
