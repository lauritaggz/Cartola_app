import { useState } from "react";
import { apiPost } from "../utils/api";
import { Link } from "react-router-dom";

export default function Register() {
  const [nombre, setNombre] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [mensaje, setMensaje] = useState("");

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await apiPost("/auth/register", { nombre, email, password });
      setMensaje("✅ Usuario registrado correctamente");
      console.log(res);
    } catch (err: any) {
      setMensaje(`❌ ${err.message}`);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-brand">
          <div className="brand-emoji">🧾</div>
          <h1 className="brand-title">Cartola App</h1>
          <p className="brand-sub">
            Comienza a controlar tus finanzas personales hoy mismo.
          </p>
        </div>

        <div className="auth-form">
          <div className="auth-form-inner">
            <h2 className="form-title text-center">Registro</h2>
            <p className="form-sub text-center">
              Crea una cuenta para empezar a gestionar tu dinero
            </p>

            <form onSubmit={handleRegister}>
              <div className="form-group">
                <label className="form-label">Nombre</label>
                <input
                  type="text"
                  placeholder="Tu nombre"
                  value={nombre}
                  onChange={(e) => setNombre(e.target.value)}
                  className="form-input"
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Correo</label>
                <input
                  type="email"
                  placeholder="ejemplo@correo.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="form-input"
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Contraseña</label>
                <input
                  type="password"
                  placeholder="Contraseña segura"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="form-input"
                  required
                />
              </div>

              <button type="submit" className="btn-primary">
                Crear cuenta
              </button>
            </form>

            {mensaje && (
              <p
                className={`message ${
                  mensaje.startsWith("✅") ? "success" : "error"
                }`}
              >
                {mensaje}
              </p>
            )}

            <p className="auth-foot">
              ¿Ya tienes cuenta?{" "}
              <Link to="/login" className="muted-link">
                Inicia sesión
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
