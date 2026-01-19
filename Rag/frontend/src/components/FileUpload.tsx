import { useState } from "react";

const UPLOAD_API = "http://127.0.0.1:8000/upload";

interface Props {
  onSuccess: () => void;
}

export default function FileUpload({ onSuccess }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);

  const uploadPdf = async () => {
    if (!file) return;

    setLoading(true);
    const formData = new FormData();
    formData.append("file", file);

    const res = await fetch(UPLOAD_API, {
      method: "POST",
      body: formData,
    });

    setLoading(false);

    if (res.ok) {
      onSuccess();
      alert(" PDF uploaded successfully");
    } else {
      alert("Upload failed");
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-5 mb-6">
      <h3 className="font-semibold mb-3">1️⃣ Upload PDF</h3>

      <input
        type="file"
        accept="application/pdf"
        onChange={(e) => setFile(e.target.files?.[0] || null)}
        className="block w-full text-sm mb-4
          file:mr-4 file:py-2 file:px-4
          file:rounded file:border-0
          file:text-sm file:font-semibold
          file:bg-blue-50 file:text-blue-700
          hover:file:bg-blue-100"
      />

      <button
        onClick={uploadPdf}
        disabled={loading}
        className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 disabled:opacity-50"
      >
        {loading ? "Uploading..." : "Upload PDF"}
      </button>
    </div>
  );
}

