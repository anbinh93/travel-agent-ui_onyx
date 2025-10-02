import AgentHubClient, { AgentMetadata } from "./AgentHubClient";
import { fetchSS } from "@/lib/utilsSS";
import { ErrorCallout } from "@/components/ErrorCallout";
import Title from "@/components/ui/title";
import Text from "@/components/ui/text";
import { Separator } from "@/components/ui/separator";

async function fetchAgents(): Promise<AgentMetadata[]> {
  const response = await fetchSS("/agenthub/agents");

  if (!response.ok) {
    throw new Error(`Failed to load agents (${response.status})`);
  }

  const data = (await response.json()) as AgentMetadata[];
  return data;
}

export default async function AgentHubPage() {
  let agents: AgentMetadata[] = [];
  let error: string | null = null;

  try {
    agents = await fetchAgents();
  } catch (err) {
    error = err instanceof Error ? err.message : "Unable to load agents";
  }

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-6 px-4 pb-12 pt-10 md:px-0">
      <div className="space-y-2">
        <Title size="lg">Agent Hub</Title>
        <Text className="text-neutral-600 dark:text-neutral-300">
          Run specialized LangGraph agents side-by-side. New agents register
          themselves via the backend registry and show up here automatically.
        </Text>
      </div>

      <Separator />

      {error ? (
        <ErrorCallout errorTitle="Failed to load agents" errorMsg={error} />
      ) : (
        <AgentHubClient agents={agents} />
      )}
    </div>
  );
}
