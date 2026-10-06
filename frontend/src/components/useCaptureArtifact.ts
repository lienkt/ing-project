import { useEffect, useState } from "react";
import { authEnabled, authHeaders } from "../auth";
import { captureArtifactUrl } from "../api/collection";

export function useCaptureArtifact(id: string | undefined, artifact: string) {
  const [result, setResult] = useState({ key: "", url: "", error: "" });
  const key = `${id}/${artifact}`;
  useEffect(() => {
    if (!id || !authEnabled) return;
    const controller = new AbortController();
    let url = "";
    async function load() {
      try {
        const response = await fetch(captureArtifactUrl(id!, artifact), {
          headers: await authHeaders(),
          signal: controller.signal,
        });
        if (!response.ok) throw new Error("Cannot load capture evidence.");
        const blob = await response.blob();
        if (controller.signal.aborted) return;
        url = URL.createObjectURL(blob);
        setResult({ key, url, error: "" });
      } catch (error) {
        if (!controller.signal.aborted)
          setResult({ key, url: "", error: (error as Error).message });
      }
    }
    void load();
    return () => {
      controller.abort();
      if (url) URL.revokeObjectURL(url);
    };
  }, [id, artifact, key]);
  if (!id) return { url: "", error: "" };
  if (!authEnabled) return { url: captureArtifactUrl(id, artifact), error: "" };
  return result.key === key ? result : { url: "", error: "" };
}
