import { useState } from "react";
import FileUpload from "./components/FileUpload";
import Chat from "./components/Chat";

export default function App() {
  const [uploaded, setUploaded] = useState(false);

  return (
    <div className="min-h-screen bg-gray-100 flex justify-center px-4">
      <div className="w-full max-w-2xl py-10">
        <h1 className="text-2xl font-bold text-center">
          📄 PDF Chat Assistant
        </h1>
        <p className="text-center text-gray-500 mb-6">
          Upload a PDF and ask questions using RAG
        </p>

        <FileUpload onSuccess={() => setUploaded(true)} />

        {uploaded && <Chat />}
      </div>
    </div>
  );
}
