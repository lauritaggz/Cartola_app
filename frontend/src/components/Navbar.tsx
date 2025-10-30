// src/components/Navbar.tsx
import { useState } from "react";
import { Menu, X } from "lucide-react";

export default function Navbar() {
  const [open, setOpen] = useState(false);

  return (
    <nav className="bg-[#0033A0] text-white shadow-md">
      <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
        {/* Logo */}
        <div className="flex items-center space-x-2">
          <img src="favicon.png" alt="FinBot Logo" className="h-8 w-8" />
          <span className="text-xl font-semibold tracking-tight">FinBot</span>
        </div>

        {/* Desktop menu */}
        <div className="hidden md:flex space-x-8 text-sm font-medium">
          <a href="/" className="hover:text-[#00AEEF]">
            Dashboard
          </a>
          <a href="/movimientos" className="hover:text-[#00AEEF]">
            Movimientos
          </a>
          <a href="/estadisticas" className="hover:text-[#00AEEF]">
            Estadísticas
          </a>
        </div>

        {/* Mobile button */}
        <button className="md:hidden" onClick={() => setOpen(!open)}>
          {open ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      {/* Mobile menu */}
      {open && (
        <div className="md:hidden bg-[#002A80] px-4 pb-3 space-y-2">
          <a href="/" className="block hover:text-[#00AEEF]">
            Dashboard
          </a>
          <a href="/movimientos" className="block hover:text-[#00AEEF]">
            Movimientos
          </a>
          <a href="/estadisticas" className="block hover:text-[#00AEEF]">
            Estadísticas
          </a>
        </div>
      )}
    </nav>
  );
}
