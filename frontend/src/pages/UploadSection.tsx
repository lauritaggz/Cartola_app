import { useState } from "react";

export default function UploadSection({
  onUploadSuccess,
}: {
  onUploadSuccess: () => void;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFile(e.target.files?.[0] || null);
    setMessage("");
  };

  const handleUpload = async () => {
    if (!file) {
      setMessage("Selecciona un archivo PDF primero.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      setLoading(true);
      setMessage("");

      // 👉 URL del backend
      const res = await fetch("http://127.0.0.1:8000/movimientos/upload-pdf", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        throw new Error(`Error ${res.status}: ${res.statusText}`);
      }

      const data = await res.json();
      console.log("Respuesta del backend:", data);

      if (data.ok) {
        setMessage(`✅ ${data.insertados} movimientos cargados correctamente.`);
        onUploadSuccess(); // Notifica al dashboard que hay nuevos datos
      } else {
        setMessage("❌ No se pudieron procesar los movimientos.");
      }
    } catch (error) {
      console.error(error);
      setMessage("❌ Error de conexión con el servidor.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <h2 className="text-lg font-semibold text-primary mb-3">
        Subir cartola PDF - Ingresa tu contraseña PRIMERO
      </h2>

      <div className="flex flex-col md:flex-row items-center gap-3">
        <input
          type="file"
          accept="application/pdf"
          onChange={handleFileChange}
          className="border border-gray-300 rounded-md p-2 w-full md:w-auto"
        />
        <button
          onClick={handleUpload}
          disabled={loading}
          className={`px-4 py-2 rounded-md text-white font-semibold transition ${
            loading ? "bg-blue-300" : "bg-blue-600 hover:bg-blue-700"
          }`}
        >
          {loading ? "Subiendo..." : "Subir"}
        </button>
      </div>

      {message && (
        <p className="mt-3 text-sm font-medium text-gray-700 text-center">
          {message}
        </p>
      )}
    </div>
  );
}
