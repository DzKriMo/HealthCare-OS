/**
 * Exponential backoff retry for API calls.
 *
 * Used when optional services (SMS, email) are temporarily unavailable.
 * Never retries mutations — only safe GET/HEAD requests.
 */
interface RetryOptions {
  maxRetries?: number;
  baseDelayMs?: number;
  maxDelayMs?: number;
  onRetry?: (attempt: number, error: Error) => void;
}

const DEFAULT_OPTIONS: Required<RetryOptions> = {
  maxRetries: 3,
  baseDelayMs: 1000,
  maxDelayMs: 10000,
  onRetry: () => {},
};

export async function fetchWithRetry(
  url: string,
  options: RequestInit & { retry?: RetryOptions } = {},
): Promise<Response> {
  const { retry: retryOpts, ...fetchOptions } = options;
  const config = { ...DEFAULT_OPTIONS, ...retryOpts };

  // Never retry mutations
  const method = (fetchOptions.method || "GET").toUpperCase();
  if (method !== "GET" && method !== "HEAD") {
    return fetch(url, fetchOptions);
  }

  let lastError: Error | null = null;

  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    try {
      const response = await fetch(url, fetchOptions);

      // Only retry on server errors (5xx) or network errors
      if (response.status < 500) {
        return response;
      }

      if (attempt < config.maxRetries) {
        const delay = Math.min(
          config.baseDelayMs * Math.pow(2, attempt),
          config.maxDelayMs,
        );
        config.onRetry(attempt + 1, new Error(`HTTP ${response.status}`));
        await sleep(delay);
      } else {
        return response;
      }
    } catch (err) {
      lastError = err as Error;
      if (attempt < config.maxRetries) {
        const delay = Math.min(
          config.baseDelayMs * Math.pow(2, attempt),
          config.maxDelayMs,
        );
        config.onRetry(attempt + 1, lastError);
        await sleep(delay);
      }
    }
  }

  throw lastError || new Error("Max retries exceeded");
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
