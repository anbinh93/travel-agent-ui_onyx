/**
 * External Agent Types
 * TypeScript interfaces for n8n-wrapped agents
 */

export interface ExternalAgent {
  id: number;
  name: string;
  description?: string | null;
  api_endpoint: string;
  auth_type: "bearer" | "api_key" | "none";
  default_model: string;
  default_temperature: number;
  default_max_tokens: number;
  supports_streaming: boolean;
  system_prompt?: string | null;
  icon_color?: string | null;
  icon_emoji?: string | null;
  is_active: boolean;
  last_test_status?: "success" | "failed" | null;
  last_test_error?: string | null;
}

export interface ExternalAgentCreate {
  name: string;
  description?: string;
  api_endpoint: string;
  api_key?: string;
  auth_type?: "bearer" | "api_key" | "none";
  default_model?: string;
  default_temperature?: number;
  default_max_tokens?: number;
  supports_streaming?: boolean;
  system_prompt?: string;
  additional_params?: Record<string, any>;
  icon_color?: string;
  icon_emoji?: string;
}

export interface ExternalAgentUpdate {
  name?: string;
  description?: string;
  api_endpoint?: string;
  api_key?: string;
  auth_type?: "bearer" | "api_key" | "none";
  default_model?: string;
  default_temperature?: number;
  default_max_tokens?: number;
  supports_streaming?: boolean;
  system_prompt?: string;
  additional_params?: Record<string, any>;
  icon_color?: string;
  icon_emoji?: string;
  is_active?: boolean;
}

export interface TestConnectionResponse {
  success: boolean;
  message: string;
  response_preview?: string;
  error?: string;
}

/**
 * OpenAI-Compatible Request Format
 */
export interface OpenAIMessage {
  role: "system" | "user" | "assistant";
  content: string;
}

export interface OpenAIRequest {
  model: string;
  messages: OpenAIMessage[];
  temperature?: number;
  max_tokens?: number;
  top_p?: number;
  stream?: boolean;
  n?: number;
  stop?: string[];
  presence_penalty?: number;
  frequency_penalty?: number;
  logit_bias?: Record<string, number>;
  user?: string;
  response_format?: { type: string };
  tools?: any[];
  tool_choice?: string;
}

export interface OpenAIChoice {
  index: number;
  message: {
    role: string;
    content: string;
  };
  finish_reason: string;
}

export interface OpenAIResponse {
  id: string;
  object: string;
  created: number;
  model: string;
  choices: OpenAIChoice[];
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}
