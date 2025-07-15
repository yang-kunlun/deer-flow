// Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
// SPDX-License-Identifier: MIT

import { Bot, Check, ChevronDown } from "lucide-react";
import { useState } from "react";

import { Button } from "~/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "~/components/ui/dropdown-menu";
import { Badge } from "~/components/ui/badge";
import { useConfig } from "~/core/api/hooks";
import { cn } from "~/lib/utils";

interface ModelOption {
  id: string;
  name: string;
  provider: string;
  description: string;
}

const DEFAULT_MODELS: ModelOption[] = [
  {
    id: "claude-sonnet-4",
    name: "Claude Sonnet 4",
    provider: "OpenRouter",
    description: "Latest Claude model with enhanced reasoning",
  },
  {
    id: "gpt-4o",
    name: "GPT-4o",
    provider: "OpenRouter", 
    description: "Latest OpenAI model",
  },
];

interface ModelSelectorProps {
  selectedModel?: string;
  onModelChange?: (modelId: string) => void;
  className?: string;
}

export function ModelSelector({ 
  selectedModel = "claude-sonnet-4",
  onModelChange,
  className 
}: ModelSelectorProps) {
  const { config } = useConfig();
  const [isOpen, setIsOpen] = useState(false);

  // Combine default models with configured models
  const availableModels: ModelOption[] = [...DEFAULT_MODELS];
  if (config?.models) {
    Object.entries(config.models).forEach(([type, models]) => {
      if (type === "basic" && models.length > 0) {
        models.forEach((model: string) => {
          if (!availableModels.find(m => m.id === model)) {
            availableModels.push({
              id: model,
              name: model,
              provider: "Custom",
              description: `${type} model`,
            });
          }
        });
      }
    });
  }

  const currentModel = availableModels.find(m => m.id === selectedModel) || availableModels[0];

  const handleModelSelect = (modelId: string) => {
    onModelChange?.(modelId);
    setIsOpen(false);
  };

  return (
    <DropdownMenu open={isOpen} onOpenChange={setIsOpen}>
      <DropdownMenuTrigger asChild>
        <Button 
          variant="outline" 
          className={cn(
            "justify-between h-8 px-3 text-xs font-medium min-w-[160px]",
            className
          )}
        >
          <div className="flex items-center gap-2">
            <Bot className="h-3 w-3" />
            <span>{currentModel?.name || "Select Model"}</span>
          </div>
          <ChevronDown className="h-3 w-3 opacity-50" />
        </Button>
      </DropdownMenuTrigger>
      
      <DropdownMenuContent align="start" className="w-64">
        {availableModels.map((model) => (
          <DropdownMenuItem
            key={model.id}
            onClick={() => handleModelSelect(model.id)}
            className="flex items-start gap-3 p-3 cursor-pointer"
          >
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className="font-medium text-sm">{model.name}</span>
                {model.id === selectedModel && (
                  <Check className="h-3 w-3 text-primary" />
                )}
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="secondary" className="text-xs">
                  {model.provider}
                </Badge>
                <span className="text-xs text-muted-foreground">
                  {model.description}
                </span>
              </div>
            </div>
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
} 