/**
 * ShopStream Timezone Utilities
 *
 * Handles timezone conversions for Charlotte, NC (Eastern Time)
 */

// Charlotte, NC is in Eastern Time Zone
const TIMEZONE = 'America/New_York';
const LOCATION = 'Charlotte, NC';

/**
 * Convert UTC date to Eastern Time
 * @param {Date|string} date - UTC date/timestamp
 * @returns {Date} - Date in Eastern Time
 */
export function toEasternTime(date) {
  if (!date) return null;

  const utcDate = typeof date === 'string' ? new Date(date) : date;

  // Get the UTC timestamp
  const utcTimestamp = utcDate.getTime();

  // Create formatter for Eastern Time
  const formatter = new Intl.DateTimeFormat('en-US', {
    timeZone: TIMEZONE,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  });

  const parts = formatter.formatToParts(new Date(utcTimestamp));
  const year = parts.find(p => p.type === 'year').value;
  const month = parts.find(p => p.type === 'month').value;
  const day = parts.find(p => p.type === 'day').value;
  const hour = parts.find(p => p.type === 'hour').value;
  const minute = parts.find(p => p.type === 'minute').value;
  const second = parts.find(p => p.type === 'second').value;

  return new Date(`${year}-${month}-${day}T${hour}:${minute}:${second}`);
}

/**
 * Format timestamp for display with timezone
 * @param {Date|string} date - UTC date/timestamp
 * @returns {string} - Formatted time string
 */
export function formatTimestamp(date) {
  if (!date) return '';

  // Create a UTC date object
  const utcDate = typeof date === 'string' ? new Date(date) : new Date(date);

  // Format using Intl with Eastern Time zone
  const formatter = new Intl.DateTimeFormat('en-US', {
    timeZone: TIMEZONE,
    hour: 'numeric',
    minute: '2-digit',
    second: '2-digit',
    hour12: true
  });

  return formatter.format(utcDate) + ' ET';
}

/**
 * Format timestamp with full details including location
 * @param {Date|string} date - UTC date/timestamp
 * @returns {string} - Formatted time string with location
 */
export function formatTimestampWithLocation(date) {
  if (!date) return '';

  const options = {
    timeZone: TIMEZONE,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: true
  };

  const timeString = new Date(date).toLocaleTimeString('en-US', options);
  return `${timeString} ET (${LOCATION})`;
}

/**
 * Format date and time for display
 * @param {Date|string} date - UTC date/timestamp
 * @returns {string} - Formatted date and time string
 */
export function formatDateTime(date) {
  if (!date) return '';

  const options = {
    timeZone: TIMEZONE,
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: true
  };

  return new Date(date).toLocaleString('en-US', options) + ' ET';
}

/**
 * Format time for chart labels (short format)
 * @param {Date|string} date - UTC date/timestamp
 * @returns {string} - Formatted time for charts (e.g., "11:30 PM")
 */
export function formatChartTime(date) {
  if (!date) return '';

  const utcDate = typeof date === 'string' ? new Date(date) : new Date(date);

  const formatter = new Intl.DateTimeFormat('en-US', {
    timeZone: TIMEZONE,
    hour: 'numeric',
    minute: '2-digit',
    hour12: true
  });

  return formatter.format(utcDate);
}

/**
 * Get current timezone name
 * @returns {string} - Timezone abbreviation (ET)
 */
export function getTimezoneName() {
  return 'ET';
}

/**
 * Get location
 * @returns {string} - Location name
 */
export function getLocation() {
  return LOCATION;
}

/**
 * Check if currently in DST (Daylight Saving Time)
 * @returns {boolean}
 */
export function isDST() {
  const date = new Date();
  const jan = new Date(date.getFullYear(), 0, 1);
  const jul = new Date(date.getFullYear(), 6, 1);
  return Math.max(jan.getTimezoneOffset(), jul.getTimezoneOffset()) !== date.getTimezoneOffset();
}

/**
 * Get full timezone description
 * @returns {string} - Full timezone info
 */
export function getTimezoneInfo() {
  const dst = isDST();
  const tzAbbr = dst ? 'EDT' : 'EST';
  return `${tzAbbr} (Eastern ${dst ? 'Daylight' : 'Standard'} Time) - ${LOCATION}`;
}
