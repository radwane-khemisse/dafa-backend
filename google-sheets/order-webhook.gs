const SHEET_NAME = PropertiesService.getScriptProperties().getProperty('ORDER_SHEET_NAME') || 'Orders Dafa Kitchen';
const HEADERS = ['date', 'orderId', 'country', 'name', 'phone', 'product', 'sku', 'quantity', 'totalprice', 'currency', 'status'];

function doPost(e) {
  try {
    const payload = JSON.parse(e.postData.contents);
    const order = payload.order || {};
    const sheet = getOrderSheet();
    ensureHeaders(sheet);

    const row = [
      order.date || formatDate(new Date()),
      order.orderId || '',
      order.country || 'KSA',
      order.name || '',
      String(order.phone || ''),
      order.product || '',
      order.sku || '',
      String(order.quantity || ''),
      order.totalprice || 0,
      order.currency || 'SAR',
      order.status || ''
    ];

    appendOrderRow(sheet, row);

    return jsonResponse({ ok: true });
  } catch (err) {
    return jsonResponse({ ok: false, error: String(err) });
  }
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
