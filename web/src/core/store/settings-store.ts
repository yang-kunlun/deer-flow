// Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
// SPDX-License-Identifier: MIT

import { create } from "zustand";

import type { MCPServerMetadata, SimpleMCPServerMetadata } from "../mcp";

const SETTINGS_KEY = "deerflow.settings";

const DEFAULT_SETTINGS: SettingsState = {
  general: {
    autoAcceptedPlan: false,
    enableDeepThinking: false,
    enableBackgroundInvestigation: false,
    maxPlanIterations: 1,
    maxStepNum: 3,
    maxSearchResults: 3,
    reportStyle: "academic",
    selectedModel: "claude-3.5-sonnet",
  },
  mcp: {
    servers: [],
  },
};

export type SettingsState = {
  general: {
    autoAcceptedPlan: boolean;
    enableDeepThinking: boolean;
    enableBackgroundInvestigation: boolean;
    maxPlanIterations: number;
    maxStepNum: number;
    maxSearchResults: number;
    reportStyle: "academic" | "popular_science" | "news" | "social_media";
    selectedModel: string;
  };
  mcp: {
    servers: MCPServerMetadata[];
  };
};

function loadSettings(): SettingsState {
  if (typeof window === "undefined") {
    return DEFAULT_SETTINGS;
  }
  
  try {
    const stored = localStorage.getItem(SETTINGS_KEY);
    if (stored) {
      const parsed = JSON.parse(stored);
      return {
        ...DEFAULT_SETTINGS,
        ...parsed,
        general: {
          ...DEFAULT_SETTINGS.general,
          ...parsed.general,
        },
        mcp: {
          ...DEFAULT_SETTINGS.mcp,
          ...parsed.mcp,
        },
      };
    }
  } catch (error) {
    console.error("Failed to load settings:", error);
  }
  
  return DEFAULT_SETTINGS;
}

function saveSettings(settings: SettingsState) {
  if (typeof window === "undefined") {
    return;
  }
  
  try {
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
  } catch (error) {
    console.error("Failed to save settings:", error);
  }
}

export const useSettingsStore = create<
  SettingsState & {
    updateSettings: (updates: Partial<SettingsState>) => void;
    setSelectedModel: (model: string) => void;
    setEnableDeepThinking: (enabled: boolean) => void;
    setEnableBackgroundInvestigation: (enabled: boolean) => void;
    setAutoAcceptedPlan: (enabled: boolean) => void;
    setReportStyle: (style: SettingsState["general"]["reportStyle"]) => void;
    setMaxPlanIterations: (iterations: number) => void;
    setMaxStepNum: (steps: number) => void;
    setMaxSearchResults: (results: number) => void;
    addMCPServer: (server: MCPServerMetadata) => void;
    removeMCPServer: (serverName: string) => void;
    updateMCPServer: (serverName: string, updates: Partial<MCPServerMetadata>) => void;
  }
>((set, get) => ({
  ...loadSettings(),

  updateSettings: (updates) => {
    const newSettings = { ...get(), ...updates };
    set(newSettings);
    saveSettings(newSettings);
  },

  setSelectedModel: (model) => {
    const newSettings = {
      ...get(),
      general: { ...get().general, selectedModel: model },
    };
    set(newSettings);
    saveSettings(newSettings);
  },

  setEnableDeepThinking: (enabled) => {
    const newSettings = {
      ...get(),
      general: { ...get().general, enableDeepThinking: enabled },
    };
    set(newSettings);
    saveSettings(newSettings);
  },

  setEnableBackgroundInvestigation: (enabled) => {
    const newSettings = {
      ...get(),
      general: { ...get().general, enableBackgroundInvestigation: enabled },
    };
    set(newSettings);
    saveSettings(newSettings);
  },

  setAutoAcceptedPlan: (enabled) => {
    const newSettings = {
      ...get(),
      general: { ...get().general, autoAcceptedPlan: enabled },
    };
    set(newSettings);
    saveSettings(newSettings);
  },

  setReportStyle: (style) => {
    const newSettings = {
      ...get(),
      general: { ...get().general, reportStyle: style },
    };
    set(newSettings);
    saveSettings(newSettings);
  },

  setMaxPlanIterations: (iterations) => {
    const newSettings = {
      ...get(),
      general: { ...get().general, maxPlanIterations: iterations },
    };
    set(newSettings);
    saveSettings(newSettings);
  },

  setMaxStepNum: (steps) => {
    const newSettings = {
      ...get(),
      general: { ...get().general, maxStepNum: steps },
    };
    set(newSettings);
    saveSettings(newSettings);
  },

  setMaxSearchResults: (results) => {
    const newSettings = {
      ...get(),
      general: { ...get().general, maxSearchResults: results },
    };
    set(newSettings);
    saveSettings(newSettings);
  },

  addMCPServer: (server) => {
    const newSettings = {
      ...get(),
      mcp: {
        ...get().mcp,
        servers: [...get().mcp.servers, server],
      },
    };
    set(newSettings);
    saveSettings(newSettings);
  },

  removeMCPServer: (serverName) => {
    const newSettings = {
      ...get(),
      mcp: {
        ...get().mcp,
        servers: get().mcp.servers.filter((s) => s.name !== serverName),
      },
    };
    set(newSettings);
    saveSettings(newSettings);
  },

  updateMCPServer: (serverName, updates) => {
    const newSettings = {
      ...get(),
      mcp: {
        ...get().mcp,
        servers: get().mcp.servers.map((s) =>
          s.name === serverName ? { ...s, ...updates } : s
        ),
      },
    };
    set(newSettings);
    saveSettings(newSettings);
  },
}));

export function getChatStreamSettings() {
  const settings = useSettingsStore.getState();
  return {
    autoAcceptedPlan: settings.general.autoAcceptedPlan,
    enableDeepThinking: settings.general.enableDeepThinking,
    enableBackgroundInvestigation: settings.general.enableBackgroundInvestigation,
    maxPlanIterations: settings.general.maxPlanIterations,
    maxStepNum: settings.general.maxStepNum,
    maxSearchResults: settings.general.maxSearchResults,
    reportStyle: settings.general.reportStyle,
    selectedModel: settings.general.selectedModel,
    mcpSettings: {
      servers: settings.mcp.servers.reduce((acc, server) => {
        acc[server.name!] = {
          ...server,
          enabled_tools: server.enabled_tools || [],
          add_to_agents: server.add_to_agents || [],
        };
        return acc;
      }, {} as Record<string, any>),
    },
  };
}
