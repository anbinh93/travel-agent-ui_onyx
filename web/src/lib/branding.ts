/**
 * Travel Agent Branding Configuration
 * Central place to manage all branding-related text and settings
 */

export const BRANDING = {
  // Application name
  APP_NAME: "Travel Agent",
  APP_NAME_SHORT: "Travel Agent",
  
  // Descriptions
  APP_DESCRIPTION: "Your AI-powered travel planning assistant",
  
  // Welcome messages - already configured in greetingMessages.ts
  
  // URLs (keep docs.onyx.app for internal reference, but don't show to end users)
  // These are admin-only URLs
  DOCS_URL: "https://docs.onyx.app",
  SUPPORT_SLACK: "https://join.slack.com/t/onyx-dot-app/shared_invite/zt-2twesxdr6-5iQitKZQpgq~hYIZ~dv3KA",
  
  // Feature names
  CHAT_FEATURE: "Chat",
  SEARCH_FEATURE: "Search",
  ASSISTANT_FEATURE: "Agent",
  
  // UI Text
  LOADING_TEXT: "Initializing Travel Agent",
  NO_AGENT_TEXT: "No agents configured yet",
  DEFAULT_AGENT_NAME: "Travel Agent",
  
  // Placeholders
  CHAT_PLACEHOLDER: "Where shall we go today?",
  
  // Error messages
  ERROR_PREFIX: "Travel Agent encountered an error",
  
} as const;

/**
 * Get application name from settings or use default
 */
export function getApplicationName(enterpriseSettings?: { application_name?: string }): string {
  return enterpriseSettings?.application_name || BRANDING.APP_NAME;
}
