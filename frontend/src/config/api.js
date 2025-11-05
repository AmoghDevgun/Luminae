// API Configuration
// In production, this will be set via environment variable REACT_APP_API_URL
// In development, it defaults to localhost or uses the proxy
const API_BASE_URL = process.env.REACT_APP_API_URL || '';

// Create axios instance with base URL
const getApiUrl = (endpoint) => {
  // Remove leading slash if present to avoid double slashes
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint;
  
  if (API_BASE_URL) {
    // Remove trailing slash from base URL if present
    const cleanBaseUrl = API_BASE_URL.endsWith('/') ? API_BASE_URL.slice(0, -1) : API_BASE_URL;
    return `${cleanBaseUrl}/${cleanEndpoint}`;
  }
  
  // In development, use relative path (will use proxy)
  return `/${cleanEndpoint}`;
};

export default getApiUrl;

