"use client";

import React from "react";
import Text from "@/components/ui/text";
import { Modal } from "../../Modal";
import Cookies from "js-cookie";
import { useRouter } from "next/navigation";
import { COMPLETED_WELCOME_FLOW_COOKIE } from "./constants";
import { useEffect, useState } from "react";
import { ApiKeyForm } from "@/components/llm/ApiKeyForm";
import { WellKnownLLMProviderDescriptor } from "@/app/admin/configuration/llm/interfaces";
import { checkLlmProvider } from "./lib";
import { User } from "@/lib/types";
import { useProviderStatus } from "@/components/chat/ProviderContext";

import { usePopup } from "@/components/admin/connectors/Popup";

function setWelcomeFlowComplete() {
  Cookies.set(COMPLETED_WELCOME_FLOW_COOKIE, "true", { expires: 365 });
}

export function CompletedWelcomeFlowDummyComponent() {
  setWelcomeFlowComplete();
  return null;
}

export function WelcomeModal({ user }: { user: User | null }) {
  const router = useRouter();

  const [providerOptions, setProviderOptions] = useState<
    WellKnownLLMProviderDescriptor[]
  >([]);
  const { popup, setPopup } = usePopup();

  const { refreshProviderInfo } = useProviderStatus();
  const clientSetWelcomeFlowComplete = async () => {
    setWelcomeFlowComplete();
    refreshProviderInfo();
    router.refresh();
  };

  useEffect(() => {
    async function fetchProviderInfo() {
      const { options } = await checkLlmProvider(user);
      setProviderOptions(options);
    }

    fetchProviderInfo();
  }, [user]);

  // Auto-complete welcome flow so we never block on API key UI.
  useEffect(() => {
    setWelcomeFlowComplete();
    router.refresh();
  }, [router]);

  // Do not render the modal at all.
  return null;
}
