// Client HTTP commun (Ala) : toutes les pages passent par lui pour parler au back-end.
// Le front ne parle JAMAIS directement à Fuseki : uniquement à l'API FastAPI (port 8000).
import axios from 'axios'

const client = axios.create({
  baseURL: 'http://localhost:8000/api',
  timeout: 10000, // 10 s
})

// Messages par défaut quand le back ne fournit pas de "detail"
const MESSAGES = {
  400: 'Requête invalide.',
  404: 'Élément introuvable.',
  409: 'Cet élément existe déjà.',
  422: 'Données du formulaire invalides.',
  500: 'Erreur interne du serveur.',
}

// Transforme le "detail" de FastAPI en texte (chaîne, ou liste d'erreurs Pydantic pour un 422)
function lireDetail(detail) {
  if (!detail) return null
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail.map((e) => `${(e.loc || []).slice(1).join('.')} : ${e.msg}`).join(' ; ')
  }
  return JSON.stringify(detail)
}

// Intercepteur : toute erreur devient une Error avec un message lisible en français
client.interceptors.response.use(
  (reponse) => reponse,
  (err) => {
    let message
    if (err.response) {
      // Le back a répondu avec un code d'erreur (400, 404, 409, 500...)
      const { status, data } = err.response
      message = lireDetail(data?.detail) || MESSAGES[status] || `Erreur ${status}.`
    } else if (err.code === 'ECONNABORTED') {
      message = 'Le serveur met trop de temps à répondre.'
    } else {
      // Pas de réponse du tout : back-end éteint ou mauvaise adresse
      message = 'Serveur injoignable : le back-end est-il lancé ?'
    }
    const erreur = new Error(message)
    erreur.status = err.response?.status // utile pour réagir à un 404 ou un 409
    erreur.response = err.response // pages de Yahya : err.response?.status, err.response.data.detail
    return Promise.reject(erreur)
  },
)

export default client
