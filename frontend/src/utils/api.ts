const API_URL = "https://finbot-p9be.onrender.com"; // tu backend FastAPI

export async function apiPost(endpoint: string, data: Record<string, string>) {
  const res = await fetch(`${API_URL}${endpoint}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: new URLSearchParams(data),
  });
  const json = await res.json();
  if (!res.ok) throw new Error(json.detail || "Error en la solicitud");
  return json;
}

export function saveToken(token: string) {
  localStorage.setItem("token", token);
}

export function getToken() {
  return localStorage.getItem("token");
}

export function logout() {
  localStorage.removeItem("token");
}
