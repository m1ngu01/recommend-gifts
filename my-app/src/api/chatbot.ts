import client from "./client";

export type ChatbotAction = {
  label: string;
  event: string;
  payload?: Record<string, any>;
};

export type ChatbotResponse = {
  session_id: string;
  state: string;
  flow?: string | null;
  message: string;
  slots?: Record<string, any>;
  profile?: Record<string, any>;
  actions: ChatbotAction[];
  data?: Record<string, any>;
};

type ChatbotEventPayload = {
  session_id?: string | null;
  event: string;
  payload?: Record<string, any>;
};

export async function triggerChatbotEvent(body: ChatbotEventPayload): Promise<ChatbotResponse> {
  const res = await client.post("/api/chatbot/events", body);
  const { ok, data, error } = res.data || {};
  if (!ok || !data) {
    const message = error?.message || "챗봇 요청이 실패했습니다.";
    throw new Error(message);
  }
  return data as ChatbotResponse;
}
