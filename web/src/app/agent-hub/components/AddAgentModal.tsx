"use client";

import { useState } from "react";
import { ExternalAgentCreate } from "@/lib/agents/types";
import { createExternalAgent } from "@/lib/agents/api";
import { Button } from "@/components/ui/button";
import { X } from "lucide-react";

interface AddAgentModalProps {
  onClose: () => void;
  onSuccess: () => void;
}

export function AddAgentModal({ onClose, onSuccess }: AddAgentModalProps) {
  const [formData, setFormData] = useState<ExternalAgentCreate>({
    name: "",
    description: "",
    api_endpoint: "",
    api_key: "",
    auth_type: "bearer",
    default_model: "",
    default_temperature: 0.7,
    default_max_tokens: 2000,
    supports_streaming: false,
    system_prompt: "",
    icon_color: "#3b82f6",
    icon_emoji: "🤖",
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      await createExternalAgent(formData);
      onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create agent");
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
          <h2 className="text-2xl font-bold">Add External Agent</h2>
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
            <label className="block text-sm font-medium mb-2">
              Agent Name <span className="text-destructive">*</span>
            </label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 border border-border rounded-lg bg-background"
              placeholder="My Travel Assistant"
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
              placeholder="A helpful travel planning assistant"
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
                placeholder="🤖"
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
            <label className="block text-sm font-medium mb-2">
              API Endpoint <span className="text-destructive">*</span>
            </label>
            <input
              type="url"
              name="api_endpoint"
              value={formData.api_endpoint}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 border border-border rounded-lg bg-background"
              placeholder="https://api.example.com/v1/chat/completions"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">
                Authentication Type <span className="text-destructive">*</span>
              </label>
              <select
                name="auth_type"
                value={formData.auth_type}
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
                API Key {formData.auth_type !== "none" && <span className="text-destructive">*</span>}
              </label>
              <input
                type="password"
                name="api_key"
                value={formData.api_key || ""}
                onChange={handleChange}
                required={formData.auth_type !== "none"}
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
              placeholder="gpt-4"
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
                value={formData.default_temperature}
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
                value={formData.default_max_tokens}
                onChange={handleChange}
                min="1"
                className="w-full px-3 py-2 border border-border rounded-lg bg-background"
              />
            </div>
          </div>

          <div>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                name="supports_streaming"
                checked={formData.supports_streaming}
                onChange={handleChange}
                className="w-4 h-4"
              />
              <span className="text-sm font-medium">Supports Streaming</span>
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
              placeholder="You are a helpful travel assistant..."
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
              {submitting ? "Creating..." : "Create Agent"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
