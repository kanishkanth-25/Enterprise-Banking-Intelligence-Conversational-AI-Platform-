"use client";

import Link from "next/link";
import { useState, type FormEvent } from "react";

type UploadResponse = {
  status: string;
  filename: string;
  pages_with_text: number;
  chunks_added: number;
  detail?: string;
};

const API_URL = (
  process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000"
).replace(/\/$/, "");

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<UploadResponse | null>(null);

  async function uploadDocument(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file || isUploading) return;
    const formElement = event.currentTarget;

    setError("");
    setResult(null);
    setIsUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const response = await fetch(`${API_URL}/api/documents/upload`, {
        method: "POST",
        body: formData,
      });
      const data = (await response.json()) as UploadResponse;
      if (!response.ok) {
        throw new Error(data.detail ?? "The document could not be indexed.");
      }
      setResult(data);
      setFile(null);
      formElement.reset();
    } catch (uploadError) {
      setError(
        uploadError instanceof Error
          ? uploadError.message
          : "Could not connect to the document service.",
      );
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-100 px-4 py-10 text-slate-900 sm:px-6">
      <section className="mx-auto w-full max-w-2xl overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-xl shadow-slate-200/60">
        <header className="border-b border-slate-200 px-6 py-5 sm:px-8">
          <Link href="/" className="text-sm font-medium text-emerald-800 hover:underline">
            ← Back to chat
          </Link>
          <h1 className="mt-4 text-2xl font-semibold tracking-tight">
            Add a banking document
          </h1>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            Upload a PDF or image. The backend extracts selectable PDF text and
            uses Tesseract OCR for scanned pages and images, then adds the text
            chunks to the searchable vector and keyword indexes.
          </p>
        </header>

        <form onSubmit={uploadDocument} className="space-y-5 p-6 sm:p-8">
          <label
            htmlFor="document-file"
            className="flex min-h-44 cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed border-slate-300 bg-slate-50 px-6 py-8 text-center transition hover:border-emerald-500 hover:bg-emerald-50/50"
          >
            <span className="flex size-12 items-center justify-center rounded-2xl bg-emerald-100 text-2xl text-emerald-800">
              ↑
            </span>
            <span className="mt-3 font-semibold">Choose a PDF or image</span>
            <span className="mt-1 text-sm text-slate-500">
              PDF, PNG, JPG, WEBP, BMP, or TIFF · up to 20 MB
            </span>
            {file && (
              <span className="mt-3 max-w-full truncate rounded-full bg-white px-3 py-1 text-sm text-slate-700 shadow-sm">
                {file.name}
              </span>
            )}
          </label>
          <input
            id="document-file"
            type="file"
            accept=".pdf,.png,.jpg,.jpeg,.webp,.bmp,.tif,.tiff"
            className="sr-only"
            onChange={(event) => setFile(event.currentTarget.files?.[0] ?? null)}
          />

          {error && (
            <p role="alert" className="rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-800">
              {error}
            </p>
          )}
          {result && (
            <div role="status" className="rounded-xl bg-emerald-50 px-4 py-3 text-sm text-emerald-900">
              <p className="font-semibold">Document indexed successfully.</p>
              <p className="mt-1">
                {result.filename}: {result.pages_with_text} pages with text and {result.chunks_added} chunks added.
              </p>
              <p className="mt-1 text-emerald-800">
                It can now be found in future chat searches.
              </p>
            </div>
          )}

          <button
            type="submit"
            disabled={!file || isUploading}
            className="w-full rounded-xl bg-emerald-700 px-5 py-3 font-semibold text-white transition hover:bg-emerald-800 disabled:cursor-not-allowed disabled:bg-slate-300"
          >
            {isUploading ? "Extracting and indexing…" : "Upload and index"}
          </button>
          <p className="text-center text-xs leading-5 text-slate-500">
            Files uploaded here are saved under the local data folder and become
            part of the shared knowledge index.
          </p>
        </form>
      </section>
    </main>
  );
}
