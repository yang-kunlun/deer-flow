import { parse } from "best-effort-json-parser";

export function parseJSON<T>(json: string | null | undefined, fallback: T) {
  if (!json) {
    return fallback;
  }
  try {
    const raw = json
      .trim()
      .replace(/^```json\s*/, "")
      .replace(/^```js\s*/, "")
      .replace(/^```ts\s*/, "")
      .replace(/^```plaintext\s*/, "")
      .replace(/^```\s*/, "")
      .replace(/\s*```$/, "");
    
    // First try with native JSON.parse for better error handling
    try {
      return JSON.parse(raw) as T;
    } catch (nativeError) {
      // Fallback to best-effort parser with better error handling
      try {
        return parse(raw) as T;
      } catch (bestEffortError) {
        // Log the error for debugging but don't crash the UI
        console.warn("JSON parsing failed for input:", raw.substring(0, 200) + "...", {
          nativeError,
          bestEffortError
        });
        return fallback;
      }
    }
  } catch (error) {
    console.warn("JSON parsing failed:", error);
    return fallback;
  }
}
