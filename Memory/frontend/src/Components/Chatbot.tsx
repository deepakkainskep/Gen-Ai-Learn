import { useEffect, useRef, useState } from "react";

import ChatLoader from "./ChatLoader";

interface Message {
  role: "user" | "assistant";
  content: string;
}

const API_URL = import.meta.env.VITE_API_BASE_URL;

console.log("API_URL:", API_URL);

const Chatbot: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [userId, setUserId] = useState<string>("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setUserId("vishnu");
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const streamResponse = async (userMessage: string, assistantIndex?: number): Promise<void> => {
    setIsLoading(true);

    try {
      const response = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          user_input: userMessage,
          user_id: userId
        }),
      });

      if (!response.body) {
        throw new Error("Streaming not supported");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");

      let assistantText = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        assistantText += chunk;

        setMessages(prev => {
          const updated = [...prev];
          const index = assistantIndex !== undefined ? assistantIndex : updated.length - 1;

          updated[index] = {
            role: "assistant",
            content: assistantText,
          };
          return updated;
        });

        await new Promise<void>(resolve => requestAnimationFrame(() => resolve()));
      }
    } catch (error) {
      console.error("Error:", error);
      setMessages(prev => {
        const updated = [...prev];
        const index = assistantIndex !== undefined ? assistantIndex : updated.length - 1;

        if (updated[index]) {
          updated[index] = {
            ...updated[index],
            content: "Error generating response"
          };
        }
        return updated;
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (): Promise<void> => {
    if (!input.trim() || isLoading || !userId) return;

    const userMessage = input.trim();
    setInput("");

    setMessages(prev => [
      ...prev,
      { role: "user", content: userMessage },
      { role: "assistant", content: "" },
    ]);

    await streamResponse(userMessage);
  };

  const handleRegenerate = async (assistantIndex: number): Promise<void> => {
    if (isLoading) return;

    const userMessage = messages
      .slice(0, assistantIndex)
      .reverse()
      .find(m => m.role === "user")?.content;

    if (!userMessage) return;

    setMessages(prev => {
      const updated = [...prev];
      updated[assistantIndex] = { role: "assistant", content: "" };
      return updated;
    });

    await streamResponse(userMessage, assistantIndex);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>): void => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      <div className="border-b bg-white px-6 py-4 font-semibold flex justify-between items-center">
        <span>Chatbot With Memory</span>
        <span className="text-xs text-gray-500">User: {userId}</span>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-2xl mx-auto space-y-4">
          {messages.map((msg, i) => (
            <div key={i}>
              <div
                className={`flex ${
                  msg.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                <div
                  className={`px-4 py-2 rounded-xl max-w-xl whitespace-pre-wrap text-sm shadow-sm ${
                    msg.role === "user"
                      ? "bg-green-900 text-white"
                      : "bg-white border text-gray-800"
                  }`}
                >
                  {msg.role === "assistant" && msg.content === "" ? (
                    <ChatLoader />
                  ) : (
                    msg.content
                  )}
                </div>
              </div>

              {msg.role === "assistant" && msg.content && !isLoading && (
                <button
                  onClick={() => handleRegenerate(i)}
                  className="mt-1 ml-2 text-xs text-gray-400 hover:text-black cursor-pointer"
                >
                  🔄 Regenerate
                </button>
              )}
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
      </div>

      <div className="border-t bg-white px-4 py-4">
        <div className="max-w-2xl mx-auto flex gap-2">
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your message..."
            disabled={isLoading}
            className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-1 focus:ring-green-900"
          />
          <button
            onClick={handleSubmit}
            disabled={isLoading || !input.trim()}
            className="px-6 py-2 bg-green-900 text-white rounded-lg disabled:opacity-50 hover:bg-green-800 transition-colors"
          >
            {isLoading ? "..." : "Send"}
          </button>
        </div>
      </div>
    </div>
  );
};

export default Chatbot;