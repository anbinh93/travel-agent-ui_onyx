"use client";

import { useState, useEffect } from "react";
import { ExternalAgent } from "@/lib/agents/types";
import { fetchExternalAgents, deleteExternalAgent } from "@/lib/agents/api";
import {
  AgentList,
  AddAgentModal,
  EditAgentModal,
} from "./components";
import { usePopup } from "@/components/admin/connectors/Popup";
import { Button } from "@/components/ui/button";
import { PlusCircle } from "lucide-react";

export default function AgentHubPage() {
  const [agents, setAgents] = useState<ExternalAgent[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingAgent, setEditingAgent] = useState<ExternalAgent | null>(null);
  const { setPopup } = usePopup();

  const loadAgents = async () => {
    try {
      setLoading(true);
      const data = await fetchExternalAgents(false);
      setAgents(data);
    } catch (error) {
      setPopup({
        type: "error",
        message: error instanceof Error ? error.message : "Failed to load agents",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAgents();
  }, []);

  const handleAgentAdded = () => {
    setShowAddModal(false);
    loadAgents();
    setPopup({
      type: "success",
      message: "External agent has been successfully added",
    });
  };

  const handleAgentUpdated = () => {
    setEditingAgent(null);
    loadAgents();
    setPopup({
      type: "success",
      message: "External agent has been successfully updated",
    });
  };

  const handleDeleteAgent = async (agentId: number) => {
    if (!confirm("Are you sure you want to delete this agent?")) {
      return;
    }

    try {
      await deleteExternalAgent(agentId);
      loadAgents();
      setPopup({
        type: "success",
        message: "External agent has been successfully deleted",
      });
    } catch (error) {
      setPopup({
        type: "error",
        message: error instanceof Error ? error.message : "Failed to delete agent",
      });
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold">Agent Hub</h1>
          <p className="text-muted-foreground mt-2">
            Manage external AI agents with OpenAI-compatible APIs
          </p>
        </div>
        <Button
          onClick={() => setShowAddModal(true)}
          className="flex items-center gap-2"
        >
          <PlusCircle className="w-4 h-4" />
          Add Agent
        </Button>
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      ) : (
        <AgentList
          agents={agents}
          onEdit={setEditingAgent}
          onDelete={handleDeleteAgent}
          onTestConnection={loadAgents}
        />
      )}

      {showAddModal && (
        <AddAgentModal
          onClose={() => setShowAddModal(false)}
          onSuccess={handleAgentAdded}
        />
      )}

      {editingAgent && (
        <EditAgentModal
          agent={editingAgent}
          onClose={() => setEditingAgent(null)}
          onSuccess={handleAgentUpdated}
        />
      )}
    </div>
  );
}
