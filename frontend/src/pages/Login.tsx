import { useState } from "react";
import { apiPost, saveToken } from "../utils/api";
import { Link } from "react-router-dom";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [mensaje, setMensaje] = useState("");

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await apiPost("/auth/login", { email, password });
      saveToken(res.access_token);
      setMensaje("✅ Inicio de sesión exitoso");
      setTimeout(() => (window.location.href = "/dashboard"), 1000);
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
            Controla tus finanzas personales con claridad, precisión y estilo.
          </p>
        </div>

        <div className="auth-form">
          <div className="auth-form-inner">
            <h2 className="form-title text-center">Iniciar Sesión</h2>
            <p className="form-sub text-center">
              Accede a tu panel y administra tu dinero
            </p>

            <form onSubmit={handleLogin}>
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
                  placeholder="Tu contraseña"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="form-input"
                  required
                />
              </div>

              <button type="submit" className="btn-primary">
                Ingresar
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
              ¿No tienes cuenta?{" "}
              <Link to="/register" className="muted-link">
                Regístrate
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
