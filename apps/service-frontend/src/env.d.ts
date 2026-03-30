/// <reference types="vite/client" />

declare global {
  interface ImportMetaEnv {
    readonly VITE_API_BASE_URL?: string;
    readonly VITE_API_PORT?: string;
    readonly VITE_REQUIRE_HUB_AUTH?: string;
    readonly VITE_DEV_HUB_USER_ID?: string;
    readonly VITE_DEV_HUB_USER_NAME?: string;
    readonly VITE_DEV_HUB_ROLE?: string;
    readonly VITE_HUB_LOGIN_URL?: string;
  }

  interface ImportMeta {
    readonly env: ImportMetaEnv;
  }

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
