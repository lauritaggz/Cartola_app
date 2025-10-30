import Navbar from "../components/Navbar";

export default function Movimientos() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <main className="max-w-6xl mx-auto px-4 py-10">
        <h1 className="text-2xl font-semibold text-gray-800 mb-6">
          Movimientos Bancarios
        </h1>
        <p className="text-gray-600">
          Aquí podrás filtrar, buscar y revisar tus movimientos.
        </p>
      </main>
    </div>
  );
}
