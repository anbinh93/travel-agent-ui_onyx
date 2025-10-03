"use client";

import { useState } from "react";
import { ExternalAgent } from "@/lib/agents/types";
import { testAgentConnection } from "@/lib/agents/api";
import { Button } from "@/components/ui/button";
import { Edit2, Trash2, TestTube, CheckCircle, XCircle } from "lucide-react";

interface AgentCardProps {
  agent: ExternalAgent;
  onEdit: () => void;
  onDelete: () => void;
  onTestConnection: () => void;
}

export function AgentCard({
  agent,
  onEdit,
  onDelete,
  onTestConnection,
}: AgentCardProps) {
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<string | null>(null);

  const handleTest = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const result = await testAgentConnection(agent.id);
      setTestResult(result.success ? "success" : "error");
      onTestConnection();
    } catch (error) {
      setTestResult("error");
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="bg-background border border-border rounded-lg p-6 hover:shadow-lg transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div
            className="w-12 h-12 rounded-full flex items-center justify-center text-2xl"
            style={{ backgroundColor: agent.icon_color || "#3b82f6" }}
          >
            {agent.icon_emoji || "🤖"}
          </div>
          <div>
            <h3 className="font-semibold text-lg">{agent.name}</h3>
            <p className="text-sm text-muted-foreground">
              {agent.default_model || "No model"}
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={onEdit}
            className="h-8 w-8 p-0"
          >
            <Edit2 className="w-4 h-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={onDelete}
            className="h-8 w-8 p-0 text-destructive hover:text-destructive"
          >
            <Trash2 className="w-4 h-4" />
          </Button>
        </div>
      </div>

      <p className="text-sm text-muted-foreground mb-4 line-clamp-2">
        {agent.description || "No description"}
      </p>

      <div className="space-y-2 mb-4 text-sm">
        <div className="flex justify-between">
          <span className="text-muted-foreground">Endpoint:</span>
          <span className="font-mono text-xs truncate max-w-[150px]">
            {agent.api_endpoint}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">Auth:</span>
          <span className="font-semibold capitalize">{agent.auth_type}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">Streaming:</span>
          <span>{agent.supports_streaming ? "Yes" : "No"}</span>
        </div>
      </div>

      <div className="flex items-center gap-2 pt-4 border-t border-border">
        <Button
          variant="outline"
          size="sm"
          onClick={handleTest}
          disabled={testing}
          className="flex-1 flex items-center gap-2"
        >
          <TestTube className="w-4 h-4" />
          {testing ? "Testing..." : "Test Connection"}
        </Button>
        {testResult === "success" && (
          <CheckCircle className="w-5 h-5 text-success" />
        )}
        {testResult === "error" && <XCircle className="w-5 h-5 text-destructive" />}
      </div>

      {agent.last_test_status && (
        <div className="mt-2 text-xs">
          <span className="text-muted-foreground">Last test: </span>
          <span
            className={
              agent.last_test_status === "success"
                ? "text-success"
                : "text-destructive"
            }
          >
            {agent.last_test_status}
          </span>
          {agent.last_test_error && (
            <p className="text-destructive mt-1 line-clamp-2">
              {agent.last_test_error}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
