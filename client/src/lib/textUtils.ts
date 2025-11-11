/**
 * Utility functions for text manipulation
 */

/**
 * Truncates text to a specified length and adds ellipsis
 * @param text - The text to truncate
 * @param maxLength - Maximum length before truncation (default: 100)
 * @returns Truncated text with ellipsis if needed
 */
export function truncateText(text: string | undefined | null, maxLength: number = 100): string {
  if (!text) return '';
  
  // Remove markdown formatting and extra whitespace
  const cleanText = text
    .replace(/\*\*/g, '') // Remove bold
    .replace(/\*/g, '')   // Remove italic
    .replace(/#/g, '')    // Remove headers
    .replace(/\n+/g, ' ') // Replace newlines with spaces
    .replace(/\s+/g, ' ') // Normalize whitespace
    .trim();
  
  if (cleanText.length <= maxLength) {
    return cleanText;
  }
  
  // Truncate at word boundary
  const truncated = cleanText.substring(0, maxLength);
  const lastSpace = truncated.lastIndexOf(' ');
  
  return lastSpace > 0 
    ? truncated.substring(0, lastSpace) + '...'
    : truncated + '...';
}

/**
 * Extracts a brief summary from detailed persona text
 * Prioritizes the first sentence or paragraph
 */
export function extractPersonaSummary(text: string | undefined | null, maxLength: number = 150): string {
  if (!text) return '';
  
  // Try to extract first meaningful sentence before any markdown headers
  const lines = text.split('\n').filter(line => line.trim());
  
  for (const line of lines) {
    // Skip markdown headers
    if (line.trim().startsWith('#')) continue;
    
    // Skip empty lines or very short lines
    if (line.trim().length < 20) continue;
    
    // Found a good candidate - clean and truncate
    const cleaned = line
      .replace(/\*\*/g, '')
      .replace(/\*/g, '')
      .replace(/#/g, '')
      .trim();
    
    if (cleaned.length > 20) {
      return truncateText(cleaned, maxLength);
    }
  }
  
  // Fallback to regular truncation
  return truncateText(text, maxLength);
}

