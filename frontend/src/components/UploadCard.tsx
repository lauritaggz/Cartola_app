import { useState } from "react";

export default function UploadCard({
  onFileSelected,
}: {
  onFileSelected: (file: File) => void;
}) {
  const [file, setFile] = useState<File | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (selected) {
      setFile(selected);
      onFileSelected(selected);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center border-2 border-dashed border-blue-400 rounded-xl p-6 bg-white hover:bg-blue-50 transition text-center">
      <label className="cursor-pointer text-blue-600 font-semibold hover:underline">
        <input
          type="file"
          accept=".pdf"
          className="hidden"
          onChange={handleFileChange}
        />
        Seleccionar Cartola Bancaria
      </label>
      {file && (
        <p className="text-sm text-gray-600 mt-2">Archivo: {file.name}</p>
      )}
    </div>
  );
}
