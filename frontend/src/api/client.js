import axios from "axios";

const client = axios.create({
  baseURL: "http://localhost:8000/api",
  headers: { "Content-Type": "application/json" },
});

// Convertir les erreurs en messages lisibles
client.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.detail ??
      error.message ??
      "Erreur inconnue";
    return Promise.reject(new Error(message));
  }
);

export default client;
