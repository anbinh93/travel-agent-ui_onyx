import React from "react";

interface TravelAgentToggleProps {
  travelAgentEnabled: boolean;
  toggleTravelAgent: () => void;
}

export function TravelAgentToggle({
  travelAgentEnabled,
  toggleTravelAgent,
}: TravelAgentToggleProps) {
  return (
    <button
      className={`ml-2 py-1.5
        rounded-lg
        group
        inline-flex 
        items-center
        px-2
        transition-all
        duration-300
        ease-in-out
        ${
          travelAgentEnabled
            ? "bg-green-500/20 text-green-600 dark:bg-green-500/10 dark:text-green-400"
            : "text-input-text hover:text-neutral-900 hover:bg-background-chat-hover dark:hover:text-neutral-50"
        }
      `}
      onClick={toggleTravelAgent}
      role="switch"
      aria-checked={travelAgentEnabled}
      title={travelAgentEnabled ? "Travel Agent Active" : "Enable Travel Agent"}
    >
      {/* Airplane/Travel icon */}
      <svg
        width="16"
        height="16"
        viewBox="0 0 16 16"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          d="M14 5L8.5 8L3 5M8.5 1L14 5V11L8.5 15L3 11V5L8.5 1ZM6 6L8.5 4.5L11 6M8.5 10V7"
          stroke="currentColor"
          strokeOpacity="0.8"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      <span
        className={`text-sm font-medium overflow-hidden transition-all duration-300 ease-in-out ${
          travelAgentEnabled
            ? "max-w-[110px] opacity-100 ml-2"
            : "max-w-0 opacity-0 ml-0"
        }`}
        style={{
          display: "inline-block",
          whiteSpace: "nowrap",
        }}
      >
        Travel Agent
      </span>
    </button>
  );
}
