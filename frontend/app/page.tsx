"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

type ChatResponse = {
  response: string;
  detail?: string;
};

const API_URL = (
  process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000"
).replace(/\/$/, "");

const suggestions = [
  "What is the minimum deposit for a fixed deposit?",
  "Who can open a fixed deposit account?",
  "What is the maximum fixed deposit period?",
];

export default function Home() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [isSending, setIsSending] = useState(false);

  async function sendMessage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const question = input.trim() || (selectedImage ? "Read the screenshot and explain its key details." : "");
    if (!question || isSending) return;

    const imageToSend = selectedImage;
    setMessages((current) => [
      ...current,
      { role: "user", content: question },
    ]);
    setInput("");
    setSelectedImage(null);
    setIsSending(true);

    try {
      let response: Response;
      if (imageToSend) {
        const formData = new FormData();
        formData.append("session_id", "web-demo-session");
        formData.append("message", question);
        formData.append("image", imageToSend);
        response = await fetch(`${API_URL}/api/chat/image`, {
          method: "POST",
          body: formData,
        });
      } else {
        response = await fetch(`${API_URL}/api/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            session_id: "web-demo-session",
            message: question,
          }),
        });
      }

      const data = (await response.json()) as ChatResponse;
      if (!response.ok) {
        throw new Error(data.detail ?? "The assistant could not answer right now.");
      }

      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content: data.response,
        },
      ]);
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "Could not connect to the banking assistant API.";
      setMessages((current) => [
        ...current,
        { role: "assistant", content: `Connection error: ${message}` },
      ]);
    } finally {
      setIsSending(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-100 px-4 py-8 text-slate-900 sm:px-6">
      <section className="mx-auto flex min-h-[calc(100vh-4rem)] w-full max-w-4xl flex-col overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-xl shadow-slate-200/60">
        <header className="flex items-center gap-4 border-b border-slate-200 px-5 py-4 sm:px-8">
          <div className="flex size-12 items-center justify-center rounded-2xl bg-emerald-700 text-2xl text-white">
            ₹
          </div>
          <div className="min-w-0 flex-1">
            <h1 className="text-lg font-semibold tracking-tight sm:text-xl">
              AI Banking Assistant
            </h1>
            <p className="mt-0.5 text-sm text-slate-500">
              Ask questions about the available banking documents
            </p>
          </div>
          <span className="hidden items-center gap-2 rounded-full bg-emerald-50 px-3 py-1.5 text-xs font-medium text-emerald-800 sm:flex">
            <span className="size-2 rounded-full bg-emerald-500" />
            Document assistant
          </span>
          <Link
            href="/upload"
            className="rounded-xl border border-emerald-200 px-3 py-2 text-sm font-medium text-emerald-800 transition hover:bg-emerald-50"
          >
            Upload documents
          </Link>
        </header>

        <div
          className="flex flex-1 flex-col gap-5 overflow-y-auto bg-slate-50/70 p-4 sm:p-8"
          role="log"
          aria-live="polite"
          aria-label="Conversation"
        >
          {messages.length === 0 ? (
            <div className="m-auto w-full max-w-2xl py-10 text-center">
              <div className="mx-auto mb-5 flex size-16 items-center justify-center rounded-3xl bg-emerald-100 text-3xl text-emerald-800">
                ✦
              </div>
              <h2 className="text-2xl font-semibold tracking-tight">
                How can I help you today?
              </h2>
              <p className="mx-auto mt-2 max-w-lg text-sm leading-6 text-slate-500">
                Ask about banking rules and policies. Answers are generated from
                the available banking documents.
              </p>
              <div className="mt-7 flex flex-wrap justify-center gap-2">
                {suggestions.map((suggestion) => (
                  <button
                    key={suggestion}
                    type="button"
                    onClick={() => setInput(suggestion)}
                    className="rounded-full border border-slate-200 bg-white px-4 py-2 text-left text-sm text-slate-700 transition hover:border-emerald-300 hover:bg-emerald-50"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((message, index) => (
              <article
                key={`${message.role}-${index}`}
                className={`max-w-[90%] rounded-2xl px-4 py-3 shadow-sm sm:max-w-[80%] ${
                  message.role === "user"
                    ? "self-end rounded-br-md bg-emerald-700 text-white"
                    : "self-start rounded-bl-md border border-slate-200 bg-white text-slate-800"
                }`}
              >
                <p className="whitespace-pre-wrap text-sm leading-6">
                  {message.content}
                </p>
              </article>
            ))
          )}
          {isSending && (
            <p className="self-start rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-500">
              Searching documents and preparing an answer…
            </p>
          )}
        </div>

        <form
          onSubmit={sendMessage}
          className="border-t border-slate-200 bg-white p-4 sm:px-8 sm:py-5"
        >
          <label htmlFor="question" className="sr-only">
            Ask a banking question
          </label>
          <div className="flex items-end gap-3 rounded-2xl border border-slate-300 bg-white p-2 shadow-sm transition focus-within:border-emerald-600 focus-within:ring-4 focus-within:ring-emerald-100">
            <textarea
              id="question"
              rows={1}
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  event.currentTarget.form?.requestSubmit();
                }
              }}
              placeholder="Ask a question about banking documents…"
              className="max-h-32 min-h-11 flex-1 resize-y bg-transparent px-3 py-3 text-sm outline-none placeholder:text-slate-400"
            />
            <button
              type="submit"
              disabled={isSending || (!input.trim() && !selectedImage)}
              className="rounded-xl bg-emerald-700 px-5 py-3 text-sm font-semibold text-white transition hover:bg-emerald-800 disabled:cursor-not-allowed disabled:bg-slate-300"
            >
              {isSending ? "Sending…" : "Send"}
            </button>
          </div>
          <div className="mt-3 flex flex-wrap items-center gap-3">
            <label
              htmlFor="chat-image"
              className="cursor-pointer rounded-lg border border-slate-200 px-3 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50"
            >
              Attach screenshot
            </label>
            <input
              id="chat-image"
              type="file"
              accept=".png,.jpg,.jpeg,.webp,.bmp,.tif,.tiff"
              className="sr-only"
              onChange={(event) => setSelectedImage(event.currentTarget.files?.[0] ?? null)}
            />
            {selectedImage && (
              <span className="text-xs text-slate-500">
                {selectedImage.name} selected
                <button
                  type="button"
                  onClick={() => setSelectedImage(null)}
                  className="ml-2 font-semibold text-rose-700 hover:underline"
                >
                  Remove
                </button>
              </span>
            )}
          </div>
          <p className="mt-2 text-center text-xs text-slate-400">
            Answers are based on the indexed banking documents.
          </p>
        </form>
      </section>
    </main>
  );
}
