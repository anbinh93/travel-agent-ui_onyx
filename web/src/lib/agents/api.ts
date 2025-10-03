/**
 * External Agent API Client
 * Handles CRUD operations for external agents
 */

import {
  ExternalAgent,
  ExternalAgentCreate,
  ExternalAgentUpdate,
  TestConnectionResponse,
} from "./types";

const API_BASE = "/api/agent-hub";

/**
 * Fetch all external agents
 */
export async function fetchExternalAgents(
  includeInactive: boolean = false
): Promise<ExternalAgent[]> {
  const url = `${API_BASE}/agents${includeInactive ? "?include_inactive=true" : ""}`;
  const response = await fetch(url, {
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch agents: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch a single agent by ID
 */
export async function fetchExternalAgent(
  agentId: number
): Promise<ExternalAgent> {
  const response = await fetch(`${API_BASE}/agents/${agentId}`, {
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch agent: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Create a new external agent
 */
export async function createExternalAgent(
  agentData: ExternalAgentCreate
): Promise<ExternalAgent> {
  const response = await fetch(`${API_BASE}/agents`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify(agentData),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `Failed to create agent: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Update an existing agent
 */
export async function updateExternalAgent(
  agentId: number,
  agentData: ExternalAgentUpdate
): Promise<ExternalAgent> {
  const response = await fetch(`${API_BASE}/agents/${agentId}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify(agentData),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `Failed to update agent: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Delete an agent (admin only)
 */
export async function deleteExternalAgent(agentId: number): Promise<void> {
  const response = await fetch(`${API_BASE}/agents/${agentId}`, {
    method: "DELETE",
    credentials: "include",
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `Failed to delete agent: ${response.statusText}`);
  }
}

/**
 * Test connection to an agent
 */
export async function testAgentConnection(
  agentId: number,
  testMessage: string = "Hello, test connection"
): Promise<TestConnectionResponse> {
  const response = await fetch(`${API_BASE}/agents/${agentId}/test`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify({ test_message: testMessage }),
  });

  if (!response.ok) {
    throw new Error(`Failed to test connection: ${response.statusText}`);
  }

  return response.json();
}
