/// <reference types="vite/client" />

declare global {
  interface Window {
    __HUB_SESSION__?: {
      hubUserId?: string;
      hubUserName?: string;
      role?: string;
      loginUrl?: string;
    };
  }
}

export {};
