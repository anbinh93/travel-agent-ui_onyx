/**
 * Travel Agent API Client
 * Communicates with backend Travel Agent service
 */

export interface TravelAgentMessage {
  role: "user" | "assistant";
  content: string;
}

export interface TravelAgentChatRequest {
  messages: TravelAgentMessage[];
  temperature?: number;
  max_tokens?: number;
  stream?: boolean;
}

export interface TravelAgentChatResponse {
  message: string;
  status: string;
}

export interface TravelAgentStatus {
  enabled: boolean;
  api_configured: boolean;
  message: string;
}

const API_BASE = "/api/travel-agent";

/**
 * Check if Travel Agent is enabled and configured
 */
export async function checkTravelAgentStatus(): Promise<TravelAgentStatus> {
  const response = await fetch(`${API_BASE}/status`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error(`Failed to check Travel Agent status: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Send a chat message to Travel Agent (non-streaming)
 */
export async function sendTravelAgentMessage(
  request: TravelAgentChatRequest
): Promise<TravelAgentChatResponse> {
  const response = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(
      errorData.detail || `Travel Agent chat failed: ${response.statusText}`
    );
  }

  return response.json();
}

/**
 * Send a chat message to Travel Agent with streaming
 * Returns an async generator that yields text chunks
 */
export async function* streamTravelAgentMessage(
  request: TravelAgentChatRequest
): AsyncGenerator<string, void, unknown> {
  const response = await fetch(`${API_BASE}/chat/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify({ ...request, stream: true }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(
      errorData.detail || `Travel Agent stream failed: ${response.statusText}`
    );
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error("Response body is not readable");
  }

  const decoder = new TextDecoder();

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split("\n");

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const data = line.slice(6).trim();
          
          if (data === "[DONE]") {
            return;
          }
          
          if (data) {
            yield data;
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}
