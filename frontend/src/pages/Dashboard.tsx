import { useState } from "react";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  LabelList,
  ResponsiveContainer,
} from "recharts";
import Navbar from "../components/Navbar";

// 🎨 Colores base (azul corporativo + tonos secundarios sobrios)
const COLORS_BASE = [
  "#2563EB", // Azul primario
  "#F97316", // Naranja
  "#22C55E", // Verde
  "#EAB308", // Amarillo
  "#8B5CF6", // Morado
  "#0EA5E9", // Celeste
  "#14B8A6", // Turquesa
  "#F43F5E", // Coral
  "#6366F1", // Índigo
];

// 🔹 Asigna color único por categoría
const getColor = (name: string,index) => {
  const hash = [...name].reduce((acc, c) => acc + c.charCodeAt(0), 0);
  return COLORS_BASE[hash % COLORS_BASE.length];
};

export default function Dashboard() {
  const [data, setData] = useState<any[]>([]);
  const [movimientos, setMovimientos] = useState<any[]>([]);
  const [mensaje, setMensaje] = useState("");
  const [loading, setLoading] = useState(false);
  const [password, setPassword] = useState("");

  const [totalGastos, setTotalGastos] = useState(0);
  const [totalIngresos, setTotalIngresos] = useState(0);

  // 📤 Subir y procesar cartola PDF
  const handleUpload = async (file: File) => {
    setLoading(true);
    setMensaje("");

    const formData = new FormData();
    formData.append("file", file);
    formData.append("password", password || "");

    try {
      const uploadRes = await fetch(
        "https://finbot-p9be.onrender.com/movimientos/upload-pdf",
        {
          method: "POST",
          body: formData,
        }
      );

      if (!uploadRes.ok) throw new Error("Error al subir PDF");
      const result = await uploadRes.json();
      console.log("✅ Subida exitosa:", result);

      // 🔹 Obtener movimientos desde backend
      const response = await fetch("https://finbot-p9be.onrender.com");
      const movimientosData = await response.json();
      setMovimientos(movimientosData);

      // 🔹 Calcular totales
      const gastos = movimientosData.reduce(
        (acc: number, m: any) => acc + (m.cargos > 0 ? m.cargos : 0),
        0
      );
      const ingresos = movimientosData.reduce(
        (acc: number, m: any) => acc + (m.abonos > 0 ? m.abonos : 0),
        0
      );

      setTotalGastos(gastos);
      setTotalIngresos(ingresos);

      // 🔹 Agrupar por categoría
      const agrupado = movimientosData.reduce((acc: any, mov: any) => {
        const cat = mov.categoria || "Otros";
        acc[cat] = (acc[cat] || 0) + (mov.cargos > 0 ? mov.cargos : 0);
        return acc;
      }, {});

      const chartData = Object.entries(agrupado).map(([name, value]) => ({
        name,
        value,
      }));

      setData(chartData);
      setMensaje(`✅ Se procesaron ${movimientosData.length} movimientos.`);
    } catch (error) {
      console.error(error);
      setMensaje("❌ Error al subir o procesar el archivo.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      <main className="max-w-7xl mx-auto px-4 py-10">
        <h1 className="text-3xl font-bold text-gray-800 mb-8 text-center">
          FinBot – Panel Financiero
        </h1>

        {/* 🔹 TARJETAS DE ESTADÍSTICAS */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mb-10">
          <div className="bg-white shadow-md rounded-xl p-6 text-center">
            <h2 className="text-gray-600 text-lg font-medium">Total Gastos</h2>
            <p className="text-3xl font-semibold text-red-600 mt-2">
              -${totalGastos.toLocaleString()}
            </p>
          </div>
          <div className="bg-white shadow-md rounded-xl p-6 text-center">
            <h2 className="text-gray-600 text-lg font-medium">
              Total Ingresos
            </h2>
            <p className="text-3xl font-semibold text-green-600 mt-2">
              +${totalIngresos.toLocaleString()}
            </p>
          </div>
          <div className="bg-white shadow-md rounded-xl p-6 text-center">
            <h2 className="text-gray-600 text-lg font-medium">
              Movimientos Totales
            </h2>
            <p className="text-3xl font-semibold text-blue-600 mt-2">
              {movimientos.length}
            </p>
          </div>
        </div>

        {/* 📊 GRÁFICO Y SUBIDA */}
        <div className="grid md:grid-cols-2 gap-8">
          {/* 📈 GRÁFICO DE GASTOS */}
          <div className="bg-white shadow-md rounded-xl p-6">
            <h2 className="text-lg font-semibold text-gray-700 mb-4">
              Distribución de Gastos
            </h2>
            {data.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={data}
                    dataKey="value"
                    nameKey="name"
                    outerRadius={110}
                    labelLine={false}
                  >
                    {data.map((entry, index) => (
                      <Cell key={index} fill={getColor(entry.name, index)} />
                    ))}
                    <LabelList
                      dataKey="name"
                      position="outside"
                      className="text-xs fill-gray-700"
                    />
                  </Pie>
                  <Tooltip
                    formatter={(v: any) => `$${v.toLocaleString()}`}
                    contentStyle={{
                      backgroundColor: "#fff",
                      borderRadius: "8px",
                      border: "1px solid #e5e7eb",
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-gray-500 text-sm">
                Sube una cartola PDF para visualizar tus gastos.
              </p>
            )}
          </div>

          {/* 📤 SUBIR CARTOLA */}
          <div className="bg-white shadow-md rounded-xl p-6 flex flex-col justify-center">
            <h2 className="text-lg font-semibold text-gray-700 mb-3">
              Subir Cartola PDF
            </h2>
            <p>Ingresa tu contraseña antes de seleccionar una cartola</p>

            <label className="text-sm font-medium text-gray-700 mb-1">
              Selecciona tu archivo
            </label>
            <input
              type="file"
              accept="application/pdf"
              onChange={(e) =>
                e.target.files && handleUpload(e.target.files[0])
              }
              className="w-full text-sm border border-gray-300 rounded-lg cursor-pointer bg-gray-50 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 p-2"
            />

            <label className="block text-sm font-medium text-gray-700 mt-4 mb-1">
              Contraseña (si tu cartola está protegida)
            </label>
            <input
              type="password"
              placeholder="Opcional"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full text-sm border border-gray-300 rounded-lg p-2 focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />

            {loading && (
              <p className="text-blue-600 mt-3 animate-pulse">
                Procesando cartola...
              </p>
            )}
            {mensaje && <p className="text-gray-700 mt-3">{mensaje}</p>}
          </div>
        </div>

        {/* 🧾 TABLA MOVIMIENTOS */}
        <div className="mt-10 bg-white shadow-md rounded-xl p-6 overflow-x-auto">
          <h2 className="text-lg font-semibold text-gray-700 mb-4">
            Movimientos
          </h2>
          {movimientos.length > 0 ? (
            <table className="min-w-full text-sm border border-gray-200">
              <thead className="bg-gray-100">
                <tr>
                  <th className="px-4 py-2 text-left">Fecha</th>
                  <th className="px-4 py-2 text-left">Detalle</th>
                  <th className="px-4 py-2 text-right">Cargos</th>
                  <th className="px-4 py-2 text-right">Abonos</th>
                  <th className="px-4 py-2 text-left">Categoría</th>
                </tr>
              </thead>
              <tbody>
                {movimientos.map((m, i) => (
                  <tr
                    key={i}
                    className="border-t border-gray-100 hover:bg-gray-50"
                  >
                    <td className="px-4 py-2">{m.fecha}</td>
                    <td className="px-4 py-2">{m.detalle}</td>
                    <td className="px-4 py-2 text-right text-red-600">
                      {m.cargos > 0 ? `-$${m.cargos.toLocaleString()}` : ""}
                    </td>
                    <td className="px-4 py-2 text-right text-green-600">
                      {m.abonos > 0 ? `+$${m.abonos.toLocaleString()}` : ""}
                    </td>
                    <td className="px-4 py-2">{m.categoria}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="text-gray-500 text-sm">
              Aún no hay movimientos cargados.
            </p>
          )}
        </div>
      </main>
    </div>
  );
}
