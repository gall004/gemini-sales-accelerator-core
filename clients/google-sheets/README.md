# Google Sheets Client — TTEC Digital AI Sales Accelerator

Google Sheets add-on for generating AI-powered sales briefings directly from a spreadsheet tracker.

## Quick Start

### 1. Set Up the Script

1. Open your Google Sheets sales tracker
2. Go to **Extensions → Apps Script**
3. Delete the default `Code.gs` file
4. Create the following files and paste the corresponding code:
   - `Code.gs` ← `src/Code.gs`
   - `ApiClient.gs` ← `src/ApiClient.gs`
   - `SheetReader.gs` ← `src/SheetReader.gs`
   - `Config.gs` ← `src/Config.gs`
   - `Utils.gs` ← `src/Utils.gs`
   - `views/briefing-sidebar.html` ← `views/briefing-sidebar.html`
   - `views/settings-dialog.html` ← `views/settings-dialog.html`
5. Copy the contents of `appsscript.json` into `appsscript.json` (View → Show manifest file)
6. Save all files and reload the spreadsheet

### 2. Configure the Connection

1. In Google Sheets, click **TTEC Digital → ⚙️ Settings**
2. Enter your **API Base URL** (e.g., `https://sales-accelerator-api-xxx.run.app`)
3. Enter your **API Key**
4. Enter your **Campaign / Product Focus** (e.g., "Google Actions Center Integrations for Event Ticketing")
5. Click **Save Settings**

### 3. Generate a Briefing

1. Highlight any row with lead data (must have a "Company Name" column)
2. Click **TTEC Digital → Generate AI Briefing**
3. The briefing sidebar opens with the AI-generated strategic analysis

## Expected Column Headers

The script reads column headers from Row 1. The following headers are recognized (case-insensitive):

| Field | Accepted Headers |
|---|---|
| Company Name (**required**) | `Company Name`, `Account Name`, `Company`, `Account`, `Name` |
| Website | `Website`, `URL`, `Company Website`, `Web` |
| Industry | `Industry`, `Vertical`, `Sector` |
| Type | `Type`, `Account Type`, `Lead Type` |
| Revenue | `Annual Revenue`, `Revenue`, `ARR` |
| Employees | `Employees`, `Number of Employees`, `Employee Count`, `Headcount` |
| Contact First | `Contact First Name`, `First Name`, `Contact First` |
| Contact Last | `Contact Last Name`, `Last Name`, `Contact Last` |
| Title | `Contact Title`, `Title`, `Job Title`, `Role` |
| Email | `Contact Email`, `Email`, `Email Address` |

Columns can be in any order. Extra columns are ignored.
