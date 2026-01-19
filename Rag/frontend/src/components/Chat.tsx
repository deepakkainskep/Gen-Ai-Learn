import { useEffect, useRef, useState } from "react";

const ASK_API = "http://127.0.0.1:8000/chat";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const bottomRef = useRef<HTMLDivElement | null>(null);

  // Auto-scroll to latest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const askQuestion = async () => {
    if (!input.trim() || loading) return;

    const question = input;
    setInput("");
    setError("");

    setMessages((prev) => [
      ...prev,
      { role: "user", content: question },
    ]);

    setLoading(true);

    try {
      const res = await fetch(ASK_API, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });

      if (!res.ok) throw new Error("Server error");

      const data = await res.json();

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.answer || "Sorry, I couldn't find the answer.",
        },
      ]);
    } catch (err) {
      setError("Failed to get response from server");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-md p-5 flex flex-col">
      {/* Header */}
      <div className="flex justify-between items-center mb-3">
        <h3 className="font-semibold text-lg"> Ask Questions</h3>
        <button
          onClick={() => setMessages([])}
          className="text-sm text-red-500 hover:underline"
        >
          Clear chat
        </button>
      </div>

      {/* Chat Window */}
      <div className="flex-1 overflow-y-auto border rounded-lg p-4 space-y-3 mb-3 bg-gray-50">
        {messages.length === 0 && (
          <p className="text-sm text-gray-400 text-center">
            Ask a question from the uploaded PDF
          </p>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${
              msg.role === "user" ? "justify-end" : "justify-start"
            }`}
          >
            <div
              className={`max-w-[75%] px-4 py-2 rounded-lg text-sm leading-relaxed
                ${
                  msg.role === "user"
                    ? "bg-blue-600 text-white"
                    : "bg-white border"
                }`}
            >
              {msg.content}
            </div>
          </div>
        ))}

        {/* Loading bubble */}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-white border px-4 py-2 rounded-lg text-sm animate-pulse">
              Thinking...
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Error */}
      {error && (
        <p className="text-sm text-red-500 mb-2">{error}</p>
      )}

      {/* Input */}
      <div className="flex gap-2 items-end">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question from the PDF..."
          rows={2}
          className="flex-1 resize-none border rounded-lg px-3 py-2 text-sm
            focus:outline-none focus:ring-2 focus:ring-blue-500"
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              askQuestion();
            }
          }}
        />

        <button
          onClick={askQuestion}
          disabled={loading}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg
            hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Send
        </button>
      </div>
    </div>
  );
}
