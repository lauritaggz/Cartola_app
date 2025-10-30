import { useEffect, useState } from "react";

interface Movimiento {
  id: number;
  fecha: string;
  detalle: string;
  cargos: number;
  abonos: number;
  categoria: string;
}

export default function MovimientosTable({ reload }: { reload: number }) {
  const [movimientos, setMovimientos] = useState<Movimiento[]>([]);
  const [filtro, setFiltro] = useState("");

  useEffect(() => {
    const fetchData = async () => {
      const url = filtro
        ? `http://127.0.0.1:8000/movimientos?categoria=${filtro}`
        : "http://127.0.0.1:8000/movimientos";
      const res = await fetch(url);
      const data = await res.json();
      setMovimientos(data);
    };
    fetchData();
  }, [reload, filtro]);

  return (
    <div className="bg-white p-6 rounded-xl shadow-md border mt-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold">Movimientos</h2>
        <select
          className="border rounded-lg px-3 py-1"
          value={filtro}
          onChange={(e) => setFiltro(e.target.value)}
        >
          <option value="">Todas las categorías</option>
          <option value="Supermercado">Supermercado</option>
          <option value="Restaurantes">Restaurantes</option>
          <option value="Transporte">Transporte</option>
          {/* ... puedes agregar más */}
        </select>
      </div>
      <table className="w-full border-collapse">
        <thead>
          <tr className="bg-blue-600 text-white text-left">
            <th className="p-2">Fecha</th>
            <th className="p-2">Detalle</th>
            <th className="p-2">Cargos</th>
            <th className="p-2">Abonos</th>
            <th className="p-2">Categoría</th>
          </tr>
        </thead>
        <tbody>
          {movimientos.map((m) => (
            <tr key={m.id} className="border-b hover:bg-blue-50">
              <td className="p-2">{m.fecha}</td>
              <td className="p-2">{m.detalle}</td>
              <td className="p-2 text-red-600">
                {m.cargos ? `- $${m.cargos.toLocaleString()}` : ""}
              </td>
              <td className="p-2 text-green-600">
                {m.abonos ? `+ $${m.abonos.toLocaleString()}` : ""}
              </td>
              <td className="p-2">{m.categoria}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
