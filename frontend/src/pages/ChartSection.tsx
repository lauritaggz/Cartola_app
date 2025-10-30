import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from "recharts";

const COLORS_BASE = [
  "#2563EB", // Azul primario
  "#F97316", // Naranja
  "#22C55E", // Verde
  "#EAB308", // Amarillo
  "#EC4899", // Rosa
  "#8B5CF6", // Morado
  "#0EA5E9", // Celeste
  "#14B8A6", // Turquesa
  "#F43F5E", // Coral
  "#6366F1", // Índigo
];

const getColor = (name: string) => {
  const hash = [...name].reduce((acc, c) => acc + c.charCodeAt(0), 0);
  return COLORS_BASE[hash % COLORS_BASE.length];
};

// Oculta etiquetas de porcentajes muy pequeñas
const renderCustomizedLabel = ({
  cx,
  cy,
  midAngle,
  innerRadius,
  outerRadius,
  percent,
}: any) => {
  if (percent < 0.05) return null;
  const RADIAN = Math.PI / 180;
  const radius = innerRadius + (outerRadius - innerRadius) * 0.7;
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);

  return (
    <text
      x={x}
      y={y}
      fill="white"
      textAnchor={x > cx ? "start" : "end"}
      dominantBaseline="central"
      fontSize={12}
    >
      {`${(percent * 100).toFixed(1)}%`}
    </text>
  );
};

export default function ChartSection({ data }: { data: any[] }) {
  if (!data || data.length === 0)
    return (
      <div className="p-4 text-gray-400 text-sm text-center">
        No hay datos de gastos aún.
      </div>
    );

  return (
    <div className="bg-white shadow-md rounded-xl p-5 w-full">
      <h2 className="text-lg font-semibold text-gray-800 mb-4">
        Distribución de Gastos
      </h2>
      <ResponsiveContainer width="100%" height={320}>
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            nameKey="name"
            cx="50%"
            cy="50%"
            outerRadius={110}
            labelLine={false}
            label={renderCustomizedLabel}
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={getColor(entry.name, index)} />
            ))}
          </Pie>
          <Tooltip
            formatter={(value: any) => `$${value.toLocaleString()}`}
            contentStyle={{
              backgroundColor: "#fff",
              borderRadius: "8px",
              border: "1px solid #e5e7eb",
            }}
          />
          <Legend
            layout="vertical"
            align="right"
            verticalAlign="middle"
            iconType="circle"
            wrapperStyle={{ fontSize: "12px", color: "#374151" }}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
