// Helpers for turning the backend's product rows into display-ready parts.

const APPLIANCE_WORDS = /\b(refrigerator|dishwasher|freezer)\b/i;

const priceFormat = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
});

function parseJson(value, fallback) {
  if (value && typeof value === 'object') return value;
  if (typeof value !== 'string') return fallback;
  try {
    return JSON.parse(value);
  } catch {
    return fallback;
  }
}

// Catalog names look like "Admiral Refrigerator Ice Maker" or
// "Blomberg Refrigerator Svc-board Electronic Control;4918670200".
// Keep the part itself: drop the leading brand + appliance and any ";code" suffix.
export function cleanPartName(name = '') {
  const withoutCode = name.split(';')[0].trim();
  const match = withoutCode.match(APPLIANCE_WORDS);
  if (!match) return withoutCode;
  const rest = withoutCode.slice(match.index + match[0].length).trim();
  return rest || withoutCode;
}

// Search results carry `specifications` as a JSON string and `price` as a
// string; direct lookups return them parsed. Normalise both shapes.
export function normalizePart(raw) {
  const specs = parseJson(raw.specifications, {}) || {};
  return {
    partNumber: raw.part_number,
    name: raw.name,
    title: cleanPartName(raw.name),
    brand: raw.brand || null,
    category: raw.category || null,
    price: Number(raw.price),
    inStock: Boolean(raw.in_stock),
    mpn: specs.mpn || null,
    fixes: Array.isArray(specs.symptoms) ? specs.symptoms : [],
    replaces: Array.isArray(specs.replace_parts) ? specs.replace_parts : [],
    url: specs.product_url || null,
  };
}

export function formatPrice(value) {
  return Number.isFinite(value) ? priceFormat.format(value) : '';
}

export function youtubeId(url) {
  if (!url) return null;
  const match = url.match(/(?:v=|youtu\.be\/|embed\/)([\w-]{11})/);
  return match ? match[1] : null;
}

export function capitalize(text = '') {
  return text ? text.charAt(0).toUpperCase() + text.slice(1) : '';
}
