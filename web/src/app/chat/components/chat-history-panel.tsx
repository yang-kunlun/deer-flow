// Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
// SPDX-License-Identifier: MIT

import { History, MessageSquare, Plus, Trash2, X } from "lucide-react";
import { useEffect, useState } from "react";

import { Button } from "~/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "~/components/ui/card";
import { ScrollArea } from "~/components/ui/scroll-area";
import { useStore } from "~/core/store";
import type { ChatSession } from "~/core/api";
import { cn } from "~/lib/utils";

export function ChatHistoryPanel() {
  const {
    chatHistory,
    historyPanelOpen,
    currentSessionId,
    refreshChatHistory,
    switchToSession,
    deleteSession,
    createNewSession,
    setHistoryPanelOpen,
  } = useStore();

  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (historyPanelOpen) {
      setLoading(true);
      refreshChatHistory().finally(() => setLoading(false));
    }
  }, [historyPanelOpen, refreshChatHistory]);

  const handleSessionClick = async (sessionId: string) => {
    if (sessionId !== currentSessionId) {
      await switchToSession(sessionId);
    }
    setHistoryPanelOpen(false);
  };

  const handleDeleteSession = async (sessionId: string, event: React.MouseEvent) => {
    event.stopPropagation();
    if (window.confirm("Are you sure you want to delete this chat?")) {
      await deleteSession(sessionId);
    }
  };

  const handleNewChat = () => {
    createNewSession();
    setHistoryPanelOpen(false);
  };

  if (!historyPanelOpen) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50"
        onClick={() => setHistoryPanelOpen(false)}
      />
      
      {/* Panel */}
      <div className="relative w-80 bg-background border-r">
        <Card className="h-full rounded-none border-0">
          <CardHeader className="pb-4">
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <History className="h-5 w-5" />
                Chat History
              </CardTitle>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setHistoryPanelOpen(false)}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
            
            <Button
              onClick={handleNewChat}
              className="w-full justify-start gap-2"
              variant="outline"
            >
              <Plus className="h-4 w-4" />
              New Chat
            </Button>
          </CardHeader>
          
          <CardContent className="p-0 flex-1">
            <ScrollArea className="h-[calc(100vh-140px)]">
              {loading ? (
                <div className="p-4 text-center text-muted-foreground">
                  Loading...
                </div>
              ) : chatHistory.length === 0 ? (
                <div className="p-4 text-center text-muted-foreground">
                  No chat history yet
                </div>
              ) : (
                <div className="space-y-1 p-2">
                  {chatHistory.map((session) => (
                    <ChatHistoryItem
                      key={session.id}
                      session={session}
                      isActive={session.id === currentSessionId}
                      onClick={() => handleSessionClick(session.id)}
                      onDelete={(e) => handleDeleteSession(session.id, e)}
                    />
                  ))}
                </div>
              )}
            </ScrollArea>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

interface ChatHistoryItemProps {
  session: ChatSession;
  isActive: boolean;
  onClick: () => void;
  onDelete: (event: React.MouseEvent) => void;
}

function ChatHistoryItem({ session, isActive, onClick, onDelete }: ChatHistoryItemProps) {
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInMs = now.getTime() - date.getTime();
    const diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24));
    
    if (diffInDays === 0) {
      return "Today";
    } else if (diffInDays === 1) {
      return "Yesterday";
    } else if (diffInDays < 7) {
      return `${diffInDays} days ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  return (
    <div
      className={cn(
        "group flex items-center gap-3 rounded-lg p-3 cursor-pointer transition-colors",
        "hover:bg-accent hover:text-accent-foreground",
        isActive && "bg-accent text-accent-foreground"
      )}
      onClick={onClick}
    >
      <MessageSquare className="h-4 w-4 flex-shrink-0" />
      
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium truncate">
          {session.title}
        </div>
        <div className="text-xs text-muted-foreground">
          {formatDate(session.updated_at)} • {session.message_count} messages
        </div>
      </div>
      
      <Button
        variant="ghost"
        size="sm"
        className="opacity-0 group-hover:opacity-100 transition-opacity"
        onClick={onDelete}
      >
        <Trash2 className="h-3 w-3" />
      </Button>
    </div>
  );
} 