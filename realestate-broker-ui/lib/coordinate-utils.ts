/**
 * Coordinate conversion utilities for handling different coordinate systems
 * Used primarily for converting Israeli ITM coordinates (EPSG:2039) to WGS84 (EPSG:4326)
 */

// ITM coordinate system bounds (approximate)
// Israeli ITM coordinates typically range from:
// X: 100,000 to 300,000 (East-West)
// Y: 500,000 to 800,000 (North-South)
const ITM_BOUNDS = {
  minX: 100000,
  maxX: 300000,
  minY: 500000,
  maxY: 800000
}

// Extended bounds to catch more ITM-like coordinates
const EXTENDED_ITM_BOUNDS = {
  minX: 50000,
  maxX: 500000,
  minY: 400000,
  maxY: 1000000
}

// WGS84 coordinate system bounds
const WGS84_BOUNDS = {
  minLat: -90,
  maxLat: 90,
  minLon: -180,
  maxLon: 180
}

/**
 * Check if coordinates are in ITM format (Israeli Transverse Mercator)
 * ITM coordinates typically have X values around 100,000-300,000 and Y values around 500,000-800,000
 */
export function isITMCoordinates(lat: number, lon: number): boolean {
  // Check if coordinates are within standard ITM bounds
  const inStandardBounds = (
    lat >= ITM_BOUNDS.minY && lat <= ITM_BOUNDS.maxY &&
    lon >= ITM_BOUNDS.minX && lon <= ITM_BOUNDS.maxX
  )
  
  // Check if coordinates are within extended ITM bounds (for edge cases)
  const inExtendedBounds = (
    lat >= EXTENDED_ITM_BOUNDS.minY && lat <= EXTENDED_ITM_BOUNDS.maxY &&
    lon >= EXTENDED_ITM_BOUNDS.minX && lon <= EXTENDED_ITM_BOUNDS.maxX
  )
  
  // Check if coordinates look like projected coordinates (large numbers, not WGS84)
  // This catches coordinates that are clearly not WGS84 but might be in a projected system
  const looksLikeProjected = (
    Math.abs(lat) > 90 || Math.abs(lon) > 180
  ) && (
    lat > 0 && lon > 0 && // Both positive
    lat > 10000 && lon > 10000 // Both large numbers
  )
  
  // If coordinates look like projected coordinates, assume they might be ITM or similar
  // This is a fallback for coordinates that don't fit standard bounds but are clearly projected
  return inStandardBounds || inExtendedBounds || looksLikeProjected
}

/**
 * Check if coordinates are in WGS84 format
 */
export function isWGS84Coordinates(lat: number, lon: number): boolean {
  return (
    lat >= WGS84_BOUNDS.minLat && lat <= WGS84_BOUNDS.maxLat &&
    lon >= WGS84_BOUNDS.minLon && lon <= WGS84_BOUNDS.maxLon
  )
}

/**
 * Convert ITM coordinates to WGS84 using a simplified transformation
 * This is a fallback for coordinates that weren't converted in the backend
 */
export function convertITMToWGS84(x: number, y: number): { lat: number; lon: number } {
  // Simple linear transformation for ITM to WGS84
  // This is a rough approximation that should work for most Israeli locations
  
  // ITM false easting and northing
  const falseEasting = 200000
  const falseNorthing = 750000
  
  // Convert to relative coordinates
  const dx = x - falseEasting
  const dy = y - falseNorthing
  
  // Approximate conversion factors for Israel region
  // These are rough approximations that should place coordinates in Israel
  const latOffset = 31.734393 // Central latitude of Israel
  const lonOffset = 35.204516 // Central longitude of Israel
  
  // Convert using approximate scale factors
  const lat = latOffset + dy / 111320 // meters per degree latitude
  const lon = lonOffset + dx / (111320 * Math.cos(latOffset * Math.PI / 180)) // meters per degree longitude
  
  return {
    lat: Math.max(WGS84_BOUNDS.minLat, Math.min(WGS84_BOUNDS.maxLat, lat)),
    lon: Math.max(WGS84_BOUNDS.minLon, Math.min(WGS84_BOUNDS.maxLon, lon))
  }
}

/**
 * Convert coordinates to WGS84 format if they're in ITM format
 * Returns the original coordinates if they're already in WGS84 or invalid
 */
export function ensureWGS84Coordinates(lat: number, lon: number): { lat: number; lon: number } | null {
  // Check if coordinates are valid numbers
  if (isNaN(lat) || isNaN(lon)) {
    return null
  }
  
  // If already in WGS84 format, return as-is
  if (isWGS84Coordinates(lat, lon)) {
    return { lat, lon }
  }
  
  // Check if coordinates might be in ITM format but with swapped lat/lon
  // This handles cases where the backend returns coordinates in the wrong order
  // We check this first because both might be detected as ITM
  if (isITMCoordinates(lon, lat)) {
    const converted = convertITMToWGS84(lat, lon) // Swap the order for conversion
    // Verify the converted coordinates are in Israel region
    if (converted && converted.lat >= 29 && converted.lat <= 34 && converted.lon >= 34 && converted.lon <= 36) {
      return converted
    }
  }
  
  // If in ITM format, convert to WGS84
  if (isITMCoordinates(lat, lon)) {
    const converted = convertITMToWGS84(lon, lat) // Note: ITM uses X,Y order, WGS84 uses lat,lon
    // Verify the converted coordinates are in Israel region
    if (converted && converted.lat >= 29 && converted.lat <= 34 && converted.lon >= 34 && converted.lon <= 36) {
      return converted
    }
  }
  
  // If coordinates are outside both systems, return null (invalid)
  return null
}

/**
 * Validate and normalize coordinates for map display
 * Returns null if coordinates are invalid or cannot be converted
 * Note: This function expects non-null values - check for null/undefined before calling
 */
export function validateCoordinates(lat: number | null | undefined, lon: number | null | undefined): { lat: number; lon: number } | null {
  // Check for null/undefined values - these are considered "missing" not "invalid"
  if (lat == null || lon == null) {
    return null
  }
  
  // Convert to numbers
  const numLat = Number(lat)
  const numLon = Number(lon)
  
  // Check if conversion resulted in valid numbers
  if (isNaN(numLat) || isNaN(numLon)) {
    return null
  }
  
  // Try to ensure coordinates are in WGS84 format
  return ensureWGS84Coordinates(numLat, numLon)
}

/**
 * Check if coordinates are missing (null/undefined) vs invalid (bad values)
 * This helps distinguish between assets that haven't been geocoded vs those with bad data
 */
export function areCoordinatesMissing(lat: number | null | undefined, lon: number | null | undefined): boolean {
  return lat == null || lon == null
}

/**
 * Check if coordinates are present but invalid (bad values that can't be converted)
 */
export function areCoordinatesInvalid(lat: number | null | undefined, lon: number | null | undefined): boolean {
  if (areCoordinatesMissing(lat, lon)) {
    return false
  }
  
  const coords = validateCoordinates(lat, lon)
  return coords === null
}
