import { useProviderStatus } from "./ProviderContext";

export function UnconfiguredLlmProviderText({
  showConfigureAPIKey,
  noSources,
}: {
  showConfigureAPIKey: () => void;
  noSources?: boolean;
}) {
  const { shouldShowConfigurationNeeded } = useProviderStatus();

  return (
    <>
      {noSources ? (
        <p className="text-base text-center w-full text-subtle">
          You have not yet added any sources. Please add{" "}
          <a
            href="/admin/add-connector"
            className="text-link hover:underline cursor-pointer"
          >
            a source
          </a>{" "}
          to continue.
        </p>
      ) : null}
      {/* Hide LLM provider warning - Travel Agent (Google Gemini) is configured as default */}
    </>
  );
}
