/**
 * Sheet Reader — Extracts lead data from the active spreadsheet.
 *
 * Uses header-based column detection (Row 1) so users can reorder or
 * add columns freely. Supports alternate header names for flexibility
 * across different team spreadsheet layouts.
 */

/** Header aliases — maps canonical field names to accepted column headers. */
var HEADER_ALIASES = {
  companyName:       ['company name', 'account name', 'client name', 'company', 'account', 'client', 'name'],
  website:           ['website', 'url', 'company website', 'web'],
  industry:          ['industry', 'vertical', 'sector'],
  type:              ['type', 'account type', 'lead type'],
  annualRevenue:     ['annual revenue', 'revenue', 'arr'],
  numberOfEmployees: ['employees', 'number of employees', 'employee count', 'headcount'],
  contactFirstName:  ['contact first name', 'first name', 'contact first'],
  contactLastName:   ['contact last name', 'last name', 'contact last'],
  contactTitle:      ['contact title', 'title', 'job title', 'role'],
  contactEmail:      ['contact email', 'email', 'email address'],
};

/**
 * Read the currently selected row and return structured lead data.
 *
 * @returns {Object|null} Lead data object, or null if header row or no selection.
 */
function readSelectedRow() {
  var sheet = SpreadsheetApp.getActiveSheet();
  var selection = sheet.getActiveRange();

  if (!selection) {
    return null;
  }

  var selectedRow = selection.getRow();
  if (selectedRow <= 1) {
    return null;
  }

  var headerRow = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  var headerMap = buildHeaderMap(headerRow);

  var dataRow = sheet.getRange(selectedRow, 1, 1, sheet.getLastColumn()).getValues()[0];

  return {
    rowNumber:          selectedRow,
    companyName:        getCellValue(dataRow, headerMap, 'companyName'),
    website:            getCellValue(dataRow, headerMap, 'website'),
    industry:           getCellValue(dataRow, headerMap, 'industry'),
    type:               getCellValue(dataRow, headerMap, 'type'),
    annualRevenue:      getCellValue(dataRow, headerMap, 'annualRevenue'),
    numberOfEmployees:  getCellValue(dataRow, headerMap, 'numberOfEmployees'),
    contactFirstName:   getCellValue(dataRow, headerMap, 'contactFirstName'),
    contactLastName:    getCellValue(dataRow, headerMap, 'contactLastName'),
    contactTitle:       getCellValue(dataRow, headerMap, 'contactTitle'),
    contactEmail:       getCellValue(dataRow, headerMap, 'contactEmail'),
  };
}

/**
 * Build the API request payload from extracted row data.
 *
 * @param {Object} rowData - Output from readSelectedRow().
 * @returns {Object} Payload matching the BriefingGenerateRequest schema.
 */
function buildApiPayload(rowData) {
  var payload = {
    entity_type: 'account',
    account: {
      name: safeString(rowData.companyName),
      website: safeString(rowData.website),
      industry: safeString(rowData.industry),
      type: safeString(rowData.type),
      annual_revenue: safeNumber(rowData.annualRevenue),
      number_of_employees: safeNumber(rowData.numberOfEmployees),
    },
    source_system: 'google_sheets',
    external_id: 'row_' + rowData.rowNumber,
    force_refresh: false,
  };

  var campaignContext = getCampaignContext();
  if (campaignContext) {
    payload.campaign_context = campaignContext;
  }

  if (rowData.contactLastName && safeString(rowData.contactLastName)) {
    payload.contact = {
      first_name: safeString(rowData.contactFirstName),
      last_name: safeString(rowData.contactLastName),
      title: safeString(rowData.contactTitle),
      email: safeString(rowData.contactEmail),
    };
  }

  return payload;
}

/**
 * Build a map from canonical field names to column indexes.
 *
 * @param {Array} headerRow - Array of header cell values from Row 1.
 * @returns {Object} Map of { fieldName: columnIndex }.
 */
function buildHeaderMap(headerRow) {
  var map = {};

  for (var col = 0; col < headerRow.length; col++) {
    var header = String(headerRow[col]).trim().toLowerCase();
    if (!header) continue;

    for (var field in HEADER_ALIASES) {
      if (map[field] !== undefined) continue;
      var aliases = HEADER_ALIASES[field];
      for (var a = 0; a < aliases.length; a++) {
        if (header === aliases[a]) {
          map[field] = col;
          break;
        }
      }
    }
  }

  return map;
}

/**
 * Safely extract a cell value using the header map.
 *
 * @param {Array} dataRow - Row data array.
 * @param {Object} headerMap - Output from buildHeaderMap().
 * @param {string} fieldName - Canonical field name.
 * @returns {*} Cell value or null if column not found.
 */
function getCellValue(dataRow, headerMap, fieldName) {
  if (headerMap[fieldName] === undefined) {
    return null;
  }
  var value = dataRow[headerMap[fieldName]];
  return (value === '' || value === undefined) ? null : value;
}
