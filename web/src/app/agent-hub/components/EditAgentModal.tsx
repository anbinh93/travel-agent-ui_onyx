"use client";

import { useState } from "react";
import { ExternalAgent, ExternalAgentUpdate } from "@/lib/agents/types";
import { updateExternalAgent } from "@/lib/agents/api";
import { Button } from "@/components/ui/button";
import { X } from "lucide-react";

interface EditAgentModalProps {
  agent: ExternalAgent;
  onClose: () => void;
  onSuccess: () => void;
}

export function EditAgentModal({
  agent,
  onClose,
  onSuccess,
}: EditAgentModalProps) {
  const [formData, setFormData] = useState<ExternalAgentUpdate>({
    name: agent.name,
    description: agent.description ?? undefined,
    api_endpoint: agent.api_endpoint,
    api_key: "", // Don't pre-fill for security
    auth_type: agent.auth_type,
    default_model: agent.default_model,
    default_temperature: agent.default_temperature,
    default_max_tokens: agent.default_max_tokens,
    supports_streaming: agent.supports_streaming,
    system_prompt: agent.system_prompt ?? undefined,
    icon_color: agent.icon_color ?? undefined,
    icon_emoji: agent.icon_emoji ?? undefined,
    is_active: agent.is_active,
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      // Only send fields that are not empty/null
      const updateData: ExternalAgentUpdate = {};
      Object.keys(formData).forEach((key) => {
        const value = formData[key as keyof ExternalAgentUpdate];
        if (value !== undefined && value !== null && value !== "") {
          updateData[key as keyof ExternalAgentUpdate] = value as any;
        }
      });

      await updateExternalAgent(agent.id, updateData);
      onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update agent");
    } finally {
      setSubmitting(false);
    }
  };

  const handleChange = (
    e: React.ChangeEvent<
      HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
    >
  ) => {
    const { name, value, type } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]:
        type === "checkbox"
          ? (e.target as HTMLInputElement).checked
          : type === "number"
            ? parseFloat(value)
            : value,
    }));
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-background rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-background border-b border-border px-6 py-4 flex justify-between items-center">
          <h2 className="text-2xl font-bold">Edit Agent</h2>
          <Button variant="ghost" size="sm" onClick={onClose} className="h-8 w-8 p-0">
            <X className="w-5 h-5" />
          </Button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="bg-destructive/10 text-destructive px-4 py-3 rounded-lg">
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium mb-2">Agent Name</label>
            <input
              type="text"
              name="name"
              value={formData.name || ""}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-border rounded-lg bg-background"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Description</label>
            <textarea
              name="description"
              value={formData.description || ""}
              onChange={handleChange}
              rows={3}
              className="w-full px-3 py-2 border border-border rounded-lg bg-background"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">Icon Emoji</label>
              <input
                type="text"
                name="icon_emoji"
                value={formData.icon_emoji || ""}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-border rounded-lg bg-background"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Icon Color</label>
              <input
                type="color"
                name="icon_color"
                value={formData.icon_color || "#3b82f6"}
                onChange={handleChange}
                className="w-full h-10 px-1 border border-border rounded-lg bg-background"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">API Endpoint</label>
            <input
              type="url"
              name="api_endpoint"
              value={formData.api_endpoint || ""}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-border rounded-lg bg-background"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">
                Authentication Type
              </label>
              <select
                name="auth_type"
                value={formData.auth_type || "bearer"}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-border rounded-lg bg-background"
              >
                <option value="bearer">Bearer Token</option>
                <option value="api_key">API Key</option>
                <option value="none">None</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">
                New API Key (leave empty to keep current)
              </label>
              <input
                type="password"
                name="api_key"
                value={formData.api_key || ""}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-border rounded-lg bg-background"
                placeholder="sk-..."
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Default Model</label>
            <input
              type="text"
              name="default_model"
              value={formData.default_model || ""}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-border rounded-lg bg-background"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">
                Temperature (0-2)
              </label>
              <input
                type="number"
                name="default_temperature"
                value={formData.default_temperature ?? 0.7}
                onChange={handleChange}
                min="0"
                max="2"
                step="0.1"
                className="w-full px-3 py-2 border border-border rounded-lg bg-background"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Max Tokens</label>
              <input
                type="number"
                name="default_max_tokens"
                value={formData.default_max_tokens ?? 2000}
                onChange={handleChange}
                min="1"
                className="w-full px-3 py-2 border border-border rounded-lg bg-background"
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                name="supports_streaming"
                checked={formData.supports_streaming ?? false}
                onChange={handleChange}
                className="w-4 h-4"
              />
              <span className="text-sm font-medium">Supports Streaming</span>
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                name="is_active"
                checked={formData.is_active ?? true}
                onChange={handleChange}
                className="w-4 h-4"
              />
              <span className="text-sm font-medium">Active</span>
            </label>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">System Prompt</label>
            <textarea
              name="system_prompt"
              value={formData.system_prompt || ""}
              onChange={handleChange}
              rows={4}
              className="w-full px-3 py-2 border border-border rounded-lg bg-background"
            />
          </div>

          <div className="flex gap-3 pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={submitting}
              className="flex-1"
            >
              Cancel
            </Button>
            <Button type="submit" disabled={submitting} className="flex-1">
              {submitting ? "Updating..." : "Update Agent"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
