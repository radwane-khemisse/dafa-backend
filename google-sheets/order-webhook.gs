const SHEET_NAME = PropertiesService.getScriptProperties().getProperty('ORDER_SHEET_NAME') || 'Orders Dafa Kitchen';
const HEADERS = ['date', 'orderId', 'country', 'name', 'phone', 'product', 'sku', 'quantity', 'totalprice', 'currency', 'status'];
const MARKET_COUNTRIES = {
  ksa: 'KSA',
  kwt: 'KWT',
  uae: 'UAE',
  qat: 'QAT',
  bhr: 'BHR',
  omn: 'OMN',
};
const MARKET_CURRENCIES = {
  ksa: 'ريال',
  kwt: 'دينار',
  uae: 'درهم',
  qat: 'ريال',
  bhr: 'دينار',
  omn: 'ريال',
};

function doPost(e) {
  try {
    const payload = JSON.parse(e.postData.contents);
    const order = payload.order || {};
    const sheet = getOrderSheet();
    ensureHeaders(sheet);

    const row = [
      order.date || formatDate(new Date()),
      order.orderId || '',
      resolveCountry(order),
      order.name || '',
      String(order.phone || ''),
      order.product || '',
      order.sku || '',
      String(order.quantity || ''),
      order.totalprice || 0,
      order.currency || MARKET_CURRENCIES[resolveMarketCode(order)] || 'ريال',
      order.status || ''
    ];

    appendOrderRow(sheet, row);

    return jsonResponse({ ok: true });
  } catch (err) {
    return jsonResponse({ ok: false, error: String(err) });
  }
}

function resolveCountry(order) {
  if (order.country) {
    return String(order.country).toUpperCase();
  }
  return MARKET_COUNTRIES[resolveMarketCode(order)] || 'KSA';
}

function resolveMarketCode(order) {
  const explicitMarket = String(order.market_code || order.marketCode || '').toLowerCase();
  if (MARKET_COUNTRIES[explicitMarket]) {
    return explicitMarket;
  }

  const source = String(order.source_url || order.landing_page || order.url || '').toLowerCase();
  const pathMatch = source.match(/\/(ksa|kwt|uae|qat|bhr|omn)(\/|$)/);
  if (pathMatch) {
    return pathMatch[1];
  }

  const currency = String(order.currency || '').trim();
  if (currency === 'درهم') return 'uae';
  if (currency === 'دينار') return inferDinarMarket(order);

  const phone = String(order.phone || '').replace(/\D/g, '');
  if (phone.startsWith('965')) return 'kwt';
  if (phone.startsWith('971')) return 'uae';
  if (phone.startsWith('974')) return 'qat';
  if (phone.startsWith('973')) return 'bhr';
  if (phone.startsWith('968')) return 'omn';
  return 'ksa';
}

function inferDinarMarket(order) {
  const phone = String(order.phone || '').replace(/\D/g, '');
  if (phone.startsWith('973')) return 'bhr';
  return 'kwt';
}

function jsonResponse(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

function ensureHeaders(sheet) {
  if (!sheet) {
    throw new Error(`Sheet not found: ${SHEET_NAME}`);
  }

  const currentHeaders = sheet.getRange(1, 1, 1, HEADERS.length).getValues()[0];
  const hasHeaders = HEADERS.every((header, index) => currentHeaders[index] === header);
  if (!hasHeaders) {
    sheet.getRange(1, 1, 1, HEADERS.length).setValues([HEADERS]);
  }
}

function getOrderSheet() {
  const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  return spreadsheet.getSheetByName(SHEET_NAME)
    || spreadsheet.getSheetByName('Orders')
    || spreadsheet.getSheetByName('Feuille 1')
    || spreadsheet.getActiveSheet();
}

function appendOrderRow(sheet, row) {
  const nextRow = sheet.getLastRow() + 1;
  sheet.getRange(nextRow, 5).setNumberFormat('@'); // phone
  sheet.getRange(nextRow, 7).setNumberFormat('@'); // sku
  sheet.getRange(nextRow, 8).setNumberFormat('@'); // quantity, e.g. 2/1/1
  sheet.getRange(nextRow, 1, 1, HEADERS.length).setValues([row]);
}

function formatDate(date) {
  return Utilities.formatDate(date, 'Asia/Riyadh', 'dd/MM/yyyy');
}
