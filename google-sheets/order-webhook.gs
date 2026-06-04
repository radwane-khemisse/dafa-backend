const SHEET_NAME = PropertiesService.getScriptProperties().getProperty('ORDER_SHEET_NAME') || 'Orders Dafa Kitchen';
const HEADERS = [
  'OrderDate',
  'country',
  'name',
  'phone',
  'address',
  'url',
  'sku',
  'Product',
  'quantity',
  'price',
  'currency',
  'notes',
  'utm_source',
  'utm_medium',
  'utm_campaign',
  'utm_term',
  'utm_content',
  'national_address',
];
const MARKET_COUNTRIES = {
  ksa: 'Saudi Arabia',
  kwt: 'Kuwait',
  uae: 'UAE',
  qat: 'Qatar',
  bhr: 'Bahrain',
  omn: 'Oman',
};
const MARKET_CURRENCIES = {
  ksa: 'SAR',
  kwt: 'KWD',
  uae: 'AED',
  qat: 'QAR',
  bhr: 'BHD',
  omn: 'OMR',
};

function doPost(e) {
  try {
    const payload = JSON.parse(e.postData.contents);
    const order = payload.order || {};
    const sheet = getOrderSheet();
    ensureHeaders(sheet);

    const rows = getOrderItems(order).map((item) => buildLeadRow(order, item));
    appendOrderRows(sheet, rows);

    return jsonResponse({ ok: true, rows: rows.length });
  } catch (err) {
    return jsonResponse({ ok: false, error: String(err) });
  }
}

function buildLeadRow(order, item) {
  return [
    order.OrderDate || order.date || formatDate(new Date()),
    resolveCountry(order),
    order.name || order.customer_name || '',
    String(order.phone || order.phone_digits || order.phone_e164 || ''),
    order.address || '',
    order.url || order.source_url || order.landing_page || '',
    getItemSku(item, order),
    getItemProductName(item, order),
    String(getItemQuantity(item, order)),
    getItemPrice(item, order),
    normalizeCurrency(order),
    buildNotes(order, item),
    getClientValue(order, 'utm_source'),
    getClientValue(order, 'utm_medium'),
    getClientValue(order, 'utm_campaign'),
    getClientValue(order, 'utm_term'),
    getClientValue(order, 'utm_content'),
    order.national_address || '',
  ];
}

function getOrderItems(order) {
  if (Array.isArray(order.items) && order.items.length > 0) {
    return order.items;
  }

  const products = splitMultiValue(order.product || order.Product);
  const skus = splitMultiValue(order.sku);
  const quantities = splitMultiValue(order.quantity);
  const prices = splitMultiValue(order.price || order.totalprice || order.total_price);
  const itemCount = Math.max(products.length, skus.length, quantities.length, prices.length, 1);

  const items = [];
  for (let index = 0; index < itemCount; index += 1) {
    items.push({
      product: products[index] || products[0] || '',
      sku: skus[index] || skus[0] || '',
      quantity: quantities[index] || quantities[0] || '',
      total_price: prices[index] || prices[0] || 0,
    });
  }
  return items;
}

function splitMultiValue(value) {
  if (value === null || value === undefined || value === '') {
    return [];
  }
  return String(value)
    .split('/')
    .map((part) => part.trim())
    .filter(Boolean);
}

function getItemProductName(item, order) {
  return item.Product || item.product || item.title_ar || item.title || item.name || item.product_name || item.product_id || order.product || '';
}

function getItemSku(item, order) {
  return String(item.sku || item.product_sku || item.product_id || order.sku || '');
}

function getItemQuantity(item, order) {
  return item.quantity || item.qty || order.quantity || 1;
}

function getItemPrice(item, order) {
  return item.price || item.total_price || item.totalPrice || item.unit_price || item.unitPrice || order.price || order.totalprice || order.total_price || 0;
}

function buildNotes(order, item) {
  const notes = [];
  if (order.notes) {
    notes.push(order.notes);
  }
  if (isUpsellItem(order, item)) {
    notes.push('this is an upsell');
  }
  return notes.join(' | ');
}

function isUpsellItem(order, item) {
  const upsell = order.upsell || {};
  const acceptedUpsell = order.upsell_accepted === true || order.upsellAccepted === true || upsell.accepted === true;
  const offerId = String(item.offer_id || item.offerId || '').toLowerCase();
  const itemProductId = String(item.product_id || item.productId || '').toLowerCase();
  const upsellProductId = String(upsell.product_id || upsell.productId || order.upsell_product_id || order.upsellProductId || '').toLowerCase();

  return item.is_upsell === true
    || item.isUpsell === true
    || offerId.indexOf('upsell') !== -1
    || (acceptedUpsell && upsellProductId && itemProductId === upsellProductId);
}

function getClientValue(order, key) {
  const client = order.client || {};
  return order[key] || client[key] || '';
}

function normalizeCurrency(order) {
  const currency = String(order.currency || '').trim().toUpperCase();
  if (['SAR', 'KWD', 'AED', 'QAR', 'BHD', 'OMR'].indexOf(currency) !== -1) {
    return currency;
  }
  return MARKET_CURRENCIES[resolveMarketCode(order)] || 'SAR';
}

function resolveCountry(order) {
  if (order.country) {
    return String(order.country);
  }
  return MARKET_COUNTRIES[resolveMarketCode(order)] || 'Saudi Arabia';
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

  const currency = String(order.currency || '').trim().toUpperCase();
  if (currency === 'AED') return 'uae';
  if (currency === 'KWD' || currency === 'BHD') return inferDinarMarket(order);
  if (currency === 'QAR') return 'qat';
  if (currency === 'OMR') return 'omn';

  const phone = String(order.phone || order.phone_digits || order.phone_e164 || '').replace(/\D/g, '');
  if (phone.startsWith('965')) return 'kwt';
  if (phone.startsWith('971')) return 'uae';
  if (phone.startsWith('974')) return 'qat';
  if (phone.startsWith('973')) return 'bhr';
  if (phone.startsWith('968')) return 'omn';
  return 'ksa';
}

function inferDinarMarket(order) {
  const phone = String(order.phone || order.phone_digits || order.phone_e164 || '').replace(/\D/g, '');
  if (phone.startsWith('973')) return 'bhr';
  return 'kwt';
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

function appendOrderRows(sheet, rows) {
  if (rows.length === 0) {
    return;
  }

  const nextRow = sheet.getLastRow() + 1;
  sheet.getRange(nextRow, 4, rows.length, 1).setNumberFormat('@'); // phone
  sheet.getRange(nextRow, 7, rows.length, 1).setNumberFormat('@'); // sku
  sheet.getRange(nextRow, 9, rows.length, 1).setNumberFormat('@'); // quantity
  sheet.getRange(nextRow, 1, rows.length, HEADERS.length).setValues(rows);
}

function formatDate(date) {
  return Utilities.formatDate(date, 'Asia/Riyadh', 'dd/MM/yyyy');
}

function jsonResponse(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
