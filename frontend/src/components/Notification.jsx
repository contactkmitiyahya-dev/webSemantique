// TEMPORAIRE (Ala) – à remplacer par la version de Linda
//
// Props : message (rien n'est affiché s'il est vide), type ('succes' | 'erreur'), onFermer, duree (ms)
import { useEffect } from 'react'
import './composants.css'

export default function Notification({ message, type = 'succes', onFermer, duree = 3500 }) {
  useEffect(() => {
    if (!message) return undefined
    const minuteur = setTimeout(onFermer, duree)
    return () => clearTimeout(minuteur)
    // onFermer volontairement absent : une fonction recréée à chaque rendu relancerait le minuteur
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [message, duree])

  if (!message) return null
  return (
    <div className={`notification ${type}`} role="status">
      <span>{message}</span>
      <button onClick={onFermer} aria-label="Fermer">×</button>
    </div>
  )
}
