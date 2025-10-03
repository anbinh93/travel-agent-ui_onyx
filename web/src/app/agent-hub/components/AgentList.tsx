import { ExternalAgent } from "@/lib/agents/types";
import { AgentCard } from "./index";

interface AgentListProps {
  agents: ExternalAgent[];
  onEdit: (agent: ExternalAgent) => void;
  onDelete: (agentId: number) => void;
  onTestConnection: () => void;
}

export function AgentList({
  agents,
  onEdit,
  onDelete,
  onTestConnection,
}: AgentListProps) {
  if (agents.length === 0) {
    return (
      <div className="text-center py-12 bg-background-100 rounded-lg border-2 border-dashed border-border">
        <p className="text-lg text-muted-foreground">No agents configured yet</p>
        <p className="text-sm text-muted-foreground mt-2">
          Click "Add Agent" to create your first external agent
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {agents.map((agent) => (
        <AgentCard
          key={agent.id}
          agent={agent}
          onEdit={() => onEdit(agent)}
          onDelete={() => onDelete(agent.id)}
          onTestConnection={onTestConnection}
        />
      ))}
    </div>
  );
}
