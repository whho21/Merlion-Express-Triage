// Error type shared by the real client and the mock server.
export class ApiError extends Error {
  constructor(message, { status = 0, code = 'NETWORK', retryable = true } = {}) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.retryable = retryable;
  }
}
