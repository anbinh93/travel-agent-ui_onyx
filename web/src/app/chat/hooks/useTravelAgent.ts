/**
 * Travel Agent Hook
 * Manages Travel Agent state and API interactions
 */

import { useState, useEffect, useCallback } from "react";
import {
  checkTravelAgentStatus,
  sendTravelAgentMessage,
  streamTravelAgentMessage,
  TravelAgentMessage,
  TravelAgentStatus,
} from "@/lib/travel-agent/api";

export function useTravelAgent() {
  const [isEnabled, setIsEnabled] = useState(false);
  const [isConfigured, setIsConfigured] = useState(false);
  const [isChecking, setIsChecking] = useState(true);

  // Check Travel Agent status on mount
  useEffect(() => {
    checkStatus();
  }, []);

  const checkStatus = useCallback(async () => {
    try {
      setIsChecking(true);
      const status = await checkTravelAgentStatus();
      setIsConfigured(status.api_configured);
    } catch (error) {
      console.error("Failed to check Travel Agent status:", error);
      setIsConfigured(false);
    } finally {
      setIsChecking(false);
    }
  }, []);

  const toggleTravelAgent = useCallback(() => {
    if (isConfigured) {
      setIsEnabled((prev) => !prev);
    }
  }, [isConfigured]);

  const sendMessage = useCallback(
    async (
      messages: TravelAgentMessage[],
      options?: { temperature?: number; max_tokens?: number }
    ) => {
      if (!isEnabled || !isConfigured) {
        throw new Error("Travel Agent is not enabled or configured");
      }

      return sendTravelAgentMessage({
        messages,
        temperature: options?.temperature ?? 0.7,
        max_tokens: options?.max_tokens ?? 2000,
      });
    },
    [isEnabled, isConfigured]
  );

  const streamMessage = useCallback(
    async function* (
      messages: TravelAgentMessage[],
      options?: { temperature?: number; max_tokens?: number }
    ) {
      if (!isEnabled || !isConfigured) {
        throw new Error("Travel Agent is not enabled or configured");
      }

      yield* streamTravelAgentMessage({
        messages,
        temperature: options?.temperature ?? 0.7,
        max_tokens: options?.max_tokens ?? 2000,
        stream: true,
      });
    },
    [isEnabled, isConfigured]
  );

  return {
    isEnabled,
    isConfigured,
    isChecking,
    toggleTravelAgent,
    sendMessage,
    streamMessage,
  };
}
