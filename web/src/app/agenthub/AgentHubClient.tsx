"use client";

import { useCallback, useMemo, useState, type KeyboardEvent } from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { FiExternalLink, FiRefreshCw } from "react-icons/fi";
import { cn } from "@/lib/utils";

export interface AgentMetadata {
  key: string;
  name: string;
  description: string;
}

interface AgentHubClientProps {
  agents: AgentMetadata[];
}

interface AgentRunResponse {
  answer: string;
  sources: { title?: string; url?: string }[];
}

export function AgentHubClient({ agents }: AgentHubClientProps) {
  const [selectedAgentKey, setSelectedAgentKey] = useState(
    agents[0]?.key ?? ""
  );
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AgentRunResponse | null>(null);
  const [lastRunAt, setLastRunAt] = useState<Date | null>(null);

  const selectedAgent = useMemo(
    () => agents.find((agent) => agent.key === selectedAgentKey) ?? null,
    [agents, selectedAgentKey]
  );

  const handleSubmit = useCallback(async () => {
    if (!selectedAgentKey) {
      setError("Please select an agent to run.");
      return;
    }

    const trimmedQuery = query.trim();
    if (!trimmedQuery) {
      setError("Ask a travel question to run the agent.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch("/api/agenthub/run", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          agent_key: selectedAgentKey,
          query: trimmedQuery,
        }),
      });

      if (!response.ok) {
        let message = "Unable to run agent";
        try {
          const data = await response.json();
          message = data?.detail || data?.message || message;
        } catch (_err) {
          message = await response.text();
        }
        throw new Error(message || "Unable to run agent");
      }

      const data = (await response.json()) as AgentRunResponse;
      setResult(data);
      setLastRunAt(new Date());
    } catch (err) {
      setResult(null);
      setLastRunAt(null);
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }, [query, selectedAgentKey]);

  const handleKeyDown = useCallback(
    (event: KeyboardEvent<HTMLTextAreaElement>) => {
      if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) {
        event.preventDefault();
        void handleSubmit();
      }
    },
    [handleSubmit]
  );

  const resultHasSources = Boolean(result?.sources?.length);

  return (
    <div className="mx-auto flex w-full max-w-4xl flex-col gap-6 pb-12">
      <Card>
        <CardHeader>
          <CardTitle>Agent Hub</CardTitle>
          <CardDescription>
            Pick a LangGraph-powered agent and run deep travel research without
            reconfiguring API keys. Agents read credentials from your Onyx
            <code className="mx-1 rounded bg-neutral-200 px-1 py-0.5 text-xs dark:bg-neutral-800">
              .env
            </code>
            so they are plug-and-play.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          {agents.length === 0 ? (
            <div className="rounded-md border border-dashed border-neutral-300 bg-neutral-50 p-6 text-sm text-neutral-600 dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-300">
              No agents are registered yet. Add a new agent module that calls
              <code className="mx-1 rounded bg-neutral-200 px-1 py-0.5 text-xs dark:bg-neutral-800">
                register_agent
              </code>
              and reload this page to use it.
            </div>
          ) : (
            <div className="flex flex-col gap-2">
              <label className="text-sm font-medium text-neutral-700 dark:text-neutral-200">
                Agent
              </label>
              <Select
                value={selectedAgentKey}
                onValueChange={(value: string) => setSelectedAgentKey(value)}
              >
                <SelectTrigger className="w-full md:w-80">
                  <SelectValue placeholder="Select an agent" />
                </SelectTrigger>
                <SelectContent>
                  {agents.map((agent) => (
                    <SelectItem key={agent.key} value={agent.key}>
                      {agent.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {selectedAgent && (
                <p className="text-sm text-neutral-600 dark:text-neutral-400">
                  {selectedAgent.description}
                </p>
              )}
            </div>
          )}

          <div className="flex flex-col gap-2">
            <label className="text-sm font-medium text-neutral-700 dark:text-neutral-200">
              Question
            </label>
            <Textarea
              placeholder="Where should I go for a 5-day culinary trip to Japan?"
              rows={4}
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              onKeyDown={handleKeyDown}
              className="resize-none"
            />
            <p className="text-xs text-neutral-500 dark:text-neutral-400">
              Press <kbd className="rounded border border-neutral-300 px-1">⌘</kbd>
              +<kbd className="rounded border border-neutral-300 px-1">Enter</kbd>
              to run, or click the button below. Results will appear in the
              response card.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Button
              onClick={handleSubmit}
              disabled={loading || !agents.length}
              className="w-full md:w-auto"
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <FiRefreshCw className="animate-spin" /> Running agent...
                </span>
              ) : (
                "Run agent"
              )}
            </Button>
            {lastRunAt && !loading && (
              <span className="text-xs text-neutral-500 dark:text-neutral-400">
                Last run at {lastRunAt.toLocaleTimeString()}
              </span>
            )}
          </div>

          {error && (
            <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/60 dark:text-red-300">
              {error}
            </div>
          )}
        </CardContent>
      </Card>

      <Card className={cn({ "opacity-60": loading })}>
        <CardHeader>
          <CardTitle>Answer</CardTitle>
          <CardDescription>
            {loading
              ? "Running agent..."
              : result
                ? "Results from the selected agent"
                : "Run an agent to see detailed travel guidance."}
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          {loading && (
            <div className="text-sm text-neutral-500 dark:text-neutral-400">
              Fetching deep search results...
            </div>
          )}

          {!loading && result && (
            <>
              <div className="whitespace-pre-wrap text-sm leading-relaxed text-neutral-900 dark:text-neutral-100">
                {result.answer || "No answer returned."}
              </div>

              {resultHasSources && (
                <div className="flex flex-col gap-2">
                  <Separator />
                  <p className="text-sm font-medium text-neutral-700 dark:text-neutral-200">
                    Sources
                  </p>
                  <ul className="flex list-disc flex-col gap-1 pl-5 text-sm text-neutral-600 dark:text-neutral-300">
                    {result.sources.map((source, index) => (
                      <li key={`${source.url ?? source.title ?? index}-${index}`}>
                        {source.url ? (
                          <a
                            href={source.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 text-blue-600 hover:underline dark:text-blue-400"
                          >
                            {source.title || source.url}
                            <FiExternalLink className="inline" size={14} />
                          </a>
                        ) : (
                          source.title || "Untitled source"
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          )}

          {!loading && !result && !error && (
            <div className="text-sm text-neutral-500 dark:text-neutral-400">
              You haven&apos;t run an agent yet. Select one above, enter a
              question, and click <strong>Run agent</strong> to get started.
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default AgentHubClient;
