import { useEffect, useState } from "react";

interface Movimiento {
  cargos: number;
  abonos: number;
}

export default function StatsCards({ reload }: { reload: number }) {
  const [totalGastos, setTotalGastos] = useState(0);
  const [totalIngresos, setTotalIngresos] = useState(0);
  const [cantidad, setCantidad] = useState(0);

  useEffect(() => {
    const fetchData = async () => {
      const res = await fetch("http://127.0.0.1:8000/movimientos");
      const data = await res.json();

      let gastos = 0;
      let ingresos = 0;
      data.forEach((m: Movimiento) => {
        gastos += m.cargos || 0;
        ingresos += m.abonos || 0;
      });

      setCantidad(data.length);
      setTotalGastos(gastos);
      setTotalIngresos(ingresos);
    };

    fetchData();
  }, [reload]);

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
      {/* GASTOS */}
      <div className="card border-l-4 border-red-500 bg-gradient-to-br from-white to-red-50">
        <h3 className="text-sm text-gray-500">Total Gastos</h3>
        <p className="text-3xl font-bold text-red-700 mt-1">
          -${totalGastos.toLocaleString()}
        </p>
        <p className="text-xs text-gray-400 mt-2">Movimientos salientes</p>
      </div>

      {/* INGRESOS */}
      <div className="card border-l-4 border-green-500 bg-gradient-to-br from-white to-green-50">
        <h3 className="text-sm text-gray-500">Total Ingresos</h3>
        <p className="text-3xl font-bold text-green-700 mt-1">
          +${totalIngresos.toLocaleString()}
        </p>
        <p className="text-xs text-gray-400 mt-2">Depósitos y abonos</p>
      </div>

      {/* MOVIMIENTOS TOTALES */}
      <div className="card border-l-4 border-primary bg-gradient-to-br from-white to-blue-50">
        <h3 className="text-sm text-gray-500">Movimientos Totales</h3>
        <p className="text-3xl font-bold text-primary mt-1">{cantidad}</p>
        <p className="text-xs text-gray-400 mt-2">Registros en la cartola</p>
      </div>
    </div>
  );
}
