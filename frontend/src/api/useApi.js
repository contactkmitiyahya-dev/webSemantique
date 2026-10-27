// Hook commun (Ala) : charge des données depuis l'API et gère chargement / erreur.
//
// Exemple :
//   const { data, loading, error, reload } = useApi(
//     () => client.get('/formateurs', { params: { page } }).then((r) => r.data),
//     [page],
//   )
import { useCallback, useEffect, useState } from 'react'

export default function useApi(fn, deps = []) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [compteur, setCompteur] = useState(0) // incrémenté par reload() pour relancer l'appel

  useEffect(() => {
    let annule = false // évite de mettre à jour l'état si le composant a changé entre-temps
    setLoading(true)
    setError(null)
    Promise.resolve()
      .then(fn)
      .then((resultat) => { if (!annule) setData(resultat) })
      .catch((e) => { if (!annule) setError(e.message) })
      .finally(() => { if (!annule) setLoading(false) })
    return () => { annule = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, compteur])

  const reload = useCallback(() => setCompteur((c) => c + 1), [])

  return { data, loading, error, reload }
}
